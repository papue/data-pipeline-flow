# Installation & Setup — Critical Analysis

> Generated 2026-04-22. Two independent agents analyzed the setup/install experience from a UX and packaging engineering perspective.

---

## Where Both Agents Agree (Most Critical)

**1. Ghost `src/stata_pipeline_flow/` directory**
The rename in commit `34b86bc` left the old directory on disk with stale `__pycache__/`. Active risk for import ambiguity and broken wheels.

**2. No pipx/uv compatibility**
The package cannot be installed with `pipx install .` or `uv tool install .` because the helper scripts (`setup_project.py`, `make_pipeline.py`) live in the repo root and manipulate `sys.path` manually. They are not proper CLI entry points. `data-pipeline-flow` itself works, but the helper workflows do not survive outside the repo.

**3. Graphviz is invisible during install**
Nothing during `pip install` warns the user that Graphviz is a system-level prerequisite. The error only surfaces when they try to render an image. The README documents this, but only as a buried troubleshooting entry — not as an upfront prerequisite.

**4. Venv activation is a silent blocker**
A Stata researcher opening PowerShell for the first time hits `ModuleNotFoundError: No module named 'yaml'` with zero indication of why. No wrapper script or README section catches this at the point of failure.

---

## Agent 1 — UX/DX Analysis: Top Friction Points

### Friction #1: Venv Activation Mandatory but Undocumented
- README says "activate the venv" but never explains what it does or what failure looks like
- Wrapper scripts fail silently without activation (cryptic import error)
- No checkpoint to verify activation worked
- PowerShell execution policy issue mentioned but failure modes not explained

### Friction #2: Two Conflicting Recommended Paths
- Path A: "Recommended for beginners" → `python setup_project.py` → `python make_pipeline.py`
- Path B: "5-minute quick start" → `data-pipeline-flow summary --project-root example/project`
- These have DIFFERENT requirements (helper scripts vs. installed CLI entry point)
- No decision tree: when to use which
- Beginners bounce between both approaches and give up

### Friction #3: Graphviz PATH Hidden in Troubleshooting
- Not mentioned as a prerequisite before starting
- Windows users install Graphviz via `.msi`, expect it to work, then get a cryptic PATH error
- README's "quick fix" (`$env:Path += "..."`) is session-only and not explained as such

### Friction #4: Helper Scripts Are Fragile Wrappers
- Only work from the repo root (hardcoded `Path(__file__).resolve().parent`)
- No `--help` flag
- No clear error messages on failure
- Advertised as "recommended" but less robust than the CLI

### Friction #5: Install Modes Are Undocumented
- Helper scripts work WITHOUT `pip install -e` (via `sys.path` manipulation)
- CLI entry point REQUIRES `pip install -e`
- No documentation clarifies this distinction
- `-e` flag is never explained; user can believe they're installed when they're not

---

## Agent 2 — Packaging Engineering Analysis: Top Technical Problems

### Problem #1: No pipx/uv Compatibility
- Entry point `data-pipeline-flow = "data_pipeline_flow.cli.main:main"` in `pyproject.toml` is correct
- But helper scripts are NOT registered as console_scripts — they cannot be installed as proper CLI tools
- `pipx install .` installs `data-pipeline-flow` but none of the helper workflow commands
- The interactive wizard/setup flow is entirely inaccessible after a non-editable install

### Problem #2: Ghost `src/stata_pipeline_flow/` Directory
- Old package directory still exists on disk after rename commit `34b86bc`
- Contains stale `__pycache__/` for config, model, parser, rules, validation
- Risk: import ambiguity on Windows (case-insensitive filesystem); corrupted wheel builds

### Problem #3: Graphviz Not Declared in Dependencies
- `pyproject.toml` dependencies: only `PyYAML>=6`
- Graphviz is a system binary, not a Python package — but this is not documented in packaging metadata
- `cli/main.py` already has hardcoded Windows path fallbacks (`C:/Program Files/Graphviz/bin/dot.exe`) — a code smell acknowledging the problem without solving it at the install level

### Problem #4: No Post-Install Verification
- No `__main__.py`, so `python -m data_pipeline_flow` does not work as a fallback
- No check that the CLI entry point was created during install
- README says "if the summary command works, installation is fine" — meaning users must manually discover whether install succeeded

### Problem #5: Fragile sys.path Manipulation in Helper Scripts
```python
# From setup_project.py
ROOT = Path(__file__).resolve().parent
SRC = ROOT / 'src'
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
```
- Assumes scripts run from repo root
- Does not check if `data_pipeline_flow` is already installed
- Breaks if scripts are moved or repo is relocated
- Not compatible with non-editable installs

---

## Proposed Solutions — Ranked by Impact

### Tier 1: Fix Now (structural bugs, zero design decisions needed)

1. **Delete `src/stata_pipeline_flow/`**
   ```bash
   git rm -r src/stata_pipeline_flow/
   git commit -m "Remove ghost stata_pipeline_flow directory (migrated in 34b86bc)"
   ```

2. **Add `src/data_pipeline_flow/__main__.py`**
   ```python
   """Allow: python -m data_pipeline_flow"""
   from data_pipeline_flow.cli.main import main
   import sys
   if __name__ == '__main__':
       sys.exit(main())
   ```
   Enables use without PATH setup: `python -m data_pipeline_flow summary ...`

---

### Tier 2: High-Value UX Improvements

3. **`install.py` — single-command setup (Agent 1 Solution 1)**
   One script that: creates venv, installs package, checks Graphviz, runs smoke test, prints next steps. User runs `python install.py` and is done. No activation, no steps to forget.

4. **Register helpers as proper console_scripts in `pyproject.toml` (Agent 2 Solution 1)**
   ```toml
   [project.scripts]
   data-pipeline-flow = "data_pipeline_flow.cli.main:main"
   data-pipeline-flow-setup = "data_pipeline_flow.cli.helpers:setup_command"
   data-pipeline-flow-make = "data_pipeline_flow.cli.helpers:make_command"
   data-pipeline-flow-inspect = "data_pipeline_flow.cli.helpers:inspect_command"
   ```
   Requires creating `src/data_pipeline_flow/cli/helpers.py` that exposes each wrapper as a proper entry point. Makes `pipx install .` work fully.

5. **`_check_install.py` — runtime Graphviz warning (Agent 2 Solution 2)**
   Check for Graphviz on first import, emit a `RuntimeWarning` if missing (not a hard error). Surfaces the problem at the right moment rather than at render time.

---

### Tier 3: Polish

6. **`install_windows.ps1`** — automates the full Windows sequence (venv create, activate, install, verify)
   ```powershell
   py -3.11 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install --upgrade pip
   pip install -e ".[dev]"
   data-pipeline-flow summary --project-root example/project
   ```

7. **Makefile** — standard targets: `make install`, `make test`, `make check-install`, `make clean`

8. **Prerequisites section at top of README** — before any code blocks, list: Python 3.10+, Graphviz (with OS-specific install commands), explain venv activation once clearly

---

## Summary Table

| Issue | Severity | Fix |
|---|---|---|
| Ghost `stata_pipeline_flow/` dir | HIGH | `git rm -r src/stata_pipeline_flow/` |
| No `__main__.py` fallback | HIGH | Add 3-line file |
| No pipx/uv support | HIGH | Register helpers as console_scripts |
| Graphviz silent at install time | HIGH | `_check_install.py` + README prereqs |
| Venv activation not explained | MEDIUM | `install.py` one-command setup |
| Two conflicting setup paths | MEDIUM | Pick one, document clearly |
| Helper scripts fragile (repo root only) | MEDIUM | Proper console_scripts fix (Tier 2 #4) |
| No post-install verification | MEDIUM | Smoke test in `install.py` |
