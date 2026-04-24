"""
Task 08: Stata do/run edge direction.

When master.do contains `do 01_clean.do` and `do 02_analyze.do`, the
data-flow edges should be:

    master.do -> 01_clean.do   (caller → callee)
    master.do -> 02_analyze.do (caller → callee)

This is CORRECT and intentional. Unlike Python `import` (where the module
feeds data *into* the importer, so the edge is reversed to helper → caller),
Stata `do` is sequential execution orchestration: the master script drives
callee scripts in order. There is no "return value" and no data flowing back
into master. The caller → callee direction naturally represents pipeline
execution order and is the expected direction for a pipeline DAG visualizer.

Reversing to callee → master would falsely imply that clean/analyze feed data
*into* master, which is semantically wrong for Stata do-file pipelines.

Decision: CORRECT — no change needed. This test locks in the current behavior
as a regression test.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from data_pipeline_flow.parser.multi_extract import build_graph_from_scripts
from data_pipeline_flow.config.schema import (
    ClassificationConfig,
    DisplayConfig,
    ExclusionConfig,
    NormalizationConfig,
    ParserConfig,
)

FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "stata_do_direction"


def _build_fixture_graph():
    script_files = ["master.do", "01_clean.do", "02_analyze.do"]
    return build_graph_from_scripts(
        project_root=FIXTURE_ROOT,
        script_files=script_files,
        exclusions=ExclusionConfig(),
        parser_config=ParserConfig(),
        normalization=NormalizationConfig(),
        classification_config=ClassificationConfig(),
        display_config=DisplayConfig(),
    )


def test_stata_do_produces_two_script_call_edges():
    """master.do calling two scripts yields exactly two script_call edges."""
    graph = _build_fixture_graph()
    script_call_edges = [e for e in graph.edges if e.kind == "script_call"]
    assert len(script_call_edges) == 2, (
        f"Expected 2 script_call edges, got {len(script_call_edges)}: "
        + str([(e.source, e.target) for e in script_call_edges])
    )


def test_stata_do_edge_source_is_master():
    """Both script_call edges must originate from master.do (caller → callee direction)."""
    graph = _build_fixture_graph()
    script_call_edges = [e for e in graph.edges if e.kind == "script_call"]
    for edge in script_call_edges:
        assert edge.source == "master.do", (
            f"Expected source='master.do', got source='{edge.source}' "
            f"target='{edge.target}'. "
            "Stata `do` edge direction should be caller → callee, "
            "not callee → caller."
        )


def test_stata_do_edge_targets_are_child_scripts():
    """The callee scripts are the edge targets."""
    graph = _build_fixture_graph()
    script_call_edges = [e for e in graph.edges if e.kind == "script_call"]
    targets = {e.target for e in script_call_edges}
    assert targets == {"01_clean.do", "02_analyze.do"}, (
        f"Expected targets={{'01_clean.do', '02_analyze.do'}}, got {targets}"
    )


def test_stata_do_edge_operation_is_do():
    """Edge operation must be 'do' (not 'import' or 'source')."""
    graph = _build_fixture_graph()
    script_call_edges = [e for e in graph.edges if e.kind == "script_call"]
    for edge in script_call_edges:
        assert edge.operation == "do", (
            f"Expected operation='do', got '{edge.operation}' "
            f"for edge {edge.source} → {edge.target}"
        )


def test_stata_do_direction_not_reversed():
    """
    Regression: Stata do edges must NOT be reversed the way Python import edges are.

    Python import: child → parent  (data flows into importer)
    Stata do:      parent → child  (master drives callee)

    This test explicitly asserts that no callee-to-master edge exists.
    """
    graph = _build_fixture_graph()
    reversed_edges = [
        e for e in graph.edges
        if e.kind == "script_call" and e.target == "master.do"
    ]
    assert reversed_edges == [], (
        f"Found unexpected reversed edge(s) pointing back to master.do: "
        + str([(e.source, e.target) for e in reversed_edges])
        + ". Stata `do` edges should NOT be reversed (unlike Python import)."
    )
