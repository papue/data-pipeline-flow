# Task DP-02 — Python dynamic paths: Fix

## Pre-condition
Task DP-01 complete: fixture project exists at `tests/fixtures/python_dynamic_paths/`,
findings documented in `tests/fixtures/python_dynamic_paths/FINDINGS.md`.

## Status
- [x] FINDINGS.md read; list of missing edges known
- [x] Fix(es) implemented in `python_extract.py`
- [x] Tool run against fixture project; all previously-missing edges now appear
- [x] No pre-existing edges disappeared (regression check)
- [x] Full test suite passes (`python -m pytest -q`) — 224 pass, 2 pre-existing failures unrelated to this task

---

## Goal

Fix `src/data_pipeline_flow/parser/python_extract.py` so the tool correctly detects
all edges that were confirmed missing in DP-01. The measure of success is:

```
data-pipeline-flow extract-edges \
  --project-root tests/fixtures/python_dynamic_paths \
  --output /tmp/dp02_edges.csv
cat /tmp/dp02_edges.csv
```

Every edge listed in FINDINGS.md as "confirmed missing" must now appear in the output.

---

## Fix guidance

Read `HANDOVER_DYNAMIC_PATHS.md` for detailed fix suggestions per pattern.
Read `src/data_pipeline_flow/parser/python_extract.py` in full before writing any code.

### Key areas to touch

**`__file__` substitution** (affects patterns using `__file__`, `Path(__file__)`, etc.):
- The extractor is called with the path of the file being parsed.
- Seed the variable map with `__file__` before processing: this allows all downstream
  `os.path.dirname`, `os.path.abspath`, `Path(...).parent`, `Path(...).resolve()` calls
  to resolve correctly through existing logic.
- `Path(__file__).resolve().parent` and `Path(__file__).parent` are the pathlib equivalents
  — check whether pathlib resolution is handled and extend if needed.

**Bare variable name at call site** (affects `read_parquet(var)`, `read_csv(var)`, etc.):
- Currently the call-site matchers capture only quoted literals.
- When the argument is a bare identifier, look it up in the variable map.

**Raw string literals** (`r"C:\path\file"`):
- Variable assignment collection may only match `"..."` and `'...'`.
- Extend to also match `r"..."` / `r'...'` / `b"..."` prefixed strings.

**Multi-line `os.path.join` / `Path(...)` chains**:
- Check whether the parser uses AST (handles multi-line natively) or regex (needs
  line-joining preprocessing).

### Iteration approach

Work one pattern at a time:
1. Pick the first missing edge from FINDINGS.md.
2. Make the minimal change needed.
3. Re-run the tool against the fixture project.
4. Check that the edge now appears and nothing else broke.
5. Move to the next missing edge.

After all missing edges are resolved:
- Run the full test suite: `python -m pytest -q`
- Fix any regressions.

---

## Fix agent instructions

1. Read `tests/fixtures/python_dynamic_paths/FINDINGS.md`.
2. Read `src/data_pipeline_flow/parser/python_extract.py` in full.
3. Implement fixes iteratively, verifying with the CLI after each change.
4. When all missing edges are detected, run `python -m pytest -q`.
5. Report: what was changed (file + line numbers), final edge list from the fixture project,
   final test count.
