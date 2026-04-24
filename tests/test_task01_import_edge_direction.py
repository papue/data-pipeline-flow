"""
Task 01: Python import edge direction.

When main_script.py does `from helper import compute`, the data-flow edge
should be helper.py → main_script.py (helper feeds into caller),
NOT main_script.py → helper.py.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from data_pipeline_flow.parser.multi_extract import build_graph_from_scripts
from data_pipeline_flow.config.schema import (
    ExclusionConfig,
    NormalizationConfig,
    ParserConfig,
    ClassificationConfig,
    DisplayConfig,
)

FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "import_direction"


def _build_fixture_graph():
    """Run the full multi-language graph builder on the fixture project."""
    script_files = ["main_script.py", "helper.py"]
    return build_graph_from_scripts(
        project_root=FIXTURE_ROOT,
        script_files=script_files,
        exclusions=ExclusionConfig(),
        parser_config=ParserConfig(),
        normalization=NormalizationConfig(),
        classification_config=ClassificationConfig(),
        display_config=DisplayConfig(),
    )


def test_import_edge_direction_source_is_helper():
    """Edge source must be helper.py (the imported module)."""
    graph = _build_fixture_graph()
    script_call_edges = [
        e for e in graph.edges if e.kind == "script_call"
    ]
    assert script_call_edges, "Expected at least one script_call edge"
    edge = script_call_edges[0]
    assert edge.source == "helper.py", (
        f"Expected source='helper.py', got source='{edge.source}' "
        f"target='{edge.target}'. "
        "Import edge direction is wrong: it should be helper → main_script, "
        "not main_script → helper."
    )


def test_import_edge_direction_target_is_main_script():
    """Edge target must be main_script.py (the importing script)."""
    graph = _build_fixture_graph()
    script_call_edges = [
        e for e in graph.edges if e.kind == "script_call"
    ]
    assert script_call_edges, "Expected at least one script_call edge"
    edge = script_call_edges[0]
    assert edge.target == "main_script.py", (
        f"Expected target='main_script.py', got source='{edge.source}' "
        f"target='{edge.target}'. "
        "Import edge direction is wrong: it should be helper → main_script, "
        "not main_script → helper."
    )
