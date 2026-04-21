"""One-command setup for data-pipeline-flow.

Usage:
    python install.py

Creates a .venv, installs the package with dev extras, checks for Graphviz,
and runs a smoke test against the bundled example project.
"""
import shutil
import subprocess
import sys
import venv
from pathlib import Path

REPO_ROOT = Path(__file__).parent.resolve()
IS_WINDOWS = sys.platform == "win32"
VENV_DIR = REPO_ROOT / ".venv"
PIP = VENV_DIR / ("Scripts/pip.exe" if IS_WINDOWS else "bin/pip")
PYTHON = VENV_DIR / ("Scripts/python.exe" if IS_WINDOWS else "bin/python")

# Graphviz Windows search paths (mirrors _check_install.py)
_GV_CANDIDATES = [
    Path("C:/Program Files/Graphviz/bin/dot.exe"),
    Path("C:/Program Files (x86)/Graphviz/bin/dot.exe"),
]


def _graphviz_found() -> bool:
    if shutil.which("dot"):
        return True
    return any(p.exists() for p in _GV_CANDIDATES)


def _run(cmd: list, **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, **kwargs)


def main() -> None:
    # ── [1/5] Python version check ────────────────────────────────────────
    print("[1/5] Checking Python version...")
    if sys.version_info < (3, 10):
        print(
            f"  ERROR: Python 3.10+ required, got {sys.version_info.major}.{sys.version_info.minor}.\n"
            "  Download a newer Python from https://python.org/downloads/"
        )
        sys.exit(1)
    print(f"  OK: Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

    # ── [2/5] Create virtual environment ─────────────────────────────────
    print("[2/5] Setting up virtual environment...")
    if VENV_DIR.exists():
        print(f"  Skipping - .venv already exists at {VENV_DIR}")
    else:
        print(f"  Creating .venv at {VENV_DIR}...")
        venv.create(str(VENV_DIR), with_pip=True)
        print("  Done.")

    # ── [3/5] Install package ─────────────────────────────────────────────
    print("[3/5] Installing data-pipeline-flow[dev]...")
    result = _run(
        [str(PIP), "install", "-e", ".[dev]", "--quiet"],
        cwd=str(REPO_ROOT),
    )
    if result.returncode != 0:
        print("  ERROR: pip install failed (see output above).")
        sys.exit(1)
    print("  Done.")

    # ── [4/5] Graphviz check ──────────────────────────────────────────────
    print("[4/5] Checking for Graphviz...")
    if _graphviz_found():
        print("  OK: Graphviz dot binary found.")
    else:
        print(
            "  WARNING: Graphviz not found - render-image won't work until it is installed.\n"
            "  Download from https://graphviz.org/download/ and make sure 'dot' is on PATH."
        )

    # ── [5/5] Smoke test ──────────────────────────────────────────────────
    print("[5/5] Running smoke test...")
    result = _run(
        [
            str(PYTHON), "-m", "data_pipeline_flow",
            "summary", "--project-root", str(REPO_ROOT / "example" / "project"),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        print("  PASSED.")
    else:
        print("  FAILED.")
        print("  stdout:", result.stdout.strip())
        print("  stderr:", result.stderr.strip())

    # ── Next steps ────────────────────────────────────────────────────────
    if IS_WINDOWS:
        activate = r"  .venv\Scripts\Activate.ps1   (PowerShell)"
    else:
        activate = "  source .venv/bin/activate"

    separator = "-" * 45
    print(
        f"\n{separator}\n"
        "Setup complete. Next steps:\n\n"
        "  1. Activate the virtual environment:\n"
        f"{activate}\n\n"
        "  2. Run the interactive setup wizard for your project:\n"
        "     data-pipeline-flow-setup\n\n"
        "  3. Build your pipeline image:\n"
        "     data-pipeline-flow-make\n\n"
        "  4. Or call the CLI directly:\n"
        "     data-pipeline-flow summary --project-root <path/to/your/project>\n"
        f"{separator}"
    )


if __name__ == "__main__":
    main()
