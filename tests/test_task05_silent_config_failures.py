"""Tests for Task 05: Fix silent config failures.

Bug A — Unknown top-level config key silently ignored (Issue 6)
Bug B — on_missing: warn should emit a helpful warning-level diagnostic (Issue 8)
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FIXTURES = Path(__file__).parent / "fixtures"


def _load_config(path: Path):
    from data_pipeline_flow.config.schema import load_config
    return load_config(path)


def _build_graph(project_root: Path, config=None):
    from data_pipeline_flow.config.schema import AppConfig, load_config
    from data_pipeline_flow.rules.pipeline import PipelineBuilder

    if config is None:
        cfg_path = project_root / "pipeline_user_settings.yaml"
        if cfg_path.exists():
            config = load_config(cfg_path)
        else:
            config = AppConfig(project_root=str(project_root))
    config = AppConfig(
        **{
            **{f: getattr(config, f) for f in config.__dataclass_fields__},
            "project_root": str(project_root),
        }
    )
    return PipelineBuilder(config).build(project_root)


# ---------------------------------------------------------------------------
# Bug A: unknown top-level config key emits a warning
# ---------------------------------------------------------------------------

class TestUnknownKeyWarning:
    """Bug A — writing 'exclude:' instead of 'exclusions:' must emit a warning."""

    def test_unknown_key_emits_warning_to_stderr(self, capsys, tmp_path):
        """load_config should print a warning to stderr for each unknown top-level key."""
        cfg_file = tmp_path / "pipeline_user_settings.yaml"
        cfg_file.write_text(
            "exclude:\n  paths:\n    - script.py\n",
            encoding="utf-8",
        )
        _load_config(cfg_file)
        captured = capsys.readouterr()
        # The warning must go to stderr
        assert "exclude" in captured.err.lower() or "unknown" in captured.err.lower(), (
            f"Expected a warning about unknown key 'exclude' in stderr, got: {captured.err!r}"
        )

    def test_unknown_key_warning_names_the_key(self, capsys, tmp_path):
        """The warning message must name the offending key."""
        cfg_file = tmp_path / "pipeline_user_settings.yaml"
        cfg_file.write_text(
            "typo_key:\n  foo: bar\n",
            encoding="utf-8",
        )
        _load_config(cfg_file)
        captured = capsys.readouterr()
        assert "typo_key" in captured.err, (
            f"Warning should name the unknown key 'typo_key', got stderr: {captured.err!r}"
        )

    def test_known_keys_do_not_trigger_warning(self, capsys, tmp_path):
        """Valid keys like 'exclusions' and 'display' must not cause a warning."""
        cfg_file = tmp_path / "pipeline_user_settings.yaml"
        cfg_file.write_text(
            "exclusions:\n  paths:\n    - script.py\ndisplay:\n  theme: modern-light\n",
            encoding="utf-8",
        )
        _load_config(cfg_file)
        captured = capsys.readouterr()
        assert "unknown" not in captured.err.lower(), (
            f"No warning expected for valid keys, got stderr: {captured.err!r}"
        )

    def test_bad_config_key_fixture(self, capsys):
        """Smoke-test the fixture used in manual CLI verification."""
        cfg_path = FIXTURES / "bad_config_key" / "pipeline_user_settings.yaml"
        _load_config(cfg_path)
        captured = capsys.readouterr()
        assert "exclude" in captured.err.lower() or "unknown" in captured.err.lower(), (
            f"Expected warning about 'exclude' in stderr, got: {captured.err!r}"
        )


# ---------------------------------------------------------------------------
# Bug B: on_missing: warn emits a diagnostic at 'warning' severity with
#         a helpful message distinguishing "not on disk" vs "not in graph"
# ---------------------------------------------------------------------------

class TestOnMissingWarnDiagnostic:
    """Bug B — on_missing: warn must emit a warning-level diagnostic."""

    def _make_graph_with_missing_target(self):
        """Build a graph with a manual edge whose target is not in the graph."""
        from data_pipeline_flow.config.schema import (
            AppConfig,
            ManualEdgeConfig,
        )
        from data_pipeline_flow.model.entities import GraphModel, Node
        from data_pipeline_flow.rules.manual_edges import apply_manual_edges

        graph = GraphModel(project_root=".")
        # Add only the source node; the target ('artifact.parquet') is absent
        graph.add_node(Node(
            node_id="script_a.py",
            label="script_a.py",
            node_type="script",
            path=None,
            role="script",
            cluster_id=None,
            metadata={},
        ))

        config = AppConfig(
            manual_edges=[
                ManualEdgeConfig(
                    source="script_a.py",
                    target="artifact.parquet",
                    on_missing="warn",
                )
            ]
        )
        return apply_manual_edges(graph, config)

    def test_on_missing_warn_emits_warning_level(self):
        """The diagnostic for a missing node must have level='warning'."""
        graph = self._make_graph_with_missing_target()
        not_found = [
            d for d in graph.diagnostics
            if d.code == "manual_edge_node_not_found"
        ]
        assert not_found, "Expected a 'manual_edge_node_not_found' diagnostic"
        assert not_found[0].level == "warning", (
            f"Expected level='warning', got level={not_found[0].level!r}"
        )

    def test_on_missing_warn_message_mentions_parser(self):
        """The warning message should hint that the parser did not detect the node."""
        graph = self._make_graph_with_missing_target()
        not_found = [
            d for d in graph.diagnostics
            if d.code == "manual_edge_node_not_found"
        ]
        assert not_found, "Expected a 'manual_edge_node_not_found' diagnostic"
        msg = not_found[0].message.lower()
        # The improved message should mention parser or placeholder
        assert "parser" in msg or "placeholder" in msg, (
            f"Expected message to mention 'parser' or 'placeholder', got: {not_found[0].message!r}"
        )

    def test_on_missing_warn_fixture(self):
        """Smoke-test the on_missing_warn fixture end-to-end."""
        project_root = FIXTURES / "on_missing_warn"
        graph = _build_graph(project_root)
        not_found = [
            d for d in graph.diagnostics
            if d.code == "manual_edge_node_not_found"
        ]
        assert not_found, "Expected manual_edge_node_not_found diagnostic from fixture"
        assert not_found[0].level == "warning"
