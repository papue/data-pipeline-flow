"""
Task 04: Graphviz Windows PATH fallback + graphviz_dot_path config.

When ``shutil.which("dot")`` returns None the resolver must:
  1. Probe known Windows install paths for dot.exe.
  2. Return the full path when a probe succeeds.
  3. Honour ``config.graphviz_dot_path`` when it is explicitly set.
  4. Raise a clear RuntimeError when nothing is found.
"""
from __future__ import annotations

from unittest.mock import patch

import pytest

from data_pipeline_flow.config.schema import AppConfig
from data_pipeline_flow.render.dot import resolve_dot_executable

_WIN_PATH = r"C:\Program Files\Graphviz\bin\dot.exe"
_WIN_PATH_X86 = r"C:\Program Files (x86)\Graphviz\bin\dot.exe"


# ---------------------------------------------------------------------------
# Helper — make os.path.isfile return True only for a specific path
# ---------------------------------------------------------------------------
def _isfile_for(real_path: str):
    def _check(p):
        # normalise separators for comparison
        return str(p).replace("/", "\\") == real_path
    return _check


# ---------------------------------------------------------------------------
# 1. Falls back to Windows probe path when dot not on PATH
# ---------------------------------------------------------------------------
def test_windows_fallback_found():
    """When which('dot') is None but the primary Windows path exists, return it."""
    with (
        patch("shutil.which", return_value=None),
        patch("os.path.isfile", side_effect=_isfile_for(_WIN_PATH)),
    ):
        result = resolve_dot_executable()
    assert result == _WIN_PATH, f"Expected {_WIN_PATH!r}, got {result!r}"


def test_windows_fallback_x86_found():
    """When primary path is missing but x86 path exists, return the x86 path."""
    def _isfile(p):
        return str(p).replace("/", "\\") == _WIN_PATH_X86

    with (
        patch("shutil.which", return_value=None),
        patch("os.path.isfile", side_effect=_isfile),
    ):
        result = resolve_dot_executable()
    assert result == _WIN_PATH_X86, f"Expected {_WIN_PATH_X86!r}, got {result!r}"


# ---------------------------------------------------------------------------
# 2. config.graphviz_dot_path takes priority
# ---------------------------------------------------------------------------
def test_config_path_takes_priority():
    """config.graphviz_dot_path is returned without any probe when it is set."""
    custom_path = r"D:\tools\graphviz\dot.exe"
    config = AppConfig(graphviz_dot_path=custom_path)
    # shutil.which should NOT be called at all (or irrelevant either way)
    with patch("shutil.which", return_value=None):
        result = resolve_dot_executable(config)
    assert result == custom_path


# ---------------------------------------------------------------------------
# 3. shutil.which result is used when PATH is set
# ---------------------------------------------------------------------------
def test_which_result_used_when_on_path():
    """When shutil.which finds dot, that path is returned directly."""
    with patch("shutil.which", return_value="/usr/bin/dot"):
        result = resolve_dot_executable()
    assert result == "/usr/bin/dot"


# ---------------------------------------------------------------------------
# 4. Clear RuntimeError when nothing is found
# ---------------------------------------------------------------------------
def test_raises_when_not_found():
    """resolve_dot_executable raises RuntimeError when dot cannot be located."""
    with (
        patch("shutil.which", return_value=None),
        patch("os.path.isfile", return_value=False),
        pytest.raises(RuntimeError, match="[Gg]raphviz"),
    ):
        resolve_dot_executable()


# ---------------------------------------------------------------------------
# 5. AppConfig has graphviz_dot_path field defaulting to None
# ---------------------------------------------------------------------------
def test_appconfig_has_graphviz_dot_path_field():
    """AppConfig must expose graphviz_dot_path (default None)."""
    cfg = AppConfig()
    assert hasattr(cfg, "graphviz_dot_path"), "AppConfig missing graphviz_dot_path"
    assert cfg.graphviz_dot_path is None
