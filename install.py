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

# Settings file where the resolved dot path is persisted.
_SETTINGS_FILE = REPO_ROOT / "pipeline_user_settings.yaml"


def _find_graphviz() -> tuple[str | None, bool]:
    """Return ``(dot_path, via_probe)`` or ``(None, False)`` if not found.

    ``via_probe`` is True when the path was found via a known Windows location
    rather than via PATH, so the caller can decide whether to persist it.
    """
    on_path = shutil.which("dot")
    if on_path:
        return on_path, False
    for candidate in _GV_CANDIDATES:
        if candidate.exists():
            return str(candidate), True
    return None, False


def _persist_dot_path(dot_path: str) -> None:
    """Write ``graphviz_dot_path`` into pipeline_user_settings.yaml."""
    # Read existing content (if any) to avoid clobbering other settings.
    lines: list[str] = []
    if _SETTINGS_FILE.exists():
        lines = _SETTINGS_FILE.read_text(encoding="utf-8").splitlines()

    # Remove any existing graphviz_dot_path line.
    lines = [ln for ln in lines if not ln.strip().startswith("graphviz_dot_path:")]

    # Append the new value.
    # Use forward slashes so the YAML is portable.
    lines.append(f"graphviz_dot_path: {dot_path.replace(chr(92), '/')}")

    _SETTINGS_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _graphviz_found() -> bool:
    dot_path, _ = _find_graphviz()
    return dot_path is not None


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
    dot_path, via_probe = _find_graphviz()
    if dot_path:
        if via_probe:
            print(f"  dot not on PATH but found at {dot_path} — using full path.")
            _persist_dot_path(dot_path)
            print(f"  Persisted graphviz_dot_path to {_SETTINGS_FILE.name}.")
        else:
            print("  OK: Graphviz dot binary found on PATH.")
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
