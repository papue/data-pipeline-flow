"""
Task 07: Stata global/local macro expansion in file paths.

Tests that $MACRO, ${MACRO}, and `local' macro references inside use/save/do
commands are correctly expanded to their literal values so that edges are
emitted to the right normalized paths.

Fixture layout
--------------
tests/fixtures/stata_macros/
    main.do          – global macro + use/save
    local_macro.do   – local macro + save
    curly.do         – ${MACRONAME} curly-brace syntax
    unquoted.do      – unquoted paths (no surrounding quotes)
    results/
        input.dta    – exists on disk (so use-edge is not filtered as orphan)
        final/       – empty directory for local macro fixture
"""
from __future__ import annotations

from pathlib import Path

import pytest

from data_pipeline_flow.config.schema import (
    AppConfig,
    ClassificationConfig,
    DisplayConfig,
    ExclusionConfig,
    NormalizationConfig,
    ParserConfig,
)
from data_pipeline_flow.parser.stata_extract import parse_do_file

FIXTURES = Path(__file__).parent / "fixtures" / "stata_macros"


def _parse(filename: str):
    """Parse a single fixture .do file and return the ScriptParseResult."""
    cfg = AppConfig()
    return parse_do_file(
        project_root=FIXTURES,
        do_file=FIXTURES / filename,
        exclusions=cfg.exclusions,
        normalization=cfg.normalization,
        parser_config=cfg.parser,
    )


def _read_paths(result) -> list[str]:
    """Collect all normalized paths from read-command events."""
    READ_CMDS = {"use", "import", "append", "merge", "cross"}
    return [
        norm
        for ev in result.events
        for norm in ev.normalized_paths
        if ev.command in READ_CMDS
    ]


def _write_paths(result) -> list[str]:
    """Collect all normalized paths from write-command events."""
    WRITE_CMDS = {"save", "export_delimited", "export_excel", "graph_export", "estimates_save"}
    return [
        norm
        for ev in result.events
        for norm in ev.normalized_paths
        if ev.command in WRITE_CMDS
    ]


# ---------------------------------------------------------------------------
# Required tests (Step 3)
# ---------------------------------------------------------------------------

def test_global_macro_use_edge():
    """main.do: use "$DATAPATH/input.dta" — global $MACRO must be expanded.

    The extracted edge should be results/input.dta → main.do (a read event
    whose normalized path is results/input.dta).
    """
    result = _parse("main.do")
    paths = _read_paths(result)
    assert any("input.dta" in p for p in paths), (
        f"Expected read edge containing 'input.dta' after $DATAPATH expansion, "
        f"got read paths: {paths!r}\nAll events: {result.events}"
    )
    assert any(p == "results/input.dta" for p in paths), (
        f"Expected normalized path 'results/input.dta', got: {paths!r}"
    )


def test_global_macro_save_edge():
    """main.do: save "$DATAPATH/output.dta" — global $MACRO must be expanded.

    The write event must produce normalized path results/output.dta
    (even if the edge is later suppressed by suppress_internal_only_writes;
    the raw parse result should contain the event).
    """
    result = _parse("main.do")
    paths = _write_paths(result)
    assert any("output.dta" in p for p in paths), (
        f"Expected write event containing 'output.dta' after $DATAPATH expansion, "
        f"got write paths: {paths!r}\nAll events: {result.events}"
    )
    assert any(p == "results/output.dta" for p in paths), (
        f"Expected normalized path 'results/output.dta', got: {paths!r}"
    )


def test_local_macro_save_edge():
    """local_macro.do: local outdir "results/final" + save "`outdir'/table1.dta"

    The backtick-quote local macro must be substituted so the write path
    resolves to results/final/table1.dta.
    """
    result = _parse("local_macro.do")
    paths = _write_paths(result)
    assert any("table1.dta" in p for p in paths), (
        f"Expected write event containing 'table1.dta' after `outdir' expansion, "
        f"got write paths: {paths!r}\nAll events: {result.events}"
    )
    assert any(p == "results/final/table1.dta" for p in paths), (
        f"Expected normalized path 'results/final/table1.dta', got: {paths!r}"
    )


# ---------------------------------------------------------------------------
# Additional tests for curly-brace and unquoted path bugs
# ---------------------------------------------------------------------------

def test_curly_brace_macro_use_edge():
    """curly.do: use "${DATAPATH}/input.dta" — ${MACRO} curly-brace form must expand.

    This is a distinct Stata syntax variant from $MACRO.  Both must work.
    """
    result = _parse("curly.do")
    paths = _read_paths(result)
    assert any(p == "results/input.dta" for p in paths), (
        f"Expected normalized path 'results/input.dta' from ${{DATAPATH}} expansion, "
        f"got read paths: {paths!r}\nAll events: {result.events}"
    )


def test_unquoted_global_macro_use_edge():
    """unquoted.do: use $DATAPATH/input.dta (no surrounding quotes).

    Stata allows unquoted paths when the path contains no spaces.
    The parser should still extract the path and expand the macro.
    """
    result = _parse("unquoted.do")
    paths = _read_paths(result)
    assert any(p == "results/input.dta" for p in paths), (
        f"Expected normalized path 'results/input.dta' from unquoted macro path, "
        f"got read paths: {paths!r}\nAll events: {result.events}"
    )


def test_unquoted_global_macro_save_edge():
    """unquoted.do: save $DATAPATH/output.dta (no surrounding quotes).

    Stata allows unquoted save paths; the parser should extract and expand.
    """
    result = _parse("unquoted.do")
    paths = _write_paths(result)
    assert any(p == "results/output.dta" for p in paths), (
        f"Expected normalized path 'results/output.dta' from unquoted macro path, "
        f"got write paths: {paths!r}\nAll events: {result.events}"
    )
