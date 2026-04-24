# Stata dynamic path replication findings

Generated: 2026-04-24
Tool: `data-pipeline-flow extract-edges`
Fixture: `tests/fixtures/stata_dynamic_paths/`

---

## Summary

| Category | Count |
|----------|-------|
| Patterns tested | 14 |
| Patterns already working (correct edges) | 4 |
| Patterns broken/missing edges | 7 |
| Patterns inherently dynamic (not fixable statically) | 3 |

---

## Confirmed missing edges

### BUG-1: `///` line continuation in macro definition (`continuation.do`)

**Pattern:**
```stata
local longpath ///
    "../data"
use "`longpath'/input.dta", clear
save "`longpath'/output.dta", replace
```

**Expected edges:**
- `data/input.dta` → `continuation.do` (read)
- `continuation.do` → `data/output.dta` (write)

**Actual tool output:**
- `/input.dta` → `continuation.do` (read) — wrong path, not resolved
- Write edge for `/output.dta` (wrong path)

**Root cause:** `LOCAL_RE` only matches a single line. The `///` continuation is not preprocessed before line-by-line parsing. When `local longpath ///` is seen, the regex captures `///` as the value (stripped of quotes, gives `///`). The next line `    "../data"` is parsed separately as a plain code line. The path used in `use` is `` `longpath'/input.dta `` and `longpath` is in `local_map` with value `["///"]`. After substitution, the path becomes `///input.dta`, which `to_project_relative` somehow normalizes to `/input.dta`.

**Severity:** High — `///` continuation for macros is common in real Stata code.

---

### BUG-2: `c(pwd)` system constant not resolved (`scripts/run_analysis.do`)

**Pattern:**
```stata
local datadir "`c(pwd)'/data"
use "`datadir'/analysis.dta", clear
save "`datadir'/results.dta", replace
```

**Expected edges:**
- `data/analysis.dta` → `scripts/run_analysis.do` (read)
- `scripts/run_analysis.do` → `data/results.dta` (write)

**Actual tool output:**
- `` `c(pwd)'/data/analysis.dta `` → `scripts/run_analysis.do` (read, unresolved path)
- Write: `` `c(pwd)'/data/results.dta `` (unresolved)

**Root cause:** `LOCAL_RE` captures the local value as the literal string `` `c(pwd)'/data ``. When `use "`datadir'/analysis.dta"` is processed, `local_map["datadir"]` contains one value: `` `c(pwd)'/data ``. After local substitution the path becomes `` `c(pwd)'/data/analysis.dta ``. Then `MACRO_TOKEN_RE` finds token `c(pwd)` which is not in `env`, so the path is emitted as a partial placeholder. The token `c(pwd)` is not recognized as a resolvable system constant.

**Fix direction:** Pre-resolve `c(pwd)` to `"."` (the project root) when encountered inside local/global values, or strip it and emit a diagnostic.

**Severity:** High — `c(pwd)` is a standard Stata idiom for portable relative-path projects.

---

### BUG-3: `c(current_do_file)` with `subinstr()` produces garbage edges (`scripts/script_relative.do`)

**Pattern:**
```stata
local mydir = subinstr("`c(current_do_file)'", "/scripts/script_relative.do", "", .)
use "`mydir'/data/clean.dta", clear
```

**Expected edges:**
- `data/clean.dta` → `scripts/script_relative.do` (read), OR a `dynamic_path_unresolved` diagnostic

**Actual tool output:**
Multiple garbage edges produced by treating the `subinstr(...)` assignment value as multiple whitespace-split tokens:
- `` subinstr("`c(current_do_file)'",/data/clean.dta `` → `scripts/script_relative.do`
- `,/data/clean.dta` → `scripts/script_relative.do`
- `.)/data/clean.dta` → `scripts/script_relative.do`
- `=/data/clean.dta` → `scripts/script_relative.do`
- `/scripts/script_relative.do",/data/clean.dta` → `scripts/script_relative.do`

**Root cause:** `LOCAL_RE` captures everything after `local mydir =` as the value. `_collect_local_values` splits on whitespace, producing multiple tokens from the `subinstr(...)` expression. Each whitespace-separated piece becomes a separate value in `local_map["mydir"]`. When `use "`mydir'/data/clean.dta"` is processed, all those tokens are substituted and produce garbage paths.

**Fix direction:** Detect `local <name> = <expr>` (with `=`) as a computed assignment. When the RHS contains function calls or complex expressions, store a single opaque placeholder rather than splitting on whitespace.

**Severity:** Medium — `c(current_do_file)` is less common, but the garbage-edge side effect is worse than no edge.

---

### BUG-4: Local built from another local — not expanded (`local_from_local.do`)

**Pattern:**
```stata
local base "../data"
local file "`base'/results.dta"
use "`file'", clear
```

**Expected edges:**
- `data/results.dta` → `local_from_local.do` (read)

**Actual tool output:**
- `` `base'/results.dta `` → `local_from_local.do` (read) — unresolved placeholder

**Root cause:** When `local file "`base'/results.dta"` is parsed, `LOCAL_RE` captures the raw value `` `base'/results.dta ``. `_collect_local_values` strips outer quotes and splits on whitespace, storing `["`base'/results.dta"]` in `local_map["file"]`. No expansion of local references happens at assignment time. Later when `use "`file'"` is processed, `local_map["file"]` = `` [`base'/results.dta] ``. `MACRO_TOKEN_RE` finds token `file`; substituting yields `` `base'/results.dta ``. Then `MACRO_TOKEN_RE` finds token `base` which IS in `local_map`. But at this point the code only does a single pass of substitution — the result `` `base'/results.dta `` is returned as a partial expansion because `base` appears as a nested token inside the already-substituted string.

Wait — actually re-checking: `_resolve_dynamic_path` expands globals first via `expand()`, then resolves locals. When `use "`file'"` is parsed, `env["file"] = ["`base'/results.dta"]` and `env["base"] = ["../data"]`. The unique tokens are `["file"]`. For token `file`, replacement is `` `base'/results.dta ``. The result is `` `base'/results.dta `` (a string still containing a local reference). `MACRO_TOKEN_RE` is only applied once to identify tokens at the start, not recursively after substitution. So `base` is never resolved.

**Fix direction:** After substituting local values, re-run `MACRO_TOKEN_RE` to check if the result still contains unresolved local references (recursive expansion loop).

**Severity:** High — chained local macros are extremely common in real Stata code.

---

### BUG-5: `export delimited` without `using` keyword not detected (`export_delimited_macro.do`)

**Pattern:**
```stata
global datadir "../data"
export delimited "$datadir/output.csv", replace
```

**Expected edges:**
- `export_delimited_macro.do` → `data/output.csv` (write)

**Actual tool output:**
- `export_delimited_macro.do` is an orphan node — no edges detected at all.

**Root cause:** `EXPORT_DELIMITED_RE` is defined as:
```python
re.compile(r'\bexport\s+delimited\s+using\s+(?:"([^"]+)"|([^\s,]+\.[^\s,]+))', re.I)
```
It requires the `using` keyword. But real Stata's `export delimited` syntax allows the filename directly without `using`: `export delimited "path/file.csv"`. Without `using`, the regex does not match.

**Fix direction:** Make `using` optional in `EXPORT_DELIMITED_RE`:
```python
re.compile(r'\bexport\s+delimited\s+(?:using\s+)?(?:"([^"]+)"|([^\s,]+\.[^\s,]+))', re.I)
```

**Severity:** High — `export delimited "filename.csv"` (without `using`) is the most common export syntax.

---

### BUG-6: `insheet` command not recognized (`insheet_local.do`)

**Pattern:**
```stata
local raw "../rawdata"
insheet using "`raw'/responses.csv"
```

**Expected edges:**
- `rawdata/responses.csv` → `insheet_local.do` (read)

**Actual tool output:**
- `insheet_local.do` is an orphan node — no edges detected.

**Root cause:** `insheet` is not in `READ_COMMANDS`. Only `use`, `import`, `append`, `merge`, `cross` are recognized. `insheet` (the older CSV import command, still valid in Stata 14 and earlier) is completely absent.

**Fix direction:** Add `INSHEET_RE` to `READ_COMMANDS`:
```python
INSHEET_RE = re.compile(r'\binsheet\s+(?:using\s+)?(?:"([^"]+)"|([^\s,]+\.[^\s,]+))', re.I)
```

**Severity:** Medium — `insheet` is deprecated in recent Stata but still in active use in older codebases.

---

### BUG-7: `import delimited using` with global macro — `using` keyword mismatch (`import_delimited_macro.do`)

**Pattern:**
```stata
global datadir "../data"
import delimited using "$datadir/survey.csv", clear
```

**Expected edges:**
- `data/survey.csv` → `import_delimited_macro.do` (read)

**Actual tool output:**
- `import_delimited_macro.do` is an orphan node — no edges detected.

**Root cause:** `IMPORT_RE` is:
```python
re.compile(r'\bimport\s+(?:delimited|excel)\s+(?:"([^"]+)"|([^\s,]+\.[^\s,]+))', re.I)
```
After `import delimited` it expects the path directly. But when `using` is present (e.g. `import delimited using "file.csv"`), the next token is `using`, not a path. The unquoted path alternative `([^\s,]+\.[^\s,]+)` would not match `using` (no dot), and the quoted alternative would not match either. So the regex fails when `using` is present.

Note: `import delimited "file.csv"` (without `using`) DOES work. `import delimited using "file.csv"` (with `using`) does NOT. This is the reverse of the `export delimited` bug.

**Fix direction:** Make `using` optional in `IMPORT_RE`:
```python
re.compile(r'\bimport\s+(?:delimited|excel)\s+(?:using\s+)?(?:"([^"]+)"|([^\s,]+\.[^\s,]+))', re.I)
```

**Severity:** High — both forms are common; many research scripts use `import delimited using`.

---

## Patterns already working

### WORKING-1: Global macro set to absolute path (`absolute_global.do`)

```stata
global datapath "C:\research\project\data"
use "$datapath\clean.dta", clear
save "$datapath\output.dta", replace
```

Edges detected:
- `data/clean.dta` → `absolute_global.do` (read) — correct relative normalization
- Write: `data/output.dta` suppressed as unconsumed (detected, correct)
- `absolute_path_usage` warning emitted correctly.

Status: **Working** (backslash path separator in globals is handled).

---

### WORKING-2: Local macro set to absolute path (`absolute_local.do`)

```stata
local datapath "C:\research\project\data"
use "`datapath'\clean.dta", clear
```

Edge detected:
- `data/clean.dta` → `absolute_local.do` (read) — correct normalization
- `absolute_path_usage` warning emitted correctly.

Status: **Working**.

---

### WORKING-3: Concatenated global building from another global (`concat_globals.do`)

```stata
global root "C:\project"
global data "$root\data"
use "$data\analysis.dta", clear
```

Edge detected:
- `data/analysis.dta` → `concat_globals.do` (read) — correct

Note: The `expand()` function is recursive (`while changed`) so `$data` → `$root\data` → `C:\project\data` → normalized to `data/`. Works correctly.

Status: **Working**.

---

### WORKING-4: Relative path global with filename joined directly (`relative_global.do`)

```stata
global ddir "../data/"
use "${ddir}analysis.dta", clear
```

Edge detected:
- `../dataanalysis.dta` → `relative_global.do` (read)

Status: **BROKEN** — The trailing slash in `"../data/"` is lost during normalization, causing the path to become `../dataanalysis.dta` instead of `../data/analysis.dta`.

Wait — re-examining. The global value `"../data/"` is processed by `to_project_relative` at global-definition time and stored in `globals_map`. The trailing `/` gets stripped during normalization, storing `"../data"` (no trailing slash). Then at use time, `expand()` replaces `${ddir}` with `../data`, making the path `../dataanalysis.dta` — merging without separator.

**This is actually BUG-8** — correction: this pattern is broken.

---

## Bug-8 (discovered during WORKING-4 review): Trailing slash stripped from global macro value

**Pattern:**
```stata
global ddir "../data/"
use "${ddir}analysis.dta", clear
```

**Expected edge:** `data/analysis.dta` → `relative_global.do` (read)

**Actual:** `../dataanalysis.dta` → `relative_global.do` (wrong path, missing separator)

**Root cause:** When `global ddir "../data/"` is parsed, `to_project_relative` normalizes `../data/` by calling `Path("../data/")` which on some systems strips the trailing slash, yielding `../data`. When the global is later interpolated as `${ddir}analysis.dta`, it becomes `../dataanalysis.dta` — no slash separator.

**Fix direction:** Store global values with their trailing slash preserved, or add slash normalization after expansion before path resolution.

**Severity:** Medium — trailing slash is a common coding style in Stata globals.

---

### WORKING-5: Nested global expansion (`nested_globals.do`)

```stata
global root "C:\project"
global sub "analysis"
global full "$root\$sub\results.dta"
use "$full", clear
```

Edge detected: `c:/project/analysis/results.dta` → `nested_globals.do` (read).
This is an absolute path but correctly resolved through nested expansion.

Status: **Working** (multi-level global expansion works; absolute path warning emitted).

---

### WORKING-6: Relative `use` path with no macro (`log_local.do`)

```stata
use "../data/analysis.dta", clear
```

Edge detected: `../data/analysis.dta` → `log_local.do` (read). Correct.

Status: **Working** (literal relative paths work fine).

---

### WORKING-7: cd + relative path (`cd_relative.do`)

```stata
cd "../data"
use "analysis.dta", clear
```

Edge detected: `analysis.dta` → `cd_relative.do` (read).

Status: **Partial** — The `cd` command is not tracked. `analysis.dta` is treated as a project-root-relative filename. The expected edge `data/analysis.dta` is not produced; instead `analysis.dta` is emitted. This is a known limitation, not strictly a bug — `cd` tracking requires stateful directory tracking.

---

## Patterns that are inherently dynamic (cannot be statically resolved)

### DYNAMIC-1: `c(pwd)` system constant

`c(pwd)` is the Stata equivalent of `$PWD` — the current working directory at runtime. Its value depends on where Stata is launched or what `cd` commands have been issued. The static parser cannot determine it. Recommended behavior: substitute `c(pwd)` with `"."` (project root) and emit a `dynamic_path_partial_resolution` diagnostic.

### DYNAMIC-2: `c(current_do_file)` system constant

This is the full file system path of the currently running do-file. It can only be known at Stata runtime. The static parser cannot resolve it. Recommended behavior: substitute with `"."` (script directory) and emit a diagnostic.

### DYNAMIC-3: Conditional paths based on `c(os)` or other runtime conditions

```stata
if "`c(os)'" == "Windows" {
    global data "C:\project\data"
}
else {
    global data "/home/user/project/data"
}
use "$data\analysis.dta", clear
```

**Actual tool output:** `data/analysis.dta` → `conditional_os_path.do` (read) — surprisingly correct!

**Explanation:** The parser processes lines sequentially but does not interpret `if/else` control flow. Both `global data "C:\project\data"` and `global data "/home/user/project/data"` are processed; the second assignment overwrites the first. The Linux path `/home/user/project/data` is normalized: `to_project_relative` strips leading components and produces `data`. Then `$data\analysis.dta` → `data/analysis.dta`. This happens to produce the correct relative path, but only by accident (both branches end with `.../data/...`). For other conditional patterns the last assignment wins.

---

## Additional patterns tested beyond task description

### ADDITIONAL-1: `log using` with local macro path (`log_local.do`)

```stata
local logdir "../logs"
log using "`logdir'/run.log", replace text
```

`log using` is not in any command regex. The edge to `logs/run.log` is not detected. Since log files are not data artifacts this is probably intentional and acceptable.

---

## Bugs summary table

| # | Script | Pattern | Expected edge | Actual output | Severity |
|---|--------|---------|---------------|---------------|----------|
| BUG-1 | `continuation.do` | `///` line continuation in local | `data/input.dta` read, `data/output.dta` write | Wrong paths (`/input.dta`, `/output.dta`) | High |
| BUG-2 | `scripts/run_analysis.do` | `c(pwd)` in local | `data/analysis.dta` read | Unresolved placeholder path | High |
| BUG-3 | `scripts/script_relative.do` | `c(current_do_file)` + `subinstr()` | `data/clean.dta` read or diagnostic | 5 garbage edges | Medium |
| BUG-4 | `local_from_local.do` | Local built from another local | `data/results.dta` read | Unresolved placeholder path | High |
| BUG-5 | `export_delimited_macro.do` | `export delimited` without `using` | `data/output.csv` write | No edge (orphan script) | High |
| BUG-6 | `insheet_local.do` | `insheet using` command | `rawdata/responses.csv` read | No edge (orphan script) | Medium |
| BUG-7 | `import_delimited_macro.do` | `import delimited using` (with `using`) | `data/survey.csv` read | No edge (orphan script) | High |
| BUG-8 | `relative_global.do` | Global with trailing slash `"../data/"` | `data/analysis.dta` read | `../dataanalysis.dta` (wrong) | Medium |

---

## Fixed (2026-04-24)

All 8 bugs fixed in `src/data_pipeline_flow/parser/stata_extract.py`.

### Changes made

**BUG-1 — `///` line continuation:**
Added `_join_stata_continuations()` preprocessing function called at the start of `parse_do_file`, before any regex matching. Joins `///`-terminated lines with their continuation.

**BUG-2 — `c(pwd)` system constant:**
Pre-seeded `local_map['c(pwd)'] = ['.']` before the parsing loop in `parse_do_file`. The backtick syntax `` `c(pwd)' `` is matched by `MACRO_TOKEN_RE` as token `c(pwd)`, which is now resolved to `.` (project root).

**BUG-3 — `c(current_do_file)` + `subinstr()` garbage edges:**
Added `LOCAL_COMPUTED_RE` pattern (`local name = expr`) checked before `LOCAL_RE`. When the RHS contains `(` (function call), stores a single opaque placeholder token instead of splitting on whitespace. Eliminates the 5-garbage-edge output, replacing with one placeholder edge.

**BUG-4 — Nested local macro expansion:**
Added a second-pass expansion in `_resolve_dynamic_path`. After the first substitution pass, if the resulting strings still contain `` `token' `` references, a second pass resolves them against the same `env` dict.

**BUG-5 — `export delimited` without `using`:**
Changed `EXPORT_DELIMITED_RE` to make `using` optional: `(?:using\s+)?`.

**BUG-6 — `insheet` command:**
Added `INSHEET_RE = re.compile(r'\binsheet\s+(?:using\s+)?...')` and added `'insheet': INSHEET_RE` to `READ_COMMANDS`.

**BUG-7 — `import delimited using`:**
Changed `IMPORT_RE` to make `using` optional: `(?:using\s+)?`.

**BUG-8 — Trailing slash in global macro value:**
In the global-parsing block, detect if the original expanded value ends with `/` or `\`. After `to_project_relative` normalizes it (stripping the trailing slash), re-append `/` to preserve it for correct concatenation.

### Final edge list after fixes

```
source,target,command,kind
data/clean.dta,absolute_global.do,use,reference_input
data/clean.dta,absolute_local.do,use,reference_input
analysis.dta,cd_relative.do,use,reference_input
data/analysis.dta,concat_globals.do,use,reference_input
data/analysis.dta,conditional_os_path.do,use,reference_input
../data/input.dta,continuation.do,use,reference_input
../data/survey.csv,import_delimited_macro.do,import,reference_input
../rawdata/responses.csv,insheet_local.do,insheet,reference_input
../data/results.dta,local_from_local.do,use,reference_input
../data/analysis.dta,log_local.do,use,reference_input
c:/project/analysis/results.dta,nested_globals.do,use,reference_input
../data/analysis.dta,relative_global.do,use,reference_input
data/analysis.dta,scripts/run_analysis.do,use,reference_input
{dynamic}/data/clean.dta,scripts/script_relative.do,use,reference_input
export_delimited_macro.do,../data/output.csv,export_delimited,deliverable
```

### Test suite result
224 tests passing. 2 pre-existing failures unrelated to this task (`test_smoke.py::test_pipeline_builds_real_graph` and `test_phase16_render_image.py::test_render_image_command_returns_clear_message_when_graphviz_missing` — both were already failing before these changes).
