# Task DP-01 — Python dynamic paths: Replication

## Status
- [x] Fixture scripts written
- [x] Tool run against fixtures; output captured showing missing edges
- [x] Additional similar patterns brainstormed and tested
- [x] Final inventory of undetected patterns documented for fix agent

---

## Goal

Write Python dummy scripts that use dynamic path patterns. Run the tool against them.
Prove that the expected data edges are **not** detected. Then document exactly what is
missing so the fix agent knows what to target.

Do NOT fix anything. Do NOT write pytest tests. Just run the CLI and capture output.

---

## Background

`python_extract.py` has variable tracking but does not substitute `__file__` with the
currently-parsed script's path. Full details: `HANDOVER_DYNAMIC_PATHS.md` (project root).

---

## Setup

Activate the venv first:
```
.venv\Scripts\activate     (Windows)
```

The CLI command to check what edges are found:
```
data-pipeline-flow extract-edges --project-root <fixture_dir> --output edges.csv
cat edges.csv
```

Also useful for a broader picture:
```
data-pipeline-flow summary --project-root <fixture_dir>
```

---

## Step 1 — Create fixture project

Create `tests/fixtures/python_dynamic_paths/` as a self-contained project.

### 1a — `__file__` relative path via `os.path.join` + f-string

File: `tests/fixtures/python_dynamic_paths/analysis/generate_graphs.py`
```python
import os
import pandas as pd

try:
    _script_dir = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _script_dir = os.path.join(os.getcwd(), 'analysis')

data_path = os.path.join(_script_dir, '..', 'results') + os.sep
df = pd.read_parquet(f"{data_path}all_results.parquet")
df2 = pd.read_parquet(f"{data_path}all_results_multiT.parquet")
```

Expected edges: `results/all_results.parquet`, `results/all_results_multiT.parquet`

Create empty placeholder files so they show as resolvable nodes:
- `tests/fixtures/python_dynamic_paths/results/all_results.parquet`
- `tests/fixtures/python_dynamic_paths/results/all_results_multiT.parquet`

### 1b — Absolute path stored in variable → passed to `read_parquet(var)`

File: `tests/fixtures/python_dynamic_paths/generate_output.py`
```python
import pandas as pd

results_path = r"C:\project\results\all_results.parquet"
df = pd.read_parquet(results_path)
```

File: `tests/fixtures/python_dynamic_paths/extract_data.py`
```python
import os
import pandas as pd

path_base = r"C:\project\results"
save_path = os.path.join(path_base, "all_results.parquet")
df = pd.DataFrame()
df.to_parquet(save_path, index=False)
```

Expected: absolute-path nodes extracted (with `absolute_path` diagnostic), edges present.

### 1c — Multi-line `os.path.join(__file__, ...)` assigned to module constant

File: `tests/fixtures/python_dynamic_paths/analysis/profit_heatmap.py`
```python
import os
import json

RESULTS_BASE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "results", "demand_benchmark"
)

param_file = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "parameters", "param_file.json"
)
with open(param_file) as f:
    params = json.load(f)
```

Create empty: `tests/fixtures/python_dynamic_paths/parameters/param_file.json`

Expected edge: `parameters/param_file.json` read.

---

## Step 2 — Run the tool and capture missing edges

Run:
```
data-pipeline-flow extract-edges \
  --project-root tests/fixtures/python_dynamic_paths \
  --output /tmp/dp01_edges.csv
cat /tmp/dp01_edges.csv
```

For each fixture script, check whether the expected edges appear. Document exactly what
is present vs. absent in the output.

---

## Step 3 — Brainstorm similar patterns and test them

Think beyond the handover. Add more scripts to the same fixture project and test them.
Below are categories to consider — implement as many as you think are plausibly common
in Python research code:

**`__file__`-based variants:**
```python
# Variant: Path object instead of os.path
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent / "data"
df = pd.read_csv(BASE / "input.csv")

# Variant: __file__ used directly in Path() without dirname
ROOT = Path(__file__).parent / ".." / "results"
df = pd.read_parquet(ROOT / "output.parquet")

# Variant: __file__ assigned to intermediate var
this_file = Path(__file__)
project_root = this_file.parent.parent
df = pd.read_csv(project_root / "data" / "input.csv")
```

**Variable path variants:**
```python
# Variant: concatenation instead of os.path.join
base = "C:/project/data/"
df = pd.read_csv(base + "input.csv")

# Variant: pathlib Path() from string literal
from pathlib import Path
p = Path("C:/project/data/input.csv")
df = pd.read_csv(p)

# Variant: string format instead of f-string
base = "../data"
path = "%s/input.csv" % base
df = pd.read_csv(path)

# Variant: .format() method
base = "../data"
path = "{}/input.csv".format(base)
df = pd.read_csv(path)
```

**`open()` and non-pandas read patterns:**
```python
# open() for JSON/text reads
with open(os.path.join(_script_dir, "..", "config", "params.json")) as f:
    config = json.load(f)

# pickle
import pickle
with open(os.path.join(_script_dir, "..", "results", "model.pkl"), "rb") as fh:
    model = pickle.load(fh)
```

For each variant you add:
1. Create a script in the fixture project
2. Create the expected data file (empty)
3. Run the tool
4. Note whether the edge is detected or missed

---

## Step 4 — Write the findings report

Create `tests/fixtures/python_dynamic_paths/FINDINGS.md` with:

```markdown
# Python dynamic path replication findings

## Confirmed missing edges

| Script | Pattern | Expected edge | Tool output |
|--------|---------|---------------|-------------|
| analysis/generate_graphs.py | __file__ + os.path.join + f-string | results/all_results.parquet | (nothing) |
| ... | ... | ... | ... |

## Patterns already working (no fix needed)
- ...

## Additional patterns tested beyond handover
- ...
```

This file is the handover to the fix agent.
