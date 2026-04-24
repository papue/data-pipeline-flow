from __future__ import annotations

import re
from pathlib import Path

from data_pipeline_flow.config.schema import ExclusionConfig, NormalizationConfig, ParserConfig
from data_pipeline_flow.model.normalize import normalize_token, to_project_relative
from data_pipeline_flow.rules.exclusions import is_excluded
from data_pipeline_flow.parser.stata_extract import (
    Diagnostic,
    ParsedEvent,
    ScriptParseResult,
    _excluded_reference,
)

# ---------------------------------------------------------------------------
# Comment stripping
# ---------------------------------------------------------------------------
_COMMENT_RE = re.compile(r'#.*$')

# ---------------------------------------------------------------------------
# External reference filter
# ---------------------------------------------------------------------------
_EXTERNAL_PREFIXES = ('http://', 'https://', 'ftp://', 's3://', 'gs://')

# ---------------------------------------------------------------------------
# Variable assignment:  name <- "value"  or  name = "value"
# ---------------------------------------------------------------------------
_VAR_ASSIGN_RE = re.compile(
    r'^\s*(\w+)\s*(?:<-|=)\s*(?:"([^"\\]*)"|\'([^\'\\]*)\')\s*$'
)

# ---------------------------------------------------------------------------
# Script-relative directory idioms (R's __file__ equivalents)
# Matches:  var <- dirname(sys.frame(1)$ofile)
#           var <- dirname(getSrcFilename(...))
#           var <- dirname(rstudioapi::getActiveDocumentContext()$path)
#           var <- tryCatch(dirname(sys.frame(1)$ofile), ...)  — first branch
# ---------------------------------------------------------------------------
_SCRIPT_DIR_RE = re.compile(
    r'^\s*(\w+)\s*(?:<-|=)\s*'
    r'(?:tryCatch\s*\(\s*)?'  # optional tryCatch(
    r'dirname\s*\('
    r'(?:'
    r'sys\.frame\s*\([^)]*\)\s*\$ofile'
    r'|getSrcFilename\s*\([^)]*\)'
    r'|rstudioapi::getActiveDocumentContext\s*\(\s*\)\s*\$path'
    r')',
    re.I,
)

# getSrcFilename assigned directly (two-step: script_path <- getSrcFilename(...); script_dir <- dirname(script_path))
_GETSRCFILENAME_RE = re.compile(
    r'^\s*(\w+)\s*(?:<-|=)\s*getSrcFilename\s*\(',
    re.I,
)

# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------
# here("a", "b", "c")  or  here::here("a", "b")
_HERE_RE = re.compile(r'\bhere(?:::here)?\s*\(([^)]+)\)', re.I)
# file.path("a", var, "c")
_FILEPATH_RE = re.compile(r'\bfile\.path\s*\(([^)]+)\)', re.I)
# paste0("a", var, "b")
_PASTE0_RE = re.compile(r'\bpaste0\s*\(([^)]+)\)', re.I)
# sprintf("template/%s/file.csv", arg1, arg2, ...)  — one or more placeholders
_SPRINTF_RE = re.compile(r'\bsprintf\s*\(\s*(?:"([^"]+)"|\'([^\']+)\')\s*,\s*(.+)\)\s*$', re.I)

# ---------------------------------------------------------------------------
# Quoted string extraction
# ---------------------------------------------------------------------------
_QUOTED_RE = re.compile(r'(?:"([^"\\]+)"|\'([^\'\\]+)\')')

# ---------------------------------------------------------------------------
# READ patterns: (command_label, regex)
# Groups 1 and 2 capture alternative double/single quoted path.
# ---------------------------------------------------------------------------
# For functions where the path is the FIRST positional arg
_READS_FIRST_ARG: list[tuple[str, re.Pattern[str]]] = [
    # base R
    ('read_csv',   re.compile(r'\bread\.csv\s*\(\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
    ('read_csv2',  re.compile(r'\bread\.csv2\s*\(\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
    ('read_table', re.compile(r'\bread\.table\s*\(\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
    ('read_delim', re.compile(r'\bread\.delim\s*\(\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
    ('readRDS',    re.compile(r'\breadRDS\s*\(\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
    ('load',       re.compile(r'\bload\s*\(\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
    # readr (qualified and unqualified)
    ('read_csv_readr',   re.compile(r'\bread_csv\s*\(\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
    ('read_csv2_readr',  re.compile(r'\bread_csv2\s*\(\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
    ('read_delim_readr', re.compile(r'\bread_delim\s*\(\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
    ('read_rds',         re.compile(r'\bread_rds\s*\(\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
    ('read_tsv',         re.compile(r'\bread_tsv\s*\(\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
    # readxl
    ('read_excel', re.compile(r'\bread_excel\s*\(\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
    ('read_xls',   re.compile(r'\bread_xls\s*\(\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
    ('read_xlsx',  re.compile(r'\bread_xlsx\s*\(\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
    # haven
    ('read_dta',  re.compile(r'\bread_dta\s*\(\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
    ('read_sas',  re.compile(r'\bread_sas\s*\(\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
    ('read_spss', re.compile(r'\bread_spss\s*\(\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
    ('read_sav',  re.compile(r'\bread_sav\s*\(\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
    # data.table
    ('fread', re.compile(r'\bfread\s*\(\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
    # arrow / feather
    ('read_parquet', re.compile(r'\bread_parquet\s*\(\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
    ('read_feather', re.compile(r'\bread_feather\s*\(\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
    # jsonlite
    ('fromJSON', re.compile(r'\bfromJSON\s*\(\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
    # sf (spatial)
    ('st_read',    re.compile(r'\bst_read\s*\(\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
    ('st_read_ns', re.compile(r'\bsf::st_read\s*\(\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
    # rvest
    ('read_html', re.compile(r'\bread_html\s*\(\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
    # openxlsx
    ('read.xlsx',    re.compile(r'\bread\.xlsx\s*\(\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
    ('loadWorkbook', re.compile(r'\bloadWorkbook\s*\(\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
    # fst
    ('read.fst', re.compile(r'\bread\.fst\s*\(\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
    ('read_fst', re.compile(r'\bread_fst\s*\(\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
]

# For readRDS with file= keyword argument
_READRDS_KW_RE = re.compile(r'\breadRDS\s*\(.*?\bfile\s*=\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)

# ---------------------------------------------------------------------------
# WRITE patterns
# ---------------------------------------------------------------------------

# Writes where the path is the SECOND positional arg: func(data, "path")
_WRITES_DATA_THEN_PATH: list[tuple[str, re.Pattern[str]]] = [
    # base R
    ('write_csv',   re.compile(r'\bwrite\.csv\s*\([^,]+,\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
    ('write_csv2',  re.compile(r'\bwrite\.csv2\s*\([^,]+,\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
    ('write_table', re.compile(r'\bwrite\.table\s*\([^,]+,\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
    ('saveRDS',     re.compile(r'\bsaveRDS\s*\([^,]+,\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
    # readr
    ('write_csv_readr',  re.compile(r'\bwrite_csv\s*\([^,]+,\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
    ('write_csv2_readr', re.compile(r'\bwrite_csv2\s*\([^,]+,\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
    ('write_tsv',        re.compile(r'\bwrite_tsv\s*\([^,]+,\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
    ('write_delim',      re.compile(r'\bwrite_delim\s*\([^,]+,\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
    ('write_rds',        re.compile(r'\bwrite_rds\s*\([^,]+,\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
    # writexl
    ('write_xlsx', re.compile(r'\bwrite_xlsx\s*\([^,]+,\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
    # data.table
    ('fwrite', re.compile(r'\bfwrite\s*\([^,]+,\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
    # haven
    ('write_dta', re.compile(r'\bwrite_dta\s*\([^,]+,\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
    ('write_sav', re.compile(r'\bwrite_sav\s*\([^,]+,\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
    ('write_sas', re.compile(r'\bwrite_sas\s*\([^,]+,\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
    # arrow
    ('write_parquet', re.compile(r'\bwrite_parquet\s*\([^,]+,\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
    ('write_feather', re.compile(r'\bwrite_feather\s*\([^,]+,\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
    # sf (spatial)
    ('st_write',    re.compile(r'\bst_write\s*\([^,]+,\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
    ('st_write_ns', re.compile(r'\bsf::st_write\s*\([^,]+,\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
    # tmap (positional form)
    ('tmap_save', re.compile(r'\btmap_save\s*\([^,]+,\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
    # htmlwidgets (positional form)
    ('saveWidget', re.compile(r'\bsaveWidget\s*\([^,]+,\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
    # writeLines (positional form)
    ('writeLines', re.compile(r'\bwriteLines\s*\([^,]+,\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
    # openxlsx
    ('write.xlsx',    re.compile(r'\bwrite\.xlsx\s*\([^,]+,\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
    ('saveWorkbook',  re.compile(r'\bsaveWorkbook\s*\([^,]+,\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
    # fst
    ('write.fst', re.compile(r'\bwrite\.fst\s*\([^,]+,\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
]

# Writes with keyword argument: file="path" or filename="path"
_WRITES_KEYWORD: list[tuple[str, re.Pattern[str]]] = [
    # saveRDS(data, file="path")
    ('saveRDS_kw', re.compile(r'\bsaveRDS\s*\(.*?\bfile\s*=\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
    # save(..., file="path")
    ('save_rdata', re.compile(r'\bsave\s*\(.*?\bfile\s*=\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
    # ggsave("path") — path is first arg
    ('ggsave',     re.compile(r'\bggsave\s*\(\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
    # ggsave(filename="path")
    ('ggsave_kw',  re.compile(r'\bggsave\s*\(.*?\bfilename\s*=\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
    # graphics devices: pdf/png/svg/jpeg/tiff("path")
    ('pdf',  re.compile(r'\bpdf\s*\(\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
    ('png',  re.compile(r'\bpng\s*\(\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
    ('svg',  re.compile(r'\bsvg\s*\(\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
    ('jpeg', re.compile(r'\bjpeg\s*\(\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
    ('tiff', re.compile(r'\btiff\s*\(\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
    # jsonlite
    ('write_json', re.compile(r'\bwrite_json\s*\([^,]+,\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
    ('toJSON_write', re.compile(r'\btoJSON\s*\(.*?\bpath\s*=\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
    # tmap (keyword form)
    ('tmap_save_kw', re.compile(r'\btmap_save\s*\(.*?\bfilename\s*=\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
    # htmlwidgets (keyword form)
    ('saveWidget_kw', re.compile(r'\bsaveWidget\s*\(.*?\bfile\s*=\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
    # writeLines (keyword form)
    ('writeLines_kw', re.compile(r'\bwriteLines\s*\(.*?\bcon\s*=\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)),
]

# ---------------------------------------------------------------------------
# Script call patterns
# ---------------------------------------------------------------------------
_SOURCE_RE = re.compile(r'\bsource\s*\(\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)
_SYS_SOURCE_RE = re.compile(r'\bsys\.source\s*\(\s*(?:"([^"]+)"|\'([^\']+)\')', re.I)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _join_continued_lines(lines: list[str]) -> list[str]:
    """
    Join lines where parentheses are not yet closed so that multi-line
    function calls become a single logical line.  Each joined line keeps
    the line-number of the FIRST physical line (the rest are replaced with
    empty strings so line counts stay correct).
    """
    result: list[str] = []
    buf = ''
    depth = 0
    for raw in lines:
        # Strip comment for paren-counting but keep original for result
        stripped = _strip_comment(raw)
        for ch in stripped:
            if ch == '(':
                depth += 1
            elif ch == ')':
                depth -= 1
        if buf:
            buf = buf.rstrip() + ' ' + raw.strip()
        else:
            buf = raw
        if depth <= 0:
            result.append(buf)
            buf = ''
            depth = 0
        else:
            # Will be consumed by next line; emit empty placeholder
            result.append('')
    if buf:
        result.append(buf)
    return result


def _strip_comment(line: str) -> str:
    """Remove R # comments, handling basic string literal detection."""
    in_single = False
    in_double = False
    for i, ch in enumerate(line):
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch == '#' and not in_single and not in_double:
            return line[:i]
    return line


def _is_external(path: str) -> bool:
    return any(path.startswith(p) for p in _EXTERNAL_PREFIXES)


def _extract_quoted_args(args_text: str) -> list[str | None]:
    """Extract a list of string values from comma-separated args text.
    Returns None for each arg that is not a plain quoted string."""
    result = []
    for piece in args_text.split(','):
        piece = piece.strip()
        m = _QUOTED_RE.match(piece)
        if m:
            result.append(m.group(1) or m.group(2))
        else:
            result.append(piece if piece else None)  # keep var name for expansion
    return result


def _resolve_path_args(args_text: str, vars_map: dict[str, str]) -> str | None:
    """Resolve a comma-separated list of path components to a joined path."""
    parts = []
    for piece in args_text.split(','):
        piece = piece.strip()
        if not piece:
            continue
        m = _QUOTED_RE.match(piece)
        if m:
            parts.append(m.group(1) or m.group(2))
        elif piece in vars_map:
            parts.append(vars_map[piece])
        else:
            return None  # unresolvable component
    return '/'.join(parts) if parts else None


def _resolve_here(line: str, vars_map: dict[str, str]) -> list[str]:
    """Resolve here() / here::here() calls."""
    results = []
    for m in _HERE_RE.finditer(line):
        resolved = _resolve_path_args(m.group(1), vars_map)
        if resolved:
            results.append((m.start(), m.end(), resolved))
    # Return paths only
    return [r for _, _, r in results]


def _resolve_filepath(line: str, vars_map: dict[str, str]) -> list[str]:
    """Resolve file.path() calls."""
    results = []
    for m in _FILEPATH_RE.finditer(line):
        resolved = _resolve_path_args(m.group(1), vars_map)
        if resolved:
            results.append(resolved)
    return results


def _resolve_paste0(line: str, vars_map: dict[str, str]) -> list[str]:
    """Resolve paste0() calls where all args are literals or known vars."""
    results = []
    for m in _PASTE0_RE.finditer(line):
        resolved = _resolve_path_args(m.group(1), vars_map)
        if resolved and ('.' in resolved or '/' in resolved):
            # Only include if it looks like a file path
            results.append(resolved)
    return results


def _resolve_sprintf(line: str, vars_map: dict[str, str]) -> list[str]:
    """Resolve sprintf("template/%s/%s/file.csv", arg1, arg2, ...) with multiple placeholders."""
    results = []
    for m in _SPRINTF_RE.finditer(line):
        template = m.group(1) or m.group(2)
        args_text = (m.group(3) or '').strip()
        # Count total format specifiers (%s, %d, %f, %i, %g)
        placeholders = re.findall(r'%[sdfig]', template)
        if not placeholders:
            continue
        # Split args by comma, resolve each
        raw_args = [a.strip() for a in args_text.split(',')]
        if len(raw_args) < len(placeholders):
            continue  # not enough args
        subs = []
        ok = True
        for i, ph in enumerate(placeholders):
            arg = raw_args[i] if i < len(raw_args) else ''
            quoted_m = _QUOTED_RE.match(arg)
            if quoted_m:
                subs.append(quoted_m.group(1) or quoted_m.group(2))
            elif arg in vars_map:
                subs.append(vars_map[arg])
            else:
                ok = False
                break
        if not ok:
            continue
        result = template
        for sub in subs:
            result = re.sub(r'%[sdfig]', sub, result, count=1)
        results.append(result)
    return results


def _try_match(pattern: re.Pattern[str], line: str, vars_map: dict[str, str]) -> str | None:
    m = pattern.search(line)
    if not m:
        return None
    raw = m.group(1) if m.group(1) is not None else m.group(2)
    if raw is None:
        return None
    return vars_map.get(raw, raw)


def _preprocess_helpers(line: str, vars_map: dict[str, str]) -> tuple[str, list[str]]:
    """
    Replace path helper calls in line with their resolved quoted equivalents.
    Returns (modified_line, list_of_standalone_paths).
    Standalone paths come from helper calls that aren't embedded in a read/write call.
    """
    standalone: list[str] = []

    def replace_here(m: re.Match[str]) -> str:
        resolved = _resolve_path_args(m.group(1), vars_map)
        if resolved:
            return f'"{resolved}"'
        return m.group(0)

    def replace_filepath(m: re.Match[str]) -> str:
        resolved = _resolve_path_args(m.group(1), vars_map)
        if resolved:
            return f'"{resolved}"'
        return m.group(0)

    def replace_paste0(m: re.Match[str]) -> str:
        resolved = _resolve_path_args(m.group(1), vars_map)
        if resolved and ('.' in resolved or '/' in resolved):
            return f'"{resolved}"'
        return m.group(0)

    def replace_sprintf(m: re.Match[str]) -> str:
        template = m.group(1) or m.group(2)
        args_text = (m.group(3) or '').strip()
        placeholders = re.findall(r'%[sdfig]', template)
        if not placeholders:
            return m.group(0)
        raw_args = [a.strip() for a in args_text.split(',')]
        if len(raw_args) < len(placeholders):
            return m.group(0)
        subs = []
        for i, _ in enumerate(placeholders):
            arg = raw_args[i] if i < len(raw_args) else ''
            quoted_m = _QUOTED_RE.match(arg)
            if quoted_m:
                subs.append(quoted_m.group(1) or quoted_m.group(2))
            elif arg in vars_map:
                subs.append(vars_map[arg])
            else:
                return m.group(0)
        result = template
        for sub in subs:
            result = re.sub(r'%[sdfig]', sub, result, count=1)
        return f'"{result}"'

    line = _HERE_RE.sub(replace_here, line)
    line = _FILEPATH_RE.sub(replace_filepath, line)
    line = _PASTE0_RE.sub(replace_paste0, line)
    line = _SPRINTF_RE.sub(replace_sprintf, line)
    return line, standalone


# ---------------------------------------------------------------------------
# Main parser
# ---------------------------------------------------------------------------

def parse_r_file(
    project_root: Path,
    r_file: Path,
    exclusions: ExclusionConfig,
    normalization: NormalizationConfig,
    parser_config: ParserConfig,
) -> ScriptParseResult:
    try:
        text = r_file.read_text(encoding='utf-8', errors='replace')
    except OSError:
        return ScriptParseResult(events=[], child_scripts=[], global_warnings=[])

    raw_lines = text.splitlines()
    rel_script, _ = to_project_relative(project_root, r_file, normalization)
    rel_script = normalize_token(rel_script)

    # Join multi-line function calls into single logical lines
    joined_lines = _join_continued_lines(raw_lines)

    # --- Pre-pass: collect variable assignments ---
    # Seed with the script's own directory (R's __file__ equivalents resolve to this)
    vars_map: dict[str, str] = {}
    script_dir_str = str(r_file.parent).replace('\\', '/')
    vars_map['__script_dir__'] = script_dir_str

    # First pass: collect literal string assignments
    for line in joined_lines:
        clean = _strip_comment(line)
        m = _VAR_ASSIGN_RE.match(clean)
        if m:
            val = m.group(2) if m.group(2) is not None else m.group(3)
            vars_map[m.group(1)] = val

    # Second pass: resolve script-dir idioms and function-call RHS assignments
    # Repeat a few times to handle chained assignments (script_path -> script_dir -> path)
    for _iteration in range(3):
        for line in joined_lines:
            clean = _strip_comment(line)
            # Pattern: var <- dirname(sys.frame(1)$ofile)  etc.
            m = _SCRIPT_DIR_RE.match(clean)
            if m:
                vars_map[m.group(1)] = script_dir_str
                continue
            # Pattern: var <- getSrcFilename(...) — evaluates to the script's path
            m = _GETSRCFILENAME_RE.match(clean)
            if m:
                vars_map[m.group(1)] = str(r_file).replace('\\', '/')
                continue
            # Pattern: var <- dirname(some_var) where some_var is already resolved
            m_dir = re.match(r'^\s*(\w+)\s*(?:<-|=)\s*dirname\s*\(\s*(\w+)\s*\)', clean)
            if m_dir:
                src_var = m_dir.group(2)
                if src_var in vars_map:
                    from pathlib import PurePosixPath
                    vars_map[m_dir.group(1)] = str(PurePosixPath(vars_map[src_var]).parent)
                continue
            # Pattern: var <- paste0(...)  — store resolved value
            m_assign = re.match(r'^\s*(\w+)\s*(?:<-|=)\s*(paste0\s*\()', clean)
            if m_assign:
                paste_start = clean.index('paste0')
                resolved_list = _resolve_paste0(clean[paste_start:], vars_map)
                if resolved_list:
                    vars_map[m_assign.group(1)] = resolved_list[0]
                continue
            # Pattern: var <- sprintf(...)  — store resolved value
            m_assign2 = re.match(r'^\s*(\w+)\s*(?:<-|=)\s*(sprintf\s*\()', clean)
            if m_assign2:
                sp_start = clean.index('sprintf')
                resolved_list = _resolve_sprintf(clean[sp_start:], vars_map)
                if resolved_list:
                    vars_map[m_assign2.group(1)] = resolved_list[0]
                continue
            # Pattern: var <- file.path(...)  — store resolved value
            m_assign3 = re.match(r'^\s*(\w+)\s*(?:<-|=)\s*(file\.path\s*\()', clean, re.I)
            if m_assign3:
                fp_start = clean.lower().index('file.path')
                resolved_list = _resolve_filepath(clean[fp_start:], vars_map)
                if resolved_list:
                    vars_map[m_assign3.group(1)] = resolved_list[0]
                continue

    events: list[ParsedEvent] = []
    child_scripts: list[str] = []
    global_warnings: list[Diagnostic] = []
    excluded_references: list[Diagnostic] = []

    seen_paths: set[tuple[str, str]] = set()

    def _add_event(line_no: int, command: str, raw_path: str, is_write: bool) -> None:
        if _is_external(raw_path):
            global_warnings.append(Diagnostic(
                level='info',
                code='external_reference',
                message=f'External reference skipped in {rel_script}:{line_no}: {raw_path}',
                payload={'script': rel_script, 'path': raw_path},
            ))
            return
        resolved_path = raw_path
        if '..' in raw_path and not Path(raw_path).is_absolute():
            resolved_path = str((r_file.parent / raw_path).resolve())
        norm, was_abs = to_project_relative(project_root, Path(resolved_path), normalization)
        norm = normalize_token(norm)
        if is_excluded(norm, exclusions):
            excluded_references.append(_excluded_reference(rel_script, line_no, command, norm))
            return
        key = (command, norm)
        if key in seen_paths:
            return
        seen_paths.add(key)
        events.append(ParsedEvent(
            script=rel_script,
            line=line_no,
            command=command,
            raw_path=raw_path,
            normalized_paths=[norm],
            was_absolute=was_abs,
        ))

    def _add_child(raw_path: str) -> None:
        candidate = r_file.parent / raw_path
        if candidate.exists():
            raw_path = str(candidate.relative_to(project_root)).replace('\\', '/')
        norm, _ = to_project_relative(project_root, Path(raw_path), normalization)
        norm = normalize_token(norm)
        if norm not in child_scripts:
            child_scripts.append(norm)

    all_write_patterns = _WRITES_DATA_THEN_PATH + _WRITES_KEYWORD

    for line_no, raw_line in enumerate(joined_lines, start=1):
        line = _strip_comment(raw_line)

        # --- Script calls ---
        for pattern in (_SOURCE_RE, _SYS_SOURCE_RE):
            m = pattern.search(line)
            if m:
                raw = m.group(1) or m.group(2)
                if raw:
                    _add_child(raw)

        # --- Preprocess path helpers (inline replacement) ---
        line, _ = _preprocess_helpers(line, vars_map)

        # --- Expand bare variable names to quoted values for pattern matching ---
        for _var, _val in vars_map.items():
            line = re.sub(rf'\b{re.escape(_var)}\b', f'"{_val}"', line)

        # --- Read patterns ---
        matched_read = False
        for command, pattern in _READS_FIRST_ARG:
            raw = _try_match(pattern, line, vars_map)
            if raw is not None:
                _add_event(line_no, command, raw, is_write=False)
                matched_read = True
                break

        if not matched_read:
            # readRDS(file="path")
            raw = _try_match(_READRDS_KW_RE, line, vars_map)
            if raw is not None:
                _add_event(line_no, 'readRDS', raw, is_write=False)

        # --- Write patterns ---
        for command, pattern in all_write_patterns:
            raw = _try_match(pattern, line, vars_map)
            if raw is not None:
                _add_event(line_no, command, raw, is_write=True)
                break

    return ScriptParseResult(
        events=events,
        child_scripts=child_scripts,
        global_warnings=global_warnings,
        excluded_references=excluded_references,
    )
