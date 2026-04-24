"""
Task 02: Python dynamic path resolution.

Tests that os.path.join() paths are correctly extracted even when:
  - The base directory comes from a module-level string variable
  - The result is assigned to another variable before being passed to read/write
"""
from __future__ import annotations

from pathlib import Path

import pytest

from data_pipeline_flow.config.schema import AppConfig
from data_pipeline_flow.parser.python_extract import parse_python_file

FIXTURES = Path(__file__).parent / "fixtures" / "dynamic_paths"

def _parse(filename: str):
    cfg = AppConfig()
    result = parse_python_file(
        project_root=FIXTURES,
        py_file=FIXTURES / filename,
        exclusions=cfg.exclusions,
        normalization=cfg.normalization,
        parser_config=cfg.parser,
    )
    return result


def test_script_a_write_edge():
    """script_a.py: df.to_parquet(path) where path=os.path.join(base,"output.parquet")
    and base="./results" should yield a write edge to results/output.parquet."""
    result = _parse("script_a.py")
    write_paths = [
        norm
        for ev in result.events
        for norm in ev.normalized_paths
        if ev.command in ("to_parquet", "to_csv", "to_excel", "to_json",
                          "to_feather", "to_hdf", "to_pickle", "to_orc",
                          "to_stata", "to_file", "savefig", "open_write",
                          "pickle_dump", "json_dump", "joblib_dump", "save_method")
    ]
    assert any("output.parquet" in p for p in write_paths), (
        f"Expected write edge containing 'output.parquet', got events: {result.events}"
    )


def test_fstring_writer_placeholder():
    """fstring_writer.py: open(f"./results/{parameter}/result_{seed}.pkl", "wb")
    should emit a placeholder write edge like results/*/result_*.pkl."""
    result = _parse("fstring_writer.py")
    fstring_events = [ev for ev in result.events if ev.command == 'fstring_path']
    assert fstring_events, (
        f"Expected at least one fstring_path event, got events: {result.events}"
    )
    # The placeholder should contain ".pkl" somewhere
    assert any(
        ".pkl" in norm
        for ev in fstring_events
        for norm in ev.normalized_paths
    ), f"Expected placeholder path with .pkl extension, got: {fstring_events}"


def test_consumer_read_edge():
    """consumer.py: pd.read_parquet(os.path.join(base,"data.parquet"))
    where base="./results" should yield a read edge from results/data.parquet."""
    result = _parse("consumer.py")
    read_paths = [
        norm
        for ev in result.events
        for norm in ev.normalized_paths
        if ev.command in ("read_parquet", "read_csv", "read_excel", "read_json",
                          "read_stata", "read_feather", "read_table", "read_hdf",
                          "read_pickle", "read_orc", "open_read", "pickle_load",
                          "json_load", "yaml_safe_load", "joblib_load")
    ]
    assert any("data.parquet" in p for p in read_paths), (
        f"Expected read edge containing 'data.parquet', got events: {result.events}"
    )
