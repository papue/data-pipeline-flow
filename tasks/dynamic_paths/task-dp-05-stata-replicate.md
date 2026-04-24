# Task DP-05 — Stata dynamic paths: Replication

## Status
- [x] `stata_extract.py` read and understood
- [x] Fixture do-files written covering known and brainstormed patterns
- [x] Tool run against fixtures; missing edges captured
- [x] FINDINGS.md written for fix agent

---

## Goal

Write Stata dummy do-files that use dynamic path patterns. Run the tool against them.
Prove which expected edges are **not** detected. Think beyond the patterns listed here —
real Stata research projects have many path-building idioms.

Do NOT fix anything. Just run the CLI and document what's missing.

---

## Setup

```
.venv\Scripts\activate
data-pipeline-flow extract-edges --project-root <fixture_dir> --output edges.csv
```

---

## Step 1 — Read the extractor first

Read `src/data_pipeline_flow/parser/stata_extract.py` before writing fixtures. Understand:
- How `globals_map` and `local_map` are populated and used
- What `_resolve_dynamic_path` handles
- Whether `c(pwd)` / `c(current_do_file)` are recognized system constants
- Whether `///` line continuation is preprocessed
- Whether backslash-based Windows paths in macros are handled

This tells you which patterns already work (skip those) and which are gaps.

---

## Step 2 — Create fixture project

Create `tests/fixtures/stata_dynamic_paths/` as a self-contained project.

### 2a — `c(pwd)` system constant used to build a path

File: `tests/fixtures/stata_dynamic_paths/scripts/run_analysis.do`
```stata
local datadir "`c(pwd)'/data"
use "`datadir'/analysis.dta", clear
save "`datadir'/results.dta", replace
```

Create empty placeholders:
- `tests/fixtures/stata_dynamic_paths/data/analysis.dta`
- `tests/fixtures/stata_dynamic_paths/data/results.dta`

Expected edges: `data/analysis.dta` read, `data/results.dta` write.

### 2b — `c(current_do_file)` to get the running script's path (Stata 16+)

File: `tests/fixtures/stata_dynamic_paths/scripts/script_relative.do`
```stata
local mydir = subinstr("`c(current_do_file)'", "/scripts/script_relative.do", "", .)
use "`mydir'/data/clean.dta", clear
```

Create: `tests/fixtures/stata_dynamic_paths/data/clean.dta`

Expected edge: `data/clean.dta` read.
(Note: `subinstr` is hard to evaluate statically. The fix agent will decide how to handle
this — either resolve it or emit a placeholder. Document whether anything is detected.)

### 2c — Global macro set to absolute path string

File: `tests/fixtures/stata_dynamic_paths/absolute_global.do`
```stata
global datapath "C:\research\project\data"
use "$datapath\clean.dta", clear
save "$datapath\output.dta", replace
```

Expected: absolute-path nodes extracted (with `absolute_path` diagnostic).

### 2d — Local macro set to absolute path string

File: `tests/fixtures/stata_dynamic_paths/absolute_local.do`
```stata
local datapath "C:\research\project\data"
use "`datapath'\clean.dta", clear
```

Expected: absolute-path node extracted.

### 2e — `///` line continuation in macro definition

File: `tests/fixtures/stata_dynamic_paths/continuation.do`
```stata
local longpath ///
    "../data"
use "`longpath'/input.dta", clear
save "`longpath'/output.dta", replace
```

Create:
- `tests/fixtures/stata_dynamic_paths/data/input.dta`
- `tests/fixtures/stata_dynamic_paths/data/output.dta`

Expected edges: `data/input.dta` read, `data/output.dta` write.

---

## Step 3 — Brainstorm additional Stata patterns and test them

Think about what real Stata research do-files do with paths. Add scripts to the fixture project:

**Path macro building patterns:**
```stata
* Concatenated global building
global root "C:\project"
global data "$root\data"
use "$data\analysis.dta", clear

* Relative path in global, joined with filename
global ddir "../data/"
use "${ddir}analysis.dta", clear

* cd + relative paths (very common pattern)
cd "../data"
use "analysis.dta", clear      // ← path is just a filename relative to cd

* Local built from another local
local base "../data"
local file "`base'/results.dta"
use "`file'", clear
```

**Non-use/save read/write verbs with macros:**
```stata
* insheet / import delimited
global datadir "../data"
import delimited using "$datadir/survey.csv", clear

* outsheet / export delimited
export delimited "$datadir/output.csv", replace

* infile / infix
local raw "../rawdata"
insheet using "`raw'/responses.csv"

* log using with path
local logdir "../logs"
log using "`logdir'/run.log", replace text
```

**Nested macro expansion:**
```stata
global root "C:\project"
global sub "analysis"
global full "$root\$sub\results.dta"
use "$full", clear
```

**Conditional paths:**
```stata
if "`c(os)'" == "Windows" {
    global data "C:\project\data"
}
else {
    global data "/home/user/project/data"
}
use "$data\analysis.dta", clear
```
(The static parser likely can't resolve conditional macros — document what happens.)

For each variant:
1. Add a do-file to the fixture project
2. Create the expected data file (empty)
3. Run the tool
4. Note detected vs. missing

---

## Step 4 — Write the findings report

Create `tests/fixtures/stata_dynamic_paths/FINDINGS.md`:

```markdown
# Stata dynamic path replication findings

## Confirmed missing edges

| Script | Pattern | Expected edge | Tool output |
|--------|---------|---------------|-------------|
| scripts/run_analysis.do | c(pwd) local macro | data/analysis.dta | (nothing) |
| ... | ... | ... | ... |

## Patterns already working
- ...

## Additional patterns tested beyond task description
- ...

## Patterns that are inherently dynamic (cannot be statically resolved)
- conditional os-based paths (c(os) branch) — document expected behavior
```
