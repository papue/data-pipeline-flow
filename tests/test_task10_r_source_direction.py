"""
Task 10 — R source() edge direction.

R's source() executes a helper script in the calling environment, making
functions/objects from the helper available to the caller.  This is analogous
to Python import: the helper *feeds into* the caller, so the data-flow edge
should point  helper.R → main.R  (not main.R → helper.R).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from data_pipeline_flow.model.entities import GraphModel
from data_pipeline_flow.parser.multi_extract import build_graph_from_scripts
from data_pipeline_flow.config.schema import (
    ClassificationConfig,
    DisplayConfig,
    ExclusionConfig,
    NormalizationConfig,
    ParserConfig,
)


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "r_source_direction"


def _build_graph() -> GraphModel:
    return build_graph_from_scripts(
        project_root=FIXTURE_ROOT,
        script_files=["main.r", "helper.r"],
        exclusions=ExclusionConfig(),
        parser_config=ParserConfig(),
        normalization=NormalizationConfig(),
        classification_config=ClassificationConfig(),
        display_config=DisplayConfig(),
    )


def _source_edges(graph: GraphModel):
    """Return all script_call edges from the graph."""
    return [e for e in graph.edges if e.kind == "script_call"]


def test_r_source_edge_source_is_helper():
    """The source of the script_call edge must be helper.r (the module that feeds in)."""
    graph = _build_graph()
    edges = _source_edges(graph)
    assert edges, "Expected at least one script_call edge"
    assert any(
        e.source == "helper.r" for e in edges
    ), f"Expected helper.r as edge source, got: {[(e.source, e.target) for e in edges]}"


def test_r_source_edge_target_is_main():
    """The target of the script_call edge must be main.r (the caller that consumes the helper)."""
    graph = _build_graph()
    edges = _source_edges(graph)
    assert edges, "Expected at least one script_call edge"
    assert any(
        e.target == "main.r" for e in edges
    ), f"Expected main.r as edge target, got: {[(e.source, e.target) for e in edges]}"


def test_r_source_direction_not_reversed():
    """There must be no edge going main.r → helper.r (wrong caller→callee direction)."""
    graph = _build_graph()
    wrong_edges = [
        e for e in _source_edges(graph)
        if e.source == "main.r" and e.target == "helper.r"
    ]
    assert not wrong_edges, (
        f"Found wrong-direction edge(s) main.r → helper.r: {wrong_edges}"
    )
