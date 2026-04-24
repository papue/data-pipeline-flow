"""
Task 09: R dynamic path resolution — file.path, paste0, here::here.

Tests that R path helper calls are correctly resolved even when:
  - The base directory comes from a variable: base_dir <- "./results"
  - The path is built with file.path(base_dir, "output.csv")
  - The path uses here::here("data", "raw.csv")
  - The path uses here() for a write target
"""
from __future__ import annotations

from pathlib import Path

import pytest

from data_pipeline_flow.config.schema import AppConfig
from data_pipeline_flow.parser.r_extract import parse_r_file

FIXTURES = Path(__file__).parent / "fixtures" / "r_dynamic_paths"

_WRITE_COMMANDS = {
    'write_csv', 'write_csv2', 'write_table', 'saveRDS',
    'write_csv_readr', 'write_csv2_readr', 'write_tsv', 'write_delim', 'write_rds',
    'write_xlsx', 'fwrite',
    'write_dta', 'write_sav', 'write_sas',
    'write_parquet', 'write_feather',
    'saveRDS_kw', 'save_rdata',
    'ggsave', 'ggsave_kw',
    'pdf', 'png', 'svg', 'jpeg', 'tiff',
    'write_json', 'toJSON_write',
    'st_write', 'st_write_ns', 'tmap_save', 'tmap_save_kw',
    'saveWidget', 'saveWidget_kw', 'writeLines', 'writeLines_kw',
    'write.xlsx', 'saveWorkbook', 'write.fst',
}

_READ_COMMANDS = {
    'read_csv', 'read_csv2', 'read_table', 'read_delim', 'readRDS', 'load',
    'read_csv_readr', 'read_csv2_readr', 'read_delim_readr', 'read_rds', 'read_tsv',
    'read_excel', 'read_xls', 'read_xlsx',
    'read_dta', 'read_sas', 'read_spss', 'read_sav',
    'fread', 'read_parquet', 'read_feather', 'fromJSON',
    'st_read', 'st_read_ns', 'read_html',
    'read.xlsx', 'loadWorkbook', 'read.fst', 'read_fst',
}


def _parse(filename: str):
    cfg = AppConfig()
    return parse_r_file(
        project_root=FIXTURES,
        r_file=FIXTURES / filename,
        exclusions=cfg.exclusions,
        normalization=cfg.normalization,
        parser_config=cfg.parser,
    )


def _write_paths(result) -> list[str]:
    return [
        norm
        for ev in result.events
        for norm in ev.normalized_paths
        if ev.command in _WRITE_COMMANDS
    ]


def _read_paths(result) -> list[str]:
    return [
        norm
        for ev in result.events
        for norm in ev.normalized_paths
        if ev.command in _READ_COMMANDS
    ]


def test_file_path_write_edge():
    """writer.R: write.csv(df, file.path(base_dir, "output.csv"))
    where base_dir <- "./results" should yield a write edge to results/output.csv."""
    result = _parse("writer.R")
    paths = _write_paths(result)
    assert any("output.csv" in p and "results" in p for p in paths), (
        f"Expected write edge to results/output.csv via file.path resolution, "
        f"got events: {result.events}"
    )


def test_file_path_read_edge():
    """reader.R: read.csv(file.path(base_dir, "output.csv"))
    where base_dir <- "./results" should yield a read edge from results/output.csv."""
    result = _parse("reader.R")
    paths = _read_paths(result)
    assert any("output.csv" in p and "results" in p for p in paths), (
        f"Expected read edge from results/output.csv via file.path resolution, "
        f"got events: {result.events}"
    )


def test_here_read_edge():
    """analysis.R: read.csv(here("data", "raw.csv"))
    should yield a read edge from data/raw.csv."""
    result = _parse("analysis.R")
    paths = _read_paths(result)
    assert any("raw.csv" in p and "data" in p for p in paths), (
        f"Expected read edge from data/raw.csv via here() resolution, "
        f"got events: {result.events}"
    )


def test_here_write_edge():
    """analysis.R: saveRDS(model, here("results", "model.rds"))
    should yield a write edge to results/model.rds."""
    result = _parse("analysis.R")
    paths = _write_paths(result)
    assert any("model.rds" in p and "results" in p for p in paths), (
        f"Expected write edge to results/model.rds via here() resolution, "
        f"got events: {result.events}"
    )
