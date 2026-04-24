"""
Task 03: Absolute-path base variable — partial edge resolution.

When a script assigns an absolute path to a variable and uses it in
``os.path.join(BASE, "literal.ext")``, the parser should:
  - still emit an edge whose path contains the literal filename component
  - flag the event as was_absolute=True so the absolute_path_usage diagnostic fires
"""
from __future__ import annotations

from pathlib import Path

import pytest

from data_pipeline_flow.config.schema import AppConfig
from data_pipeline_flow.parser.python_extract import parse_python_file

FIXTURES = Path(__file__).parent / "fixtures" / "abs_path"


def _parse(filename: str):
    cfg = AppConfig()
    return parse_python_file(
        project_root=FIXTURES,
        py_file=FIXTURES / filename,
        exclusions=cfg.exclusions,
        normalization=cfg.normalization,
        parser_config=cfg.parser,
    )


def test_abs_path_writer_emits_edge():
    """writer.py uses os.path.join(BASE, 'output.parquet') where BASE is an
    absolute Windows path.  A write edge whose target contains 'output.parquet'
    must be emitted (partial resolution)."""
    result = _parse("writer.py")
    write_paths = [
        norm
        for ev in result.events
        for norm in ev.normalized_paths
        if ev.command in (
            "to_parquet", "to_csv", "to_excel", "to_json", "to_feather",
            "to_hdf", "to_pickle", "to_orc", "to_stata", "to_file",
            "savefig", "open_write", "pickle_dump", "json_dump",
            "joblib_dump", "save_method",
        )
    ]
    assert any("output.parquet" in p for p in write_paths), (
        f"Expected write edge containing 'output.parquet', got events: {result.events}"
    )


def test_abs_path_writer_flagged_as_absolute():
    """writer.py write event must have was_absolute=True so the
    absolute_path_usage diagnostic can fire downstream."""
    result = _parse("writer.py")
    abs_write_events = [
        ev for ev in result.events
        if ev.was_absolute and ev.command in (
            "to_parquet", "to_csv", "to_excel", "to_json", "to_feather",
            "to_hdf", "to_pickle", "to_orc", "to_stata", "to_file",
            "savefig", "open_write", "pickle_dump", "json_dump",
            "joblib_dump", "save_method",
        )
    ]
    assert abs_write_events, (
        f"Expected at least one write event with was_absolute=True, got: {result.events}"
    )


def test_abs_path_reader_emits_edge():
    """reader.py uses os.path.join(BASE, 'output.parquet') where BASE is an
    absolute Windows path.  A read edge whose source contains 'output.parquet'
    must be emitted (partial resolution)."""
    result = _parse("reader.py")
    read_paths = [
        norm
        for ev in result.events
        for norm in ev.normalized_paths
        if ev.command in (
            "read_parquet", "read_csv", "read_excel", "read_json",
            "read_stata", "read_feather", "read_table", "read_hdf",
            "read_pickle", "read_orc", "open_read", "pickle_load",
            "json_load", "yaml_safe_load", "joblib_load",
        )
    ]
    assert any("output.parquet" in p for p in read_paths), (
        f"Expected read edge containing 'output.parquet', got events: {result.events}"
    )


def test_abs_path_reader_flagged_as_absolute():
    """reader.py read event must have was_absolute=True so the
    absolute_path_usage diagnostic can fire downstream."""
    result = _parse("reader.py")
    abs_read_events = [
        ev for ev in result.events
        if ev.was_absolute and ev.command in (
            "read_parquet", "read_csv", "read_excel", "read_json",
            "read_stata", "read_feather", "read_table", "read_hdf",
            "read_pickle", "read_orc", "open_read", "pickle_load",
            "json_load", "yaml_safe_load", "joblib_load",
        )
    ]
    assert abs_read_events, (
        f"Expected at least one read event with was_absolute=True, got: {result.events}"
    )
