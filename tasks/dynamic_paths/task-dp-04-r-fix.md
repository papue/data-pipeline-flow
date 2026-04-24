# Task DP-04 — R dynamic paths: Fix

## Pre-condition
Task DP-03 complete: fixture project at `tests/fixtures/r_dynamic_paths/`,
findings in `tests/fixtures/r_dynamic_paths/FINDINGS.md`.

## Status
- [x] FINDINGS.md read; list of missing edges known
- [x] Fix(es) implemented in `r_extract.py`
- [x] Tool run against fixture project; all previously-missing edges now appear
- [x] No pre-existing edges disappeared (regression check)
- [x] Full test suite passes (`python -m pytest -q`) — 224 pass, 2 pre-existing failures unrelated to these changes

---

## Goal

Fix `src/data_pipeline_flow/parser/r_extract.py` so every edge listed as missing in
FINDINGS.md now appears in:

```
data-pipeline-flow extract-edges \
  --project-root tests/fixtures/r_dynamic_paths \
  --output /tmp/dp04_edges.csv
cat /tmp/dp04_edges.csv
```

---

## Fix guidance

Read `r_extract.py` in full before writing any code.

### Key areas to touch

**`sys.frame(1)$ofile` / `getSrcFilename()` / `rstudioapi::getActiveDocumentContext()$path`**
(R's equivalents of Python's `__file__`):
- These all evaluate to the path of the currently-running script.
- Seed `vars_map` with the current script's path before processing lines.
- Add a preprocessing regex (or line-by-line detector) that recognizes the idiom:
  `var <- dirname(sys.frame(1)$ofile)` or `var <- dirname(getSrcFilename(...))` and
  rewrites the RHS to the known resolved directory string.
- For `tryCatch(dirname(...), error = function(e) getwd())`, take only the first
  (non-error) expression.

**Bare variable name at call site** (`read.csv(var)`, `readRDS(var)`, `fread(var)`, etc.):
- The read/write patterns match quoted literals. When the argument is a bare identifier,
  look it up in `vars_map`.
- Two approaches: extend the regex to capture bare identifiers as a fallback group, or
  do a second-pass lookup after the literal match fails.

**Multi-line `file.path()` / `paste0()` calls**:
- The regexes use `[^)]+` which cannot span newlines.
- Add a line-joining preprocessor for open parentheses before the main loop.

### Iteration approach

One missing edge at a time:
1. Pick the first missing edge from FINDINGS.md.
2. Minimal change.
3. Re-run CLI, verify the edge appears.
4. Move to next.

After all missing edges resolved:
```
python -m pytest -q
```
Fix regressions if any.

---

## Fix agent instructions

1. Read `tests/fixtures/r_dynamic_paths/FINDINGS.md`.
2. Read `src/data_pipeline_flow/parser/r_extract.py` in full.
3. Fix iteratively, verifying with CLI after each change.
4. Run full test suite when done.
5. Report: lines changed, final edge list from fixture, final test count.
