# R dynamic path replication findings

Generated: 2026-04-24
Fixed: 2026-04-24

## Fixed

All 8 missing edges and 2 suppressed edges are now detected. Summary of fixes applied:

| Root cause | Fix | Files changed |
|-----------|-----|---------------|
| Cat-1: `sys.frame(1)$ofile`, `getSrcFilename()`, `rstudioapi::getActiveDocumentContext()$path` not recognized | Added `_SCRIPT_DIR_RE` / `_GETSRCFILENAME_RE` patterns; seeded `vars_map` with `__script_dir__` = script's parent dir; multi-iteration pre-pass resolves chained vars | `parser/r_extract.py` |
| Cat-1: `paste0()`/`sprintf()`/`file.path()` RHS assignments not stored in `vars_map` | Pre-pass now detects `var <- paste0(...)`, `var <- sprintf(...)`, `var <- file.path(...)` and stores resolved values | `parser/r_extract.py` |
| Cat-2: Multi-line `file.path()` calls not matched | Added `_join_continued_lines()` preprocessor that joins open-paren lines before the main loop | `parser/r_extract.py` |
| Cat-3: `.rds` not in `deliverable_extensions` | Added `.rds`, `.rdata`, `.rda`, `.feather`, `.parquet` to the default list | `config/schema.py` |
| Cat-4: `_SPRINTF_RE` only handled single `%s` | Extended regex and resolution logic to handle multiple `%s`/`%d`/`%f`/`%i`/`%g` placeholders | `parser/r_extract.py` |

Final edge list from fixture project (`tests/fixtures/r_dynamic_paths`):

```
source,target,command,kind
data/raw.csv,analysis.r,read_csv,reference_input
data/results.parquet,analysis/arrow_var.r,read_parquet,reference_input
data/large_file.csv,analysis/fread_var.r,fread,reference_input
data/input.csv,analysis/getsrcfilename.r,read_csv,reference_input      ← was MISSING
data/survey.dta,analysis/haven_var.r,read_dta,reference_input
data/input.csv,analysis/here_pkg.r,read_csv,reference_input
data/results.csv,analysis/multiline.r,read_csv,reference_input          ← was MISSING
data/input.csv,analysis/paste0_inline.r,read_csv,reference_input
data/results.csv,analysis/paste0_var_base.r,read_csv,reference_input    ← was MISSING
data/results.csv,analysis/process.r,read_csv,reference_input            ← was MISSING
data/spreadsheet.xlsx,analysis/readxl_var.r,read_excel,reference_input
data/input.csv,analysis/robust_paths.r,read_csv,reference_input         ← was MISSING
data/input.csv,analysis/rstudioapi_path.r,read_csv,reference_input      ← was MISSING
data/results_final.csv,analysis/sprintf_var.r,read_csv,reference_input  ← was MISSING
c:/project/models/fit.rds,load_data.r,readRDS,reference_input
data/results.csv,load_data.r,read_csv,reference_input
results/output.csv,reader.r,read_csv,generated_artifact
analysis.r,results/model.rds,saveRDS,deliverable                        ← was SUPPRESSED
analysis/here_pkg.r,output/processed.csv,write_csv,deliverable
analysis/process.r,output/processed.csv,write_csv,deliverable           ← was MISSING
analysis/write_var.r,output/model.rds,saveRDS,deliverable               ← was SUPPRESSED
analysis/write_var.r,output/result.csv,write_csv,deliverable
writer.r,results/output.csv,write_csv,deliverable
```

Test suite: 224 pass, 2 pre-existing failures (unrelated to these changes).

## Test matrix

| # | Script | Pattern | Expected edge | Detected? | Notes |
|---|--------|---------|---------------|-----------|-------|
| 1 | analysis/process.R | `sys.frame(1)$ofile` + `file.path` → `data/results.csv` read | data/results.csv → process.r | MISSING | `sys.frame(1)$ofile` not in `_VAR_ASSIGN_RE`; variable assigned via function call |
| 2 | analysis/process.R | `sys.frame(1)$ofile` + `file.path` → `output/processed.csv` write | process.r → output/processed.csv | MISSING | Same root cause as #1 |
| 3 | analysis/robust_paths.R | `tryCatch(dirname(sys.frame(1)$ofile), ...)` + `file.path` | data/input.csv → robust_paths.r | MISSING | `tryCatch` multi-line assignment not resolved; `sys.frame` not recognized |
| 4 | analysis/multiline.R | Multi-line `file.path(\n  base_dir,\n  "results.csv"\n)` | data/results.csv → multiline.r | MISSING | `_FILEPATH_RE` uses `[^)]+` which doesn't match newlines; multi-line calls unsupported |
| 5 | analysis/getsrcfilename.R | `getSrcFilename(function(){}, full.names=TRUE)` | data/input.csv → getsrcfilename.r | MISSING | `getSrcFilename()` not recognized; variable assigned via function call |
| 6 | analysis/rstudioapi_path.R | `rstudioapi::getActiveDocumentContext()$path` | data/input.csv → rstudioapi_path.r | MISSING | `rstudioapi::getActiveDocumentContext()` not recognized; variable assigned via function call |
| 7 | analysis/here_pkg.R | `read.csv(here("data", "input.csv"))` | data/input.csv → here_pkg.r | OK | `here()` resolved correctly |
| 8 | analysis/here_pkg.R | `write.csv(df, here("output", "processed.csv"))` | here_pkg.r → output/processed.csv | OK | `here()` in write position resolved correctly |
| 9 | analysis/paste0_var_base.R | `base <- "../data"` + `path <- paste0(base, "/results.csv")` + `read.csv(path)` | data/results.csv → paste0_var_base.r | MISSING | `paste0` resolves to `"../data//results.csv"` but assignment `path <- paste0(...)` is not captured by `_VAR_ASSIGN_RE` (which only handles string literals); bare-var expansion of `path` fails because `path` never entered `vars_map` |
| 10 | analysis/sprintf_var.R | `base <- "../data"` + `path <- sprintf("%s/results_%s.csv", base, "final")` + `read.csv(path)` | data/results_final.csv → sprintf_var.r | MISSING | Two `%s` placeholders: `_SPRINTF_RE` only handles single `%s`; even if it did, `path` never enters `vars_map` |
| 11 | analysis/paste0_inline.R | `prefix <- "../data/"` + `read.csv(paste0(prefix, "input.csv"))` | data/input.csv → paste0_inline.r | OK | `paste0` resolved inline at call site; `prefix` is literal string var in `vars_map` |
| 12 | analysis/fread_var.R | `path <- "../data/large_file.csv"` + `dt <- fread(path)` | data/large_file.csv → fread_var.r | OK | Literal string var expanded at call site |
| 13 | analysis/haven_var.R | `path <- "../data/survey.dta"` + `df <- read_dta(path)` | data/survey.dta → haven_var.r | OK | Literal string var expanded at call site |
| 14 | analysis/readxl_var.R | `path <- "../data/spreadsheet.xlsx"` + `df <- read_excel(path)` | data/spreadsheet.xlsx → readxl_var.r | OK | Literal string var expanded at call site |
| 15 | analysis/arrow_var.R | `path <- "../data/results.parquet"` + `df <- read_parquet(path)` | data/results.parquet → arrow_var.r | OK | Literal string var expanded at call site |
| 16 | analysis/write_var.R | `out <- "../output"` + `write.csv(df, file.path(out, "result.csv"))` | write_var.r → output/result.csv | OK | `file.path` with literal var resolved inline |
| 17 | analysis/write_var.R | `out <- "../output"` + `saveRDS(model, file.path(out, "model.rds"))` | write_var.r → output/model.rds | SUPPRESSED | Regex matches correctly; `file.path` resolves correctly; edge is detected internally but then **suppressed** because `.rds` is not in `deliverable_extensions` and no downstream consumer exists |
| 18 | load_data.R | `data_path <- "C:/project/data/results.csv"` + `read.csv(data_path)` | absolute path node → load_data.r | OK (absolute) | Absolute path extracted correctly; `absolute_path` diagnostic fired |
| 19 | load_data.R | `model_path <- "C:/project/models/fit.rds"` + `readRDS(model_path)` | absolute path node → load_data.r | OK (absolute) | Absolute path extracted correctly; `absolute_path` diagnostic fired |

---

## Confirmed missing edges

| Script | Pattern | Expected edge | Root cause |
|--------|---------|---------------|------------|
| analysis/process.R | `sys.frame(1)$ofile` → `file.path` → `read.csv` | data/results.csv | `_VAR_ASSIGN_RE` only matches `var <- "literal"` — function calls on RHS not captured |
| analysis/process.R | `sys.frame(1)$ofile` → `file.path` → `write.csv` | output/processed.csv | Same as above |
| analysis/robust_paths.R | `tryCatch(dirname(...), ...)` multi-line assignment | data/input.csv | Multi-line assignment not supported; `tryCatch` RHS not recognized |
| analysis/multiline.R | Multi-line `file.path(\n  var,\n  "file"\n)` | data/results.csv | `_FILEPATH_RE` regex `[^)]+` does not span newlines — multi-line calls invisible |
| analysis/getsrcfilename.R | `getSrcFilename(function(){}, ...)` as script locator | data/input.csv | `getSrcFilename()` not in `_VAR_ASSIGN_RE` recognized patterns |
| analysis/rstudioapi_path.R | `rstudioapi::getActiveDocumentContext()$path` | data/input.csv | `rstudioapi::getActiveDocumentContext()` not recognized |
| analysis/paste0_var_base.R | `path <- paste0(base, "/results.csv")` then `read.csv(path)` | data/results.csv | Intermediate path variable assigned via `paste0()` — `_VAR_ASSIGN_RE` requires literal string RHS |
| analysis/sprintf_var.R | `path <- sprintf("%s/results_%s.csv", base, "final")` then `read.csv(path)` | data/results_final.csv | (1) `_SPRINTF_RE` only handles single `%s`; (2) intermediate var assignment via `sprintf()` not captured |

---

## Suppressed (detected internally but dropped from graph)

| Script | Pattern | Expected edge | Why suppressed |
|--------|---------|---------------|----------------|
| analysis/write_var.R | `saveRDS(model, file.path(out, "model.rds"))` | write_var.r → output/model.rds | `.rds` not in `deliverable_extensions` (only `.csv`, `.xlsx`, `.pdf`, `.png`, `.svg`, `.docx`, `.tex`, `.ster`); no downstream consumer → `suppressed_internal_only` logic drops the edge |
| analysis.R | `saveRDS(model, here("results", "model.rds"))` | analysis.r → results/model.rds | Same suppression: `.rds` not in `deliverable_extensions` |

---

## Patterns already working

- `here("dir", "file.ext")` at call site (read and write) — fully resolved
- `here::here(...)` — fully resolved
- `file.path(literal_var, "file.ext")` where var is assigned a string literal — resolved
- `paste0(literal_var, "/file.ext")` — resolved inline at call site
- String literal variable → bare var name at read/write call site (`fread`, `read_dta`, `read_excel`, `read_parquet`, etc.)
- Absolute path in literal string variable → bare var expansion at call site (with `absolute_path` diagnostic)
- All read functions: `read.csv`, `fread`, `read_dta`, `read_excel`, `read_parquet` — detect literal or expanded-literal paths
- Write functions for deliverable extensions: `write.csv` with resolved path — detected

---

## Additional patterns tested beyond task description

1. **`saveRDS` write suppression (`.rds` not a deliverable extension)** — regex matching works but edge is dropped by `suppressed_internal_only` logic in `stata_extract.py`. Fix requires adding `.rds` (and other R binary formats: `.rda`, `.rdata`, `.feather`, `.parquet`) to `deliverable_extensions` defaults, or applying `deliverable` role to `saveRDS` outputs.

2. **Intermediate path variable via `paste0`** (`path <- paste0(base, "/file.csv")` then `read.csv(path)`) — `path` never enters `vars_map` because `_VAR_ASSIGN_RE` only matches `var <- "literal"`. The `paste0()` resolution in `_preprocess_helpers` only works at the exact call site, not when the resolved path is assigned to a new variable.

3. **`sprintf` with 2 `%s` arguments** (`sprintf("%s/results_%s.csv", base, "final")`) — `_SPRINTF_RE` has a hard constraint: `template.count('%s') == 1`. Two-substitution patterns silently fail.

---

## Summary statistics

- Patterns tested: 19 (across 14 scripts)
- Fully working: 9
- Missing (no edge produced): 8
- Suppressed (edge produced internally but dropped): 2
- False positives: 0

---

## Root cause categories

### Cat-1: `_VAR_ASSIGN_RE` only captures `var <- "literal"` assignments
Affects: `sys.frame`, `getSrcFilename`, `rstudioapi`, `tryCatch`, `paste0/sprintf` intermediate assignment.
The parser cannot track variables whose values come from function calls.

### Cat-2: Single-line regex for multi-line function calls
Affects: multi-line `file.path(...)` calls.
`_FILEPATH_RE` (and all other helper regexes) use `[^)]+` which does not cross line boundaries.
The parser joins no lines before applying regexes.

### Cat-3: `.rds` not in `deliverable_extensions`
Affects: `saveRDS`, `save()` to `.rda`/`.rdata`, `write_rds()`.
The Stata-centric suppression logic treats `.rds` outputs without downstream consumers as internal intermediates and drops them from the graph.

### Cat-4: `_SPRINTF_RE` single-`%s` restriction
Affects: any `sprintf` with 2+ format placeholders.
