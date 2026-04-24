# Parser Handover: Undetected Dynamic Paths in Python Projects

## Context

This handover describes three patterns found in a real Python research project that the
parser currently fails to detect. All patterns are from `*.py` scripts in a project
scanned by `data-pipeline-flow`. The result is that the dependency graph shows all
analysis scripts as disconnected orphans, even though their data connections are
fully statically resolvable.

The goal is for the coding agent to add support for these patterns in
`src/data_pipeline_flow/parser/python_extract.py`, and ideally add regression fixtures
for each.

---

## Pattern 1 — `__file__`-relative path via `os.path.join` with `..` traversal

### Frequency
Most common pattern. Used in at least 3 scripts: `generate_graphs.py`,
`generate_graphs_k0.py`, `random_action_check.py`.

### Exact code
```python
try:
    _script_dir = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _script_dir = os.path.join(os.getcwd(), '01 data work', 'analysis')

data_path = os.path.join(_script_dir, '..', 'results') + os.sep
df_results = pd.read_parquet(f"{data_path}all_results.parquet")
df_results_2t = pd.read_parquet(f"{data_path}all_results_multiT.parquet")
```

### What the parser should resolve

The parser already knows which file it is currently parsing. So at parse time:

- `__file__` = the absolute path of the script being parsed, e.g.
  `<project_root>/analysis/generate_graphs.py`
- `os.path.dirname(os.path.abspath(__file__))` = `<project_root>/analysis`
- `os.path.join(_script_dir, '..', 'results')` = `<project_root>/results`
- `f"{data_path}all_results.parquet"` = `<project_root>/results/all_results.parquet`
- Project-relative: `results/all_results.parquet`

The `try/except NameError` block is an interactive-mode fallback. For static
analysis, only the `try` branch matters — the `except` branch only runs in
IPython/PyCharm consoles and should be ignored or skipped.

### Expected parser output
```
read: results/all_results.parquet
read: results/all_results_multiT.parquet
```

### Why it is currently missed
The parser does not substitute `__file__` with the currently-parsed script's own
path. Without that substitution, `_script_dir` is an unresolved variable, so the
`os.path.join` call produces nothing, and the f-string `f"{data_path}..."` also
produces nothing.

### Suggested fix
In `python_extract.py`, when evaluating `os.path.dirname(os.path.abspath(__file__))`:
1. Recognize `__file__` as a special name; substitute it with the path of the file
   currently being parsed.
2. Apply `os.path.abspath` (which is a no-op if the path is already absolute).
3. Apply `os.path.dirname` to get the containing directory.
4. Store the result in the local variable binding (`_script_dir`).
5. Continue resolving `os.path.join(_script_dir, '..', 'results')` using the
   existing `..` normalization logic.
6. Dereference the variable when it appears in an f-string.

---

## Pattern 2 — Hardcoded absolute path in a variable, passed to read/write call

### Frequency
Used in `generate_output.py` (read) and `extract_data.py` (both read and write).

### Exact code — read side (`generate_output.py`)
```python
results_path = r"D:\Sciebo New\electricity_qlearning\AlgorithmicElectricityAuctions\results\all_results.parquet"
df_results = pd.read_parquet(results_path)
```

### Exact code — write side (`extract_data.py`)
```python
path_base = r"D:\Sciebo New\electricity_qlearning\AlgorithmicElectricityAuctions\results"
save_path = os.path.join(path_base, "all_results.parquet")
df_results.to_parquet(save_path, index=False)
```

Also in `generate_output_multiple_periods.py`:
```python
results_path = r"D:\Sciebo New\electricity_qlearning\AlgorithmicElectricityAuctions\results\all_results_multiT.parquet"
df_results = pd.read_parquet(results_path)
```

### What the parser should resolve

- The string literal assigned to `results_path` / `path_base` is an absolute path.
- `os.path.join(path_base, "all_results.parquet")` appends a literal filename to an
  absolute base — the result is still absolute.
- The parser should track that these variables hold path strings and dereference them
  at the call site (`read_parquet(results_path)`, `to_parquet(save_path)`).
- Since the resolved path is absolute, it should be relativized against the
  project root if it falls within it, or flagged as `absolute_path` if it does not.
- In this project, `results/` sits outside the `project_root` (`01 data work/`),
  so the correct outcome is an `absolute_path` diagnostic — but the node should
  still be extracted so the edge appears in the graph (as it does for manual
  placeholder nodes today).

### Expected parser output
```
read:  <absolute> results/all_results.parquet          → absolute_path diagnostic
write: <absolute> results/all_results.parquet          → absolute_path diagnostic
```

### Why it is currently missed
The parser detects literal strings passed directly to `read_parquet("literal")` but
does not track variable assignments. When the path is stored in `results_path` first
and then passed as a variable name, the call-site argument is not a string literal
and the parser produces nothing.

### Suggested fix
Add a simple single-file variable tracker in `python_extract.py`:
1. When a string literal (or `os.path.join` of string literals) is assigned to a
   variable at module scope or function scope, record it: `{var_name: resolved_path}`.
2. When a read/write call is encountered and its argument is a bare name (not a
   literal), look it up in the variable map.
3. If found, treat the resolved value as the path argument and proceed as normal
   (relativize or emit `absolute_path`).

This does not need to handle reassignment, conditionals, or loops — a simple
last-write-wins map over the top-level AST is sufficient for the patterns seen here.

---

## Pattern 3 — Multi-line `os.path.join` with `__file__`

### Frequency
Used in `profit_heatmap.py`.

### Exact code
```python
RESULTS_BASE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "results", "demand_benchmark"
)
PLOTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plots")

param_file = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "parameters", "parameter_demand_benchmark_df2.json"
)
with open(param_file) as f:
    ...

folder = os.path.join(RESULTS_BASE, df_name)      # df_name is a loop variable
with open(os.path.join(folder, fname), "rb") as fh:
    result.append(pickle.load(fh))
```

### What the parser should resolve

- `RESULTS_BASE` resolves via Pattern 1 logic to `results/demand_benchmark/`
  (project-relative, or absolute if outside project root).
- `param_file` resolves to `parameters/parameter_demand_benchmark_df2.json` —
  a readable, project-relative path.
- `folder = os.path.join(RESULTS_BASE, df_name)` — `df_name` is a loop variable
  and cannot be resolved; this edge should be skipped or noted as dynamic.
- `pickle.load(open(...))` is a read pattern not currently covered (only
  `pd.read_parquet`, `pd.read_csv` etc. are likely covered).

### Why it is currently missed

Two sub-issues:
1. Same `__file__` resolution gap as Pattern 1.
2. The `os.path.join(...)` call is split across multiple lines. If the parser
   uses regex rather than AST, it may only match single-line `os.path.join(...)`.

### Suggested fix
1. Apply the `__file__` substitution from Pattern 1.
2. Ensure `os.path.join` resolution operates on the AST call node, not a
   single-line regex match — multi-line calls are identical in the AST.
3. Add `pickle.load(open(..., "rb"))` and `open(...).read()` as recognized
   read patterns in the extractor.

---

## Summary Table

| Pattern | Scripts affected | Read or write | Resolvable? | Fix needed |
|---------|-----------------|---------------|-------------|------------|
| `__file__` → `dirname` → `join(..)` → f-string | `generate_graphs.py`, `generate_graphs_k0.py`, `random_action_check.py` | read | Yes — fully | Substitute `__file__` with current script path; resolve `..` |
| Absolute string literal → variable → `read_parquet(var)` | `generate_output.py`, `generate_output_multiple_periods.py` | read | Yes — emit `absolute_path` | Track module-scope variable assignments |
| Absolute string literal → variable → `os.path.join` → `to_parquet(var)` | `extract_data.py` | write | Yes — emit `absolute_path` | Track module-scope variable assignments |
| Multi-line `os.path.join(__file__, ...)` | `profit_heatmap.py` | read | Yes — fully | Same as first row + multi-line AST support |
| `pickle.load(open(var, "rb"))` | `profit_heatmap.py` | read | Partially (path itself is dynamic) | Add `pickle.load` / `open` as recognized read patterns |

---

## Suggested Regression Fixtures

For each pattern, a minimal fixture in `tests/fixtures/` would suffice:

```
tests/fixtures/file_relative_paths/
    reader.py        # uses __file__ + os.path.join + .. + f-string
    results/
        data.parquet (empty)

tests/fixtures/variable_absolute_path/
    writer.py        # assigns absolute string to var, calls to_parquet(var)
    reader.py        # assigns absolute string to var, calls read_parquet(var)

tests/fixtures/multiline_join/
    script.py        # os.path.join(...) split across lines with __file__
```

Each fixture should have a corresponding test asserting the expected edges are
extracted (or the expected diagnostic is raised for absolute paths).
