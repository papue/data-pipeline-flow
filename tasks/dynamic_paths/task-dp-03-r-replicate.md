# Task DP-03 — R dynamic paths: Replication

## Status
- [x] `r_extract.py` read and understood
- [x] Fixture R scripts written covering known and brainstormed patterns
- [x] Tool run against fixtures; missing edges captured
- [x] FINDINGS.md written for fix agent

---

## Goal

Write R dummy scripts that use dynamic path patterns. Run the tool against them. Prove
which expected edges are **not** detected. Go beyond the patterns listed below — think
about what real R research scripts do with paths.

Do NOT fix anything. Just run the CLI and document what's missing.

---

## Setup

```
.venv\Scripts\activate
data-pipeline-flow extract-edges --project-root <fixture_dir> --output edges.csv
```

---

## Step 1 — Read the extractor first

Read `src/data_pipeline_flow/parser/r_extract.py` before writing fixtures. Understand:
- What variable assignment patterns it captures (`_VAR_ASSIGN_RE`)
- What path-building functions it resolves (`here()`, `file.path()`, `paste0()`)
- Whether bare variable names at call sites are resolved
- Whether `sys.frame(1)$ofile` / `getSrcFilename()` are handled
- Whether multi-line calls are handled

This tells you which patterns are already working (skip those in fixtures) and which are gaps.

---

## Step 2 — Create fixture project

Create `tests/fixtures/r_dynamic_paths/` as a self-contained project.

### 2a — Script-relative path via `sys.frame` (R's `__file__`)

File: `tests/fixtures/r_dynamic_paths/analysis/process.R`
```r
script_dir <- dirname(sys.frame(1)$ofile)
data_path <- file.path(script_dir, "..", "data", "results.csv")
df <- read.csv(data_path)
write.csv(df, file.path(script_dir, "..", "output", "processed.csv"))
```

Create empty placeholder files:
- `tests/fixtures/r_dynamic_paths/data/results.csv`
- `tests/fixtures/r_dynamic_paths/output/processed.csv`

Expected edges: `data/results.csv` read, `output/processed.csv` write.

### 2b — tryCatch fallback (common in scripts meant to run both interactively and via Rscript)

File: `tests/fixtures/r_dynamic_paths/analysis/robust_paths.R`
```r
script_dir <- tryCatch(
  dirname(sys.frame(1)$ofile),
  error = function(e) getwd()
)
df <- read.csv(file.path(script_dir, "..", "data", "input.csv"))
```

Create: `tests/fixtures/r_dynamic_paths/data/input.csv`

Expected edge: `data/input.csv` read.

### 2c — Absolute path in variable → bare variable at call site

File: `tests/fixtures/r_dynamic_paths/load_data.R`
```r
data_path <- "C:/project/data/results.csv"
df <- read.csv(data_path)
model_path <- "C:/project/models/fit.rds"
model <- readRDS(model_path)
```

Expected: absolute-path nodes extracted (with `absolute_path` diagnostic).

### 2d — Multi-line `file.path()` call

File: `tests/fixtures/r_dynamic_paths/analysis/multiline.R`
```r
base_dir <- "../data"
data_path <- file.path(
  base_dir,
  "results.csv"
)
df <- read.csv(data_path)
```

Create: `tests/fixtures/r_dynamic_paths/data/results.csv` (already exists from 2a)

Expected edge: `data/results.csv` read.

---

## Step 3 — Brainstorm additional R patterns and test them

Think about what real R research scripts do. Add scripts to the fixture project for each
pattern you think is plausibly common:

**More `__file__` / script-location idioms:**
```r
# getSrcFilename — another way to get current script path
script_path <- getSrcFilename(function(){}, full.names=TRUE)
script_dir  <- dirname(script_path)
df <- read.csv(file.path(script_dir, "..", "data", "input.csv"))

# rstudioapi (very common in interactive research scripts)
script_dir <- dirname(rstudioapi::getActiveDocumentContext()$path)
df <- read.csv(file.path(script_dir, "..", "data", "input.csv"))

# here() package — already likely handled, but test it
library(here)
df <- read.csv(here("data", "input.csv"))
```

**Variable path building variants:**
```r
# paste0 path building with variable base
base <- "../data"
path <- paste0(base, "/results.csv")
df <- read.csv(path)

# sprintf path building
base <- "../data"
path <- sprintf("%s/results_%s.csv", base, "final")
df <- read.csv(path)

# String concatenation (less common but exists)
prefix <- "../data/"
df <- read.csv(paste0(prefix, "input.csv"))
```

**Non-standard read functions:**
```r
# data.table::fread with variable path
library(data.table)
path <- "../data/large_file.csv"
dt <- fread(path)

# haven for Stata/SPSS files
library(haven)
path <- "../data/survey.dta"
df <- read_dta(path)

# readxl
library(readxl)
path <- "../data/spreadsheet.xlsx"
df <- read_excel(path)

# arrow parquet
library(arrow)
path <- "../data/results.parquet"
df <- read_parquet(path)
```

**Write variants with variable path:**
```r
out <- "../output"
write.csv(df, file.path(out, "result.csv"))
saveRDS(model, file.path(out, "model.rds"))
```

For each variant:
1. Add a script to the fixture project
2. Create the expected data file (empty touch)
3. Run the tool
4. Note whether detected or missed

---

## Step 4 — Write the findings report

Create `tests/fixtures/r_dynamic_paths/FINDINGS.md`:

```markdown
# R dynamic path replication findings

## Confirmed missing edges

| Script | Pattern | Expected edge | Tool output |
|--------|---------|---------------|-------------|
| analysis/process.R | sys.frame(1)$ofile + file.path | data/results.csv | (nothing) |
| ... | ... | ... | ... |

## Patterns already working
- ...

## Additional patterns tested beyond task description
- ...
```
