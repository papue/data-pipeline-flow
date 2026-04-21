"""Console-script entry points for the interactive wizard commands.

These are registered as ``[project.scripts]`` in ``pyproject.toml`` so that
after ``pip install`` (or ``pipx install``) the commands are available on PATH
from any working directory.

Each function passes ``Path.cwd()`` as the ``repo_root`` argument so that
settings files (``pipeline_user_settings.yaml``) and relative config paths are
resolved against the directory where the user invokes the command — which is
the correct behaviour when the package is installed outside the repo tree.
"""

from __future__ import annotations

import sys
from pathlib import Path


def setup_command() -> None:
    """data-pipeline-flow-setup: Interactive first-run setup wizard."""
    from data_pipeline_flow.wizard import setup_interactive

    sys.exit(setup_interactive(Path.cwd()))


def make_command() -> None:
    """data-pipeline-flow-make: Interactive pipeline render."""
    from data_pipeline_flow.wizard import render_interactive

    sys.exit(render_interactive(Path.cwd()))


def inspect_command() -> None:
    """data-pipeline-flow-inspect: Interactive graph inspection (summary / validate)."""
    from data_pipeline_flow.wizard import inspect_interactive

    sys.exit(inspect_interactive(Path.cwd()))


def edit_exclusions_command() -> None:
    """data-pipeline-flow-edit-exclusions: Interactive exclusion editor."""
    from data_pipeline_flow.wizard import edit_exclusions_interactive

    sys.exit(edit_exclusions_interactive(Path.cwd()))


def manage_clusters_command() -> None:
    """data-pipeline-flow-manage-clusters: Interactive cluster editor."""
    from data_pipeline_flow.wizard import manage_clusters_interactive

    sys.exit(manage_clusters_interactive(Path.cwd()))
