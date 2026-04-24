# Task DP-06 — Stata dynamic paths: Fix

## Pre-condition
Task DP-05 complete: fixture project at `tests/fixtures/stata_dynamic_paths/`,
findings in `tests/fixtures/stata_dynamic_paths/FINDINGS.md`.

## Status
- [x] FINDINGS.md read; list of missing edges known
- [x] Fix(es) implemented in `stata_extract.py`
- [x] Tool run against fixture project; all previously-missing edges now appear
- [x] No pre-existing edges disappeared (regression check)
- [x] Full test suite passes (`python -m pytest -q`) — 224 passing, 2 pre-existing failures unrelated to this task

---

## Goal

Fix `src/data_pipeline_flow/parser/stata_extract.py` so every edge listed as missing in
FINDINGS.md now appears in:

```
data-pipeline-flow extract-edges \
  --project-root tests/fixtures/stata_dynamic_paths \
  --output /tmp/dp06_edges.csv
cat /tmp/dp06_edges.csv
```

---

## Fix guidance

Read `stata_extract.py` in full before writing any code.

### Key areas to touch

**`c(pwd)` and `c(current_do_file)` system constants:**
- `c(pwd)` at parse time is best approximated by the project root (what `--project-root`
  was set to), since that's where Stata is typically launched from in research pipelines.
- `c(current_do_file)` is the path of the currently-parsed do-file.
- Add these as seeded entries in whatever constant/system-macro table exists before macro
  expansion runs. In Stata syntax these appear as `` `c(pwd)' `` and `` `c(current_do_file)' ``.
- `subinstr` is hard to evaluate statically — if the argument includes `c(current_do_file)`,
  emit a placeholder node rather than dropping the edge entirely.

**Absolute path strings in globals/locals (backslash paths):**
- Verify that `globals_map` / `local_map` population handles backslash paths
  (`"C:\research\data"`). The macro expansion step must substitute `$NAME\filename` and
  `$NAME/filename` both correctly.
- After expansion, if the resolved path starts with a drive letter (`C:\`) or is otherwise
  absolute, route it through the absolute-path diagnostic logic.

**`///` line continuation:**
- Add a preprocessing pass at the start of `extract_stata_edges` that joins `///`-terminated
  lines with their continuation:
  ```python
  def _join_stata_continuations(text: str) -> str:
      lines = text.splitlines()
      result, i = [], 0
      while i < len(lines):
          line = lines[i]
          while line.rstrip().endswith("///") and i + 1 < len(lines):
              line = line.rstrip()[:-3].rstrip() + " " + lines[i + 1].lstrip()
              i += 1
          result.append(line)
          i += 1
      return "\n".join(result)
  ```

**Nested macro expansion** (`$root\$sub\file.dta`):
- After a first-pass expansion, check whether any unexpanded `$NAME` or `` `name' `` tokens
  remain. If so, do a second-pass expansion. Two passes are sufficient for typical research
  code.

### Iteration approach

One missing edge at a time:
1. Pick the first missing edge from FINDINGS.md.
2. Minimal change.
3. Re-run CLI, verify the edge appears.
4. Move to next.

After all resolved:
```
python -m pytest -q
```
Fix regressions if any.

---

## Fix agent instructions

1. Read `tests/fixtures/stata_dynamic_paths/FINDINGS.md`.
2. Read `src/data_pipeline_flow/parser/stata_extract.py` in full.
3. Fix iteratively, verifying with CLI after each change.
4. Run full test suite when done.
5. Report: lines changed, final edge list from fixture, final test count.
