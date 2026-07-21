"""Walk a folder of Roy-Hill-style .log files and flag the ORIG/PROCESSED
filename-vs-header mismatch, plus the row-width ("duplicated curve") issue.

Two independent checks per file:

1. Naming mismatch: filename ends in ``_ORIG.log`` (claims to be the raw
   original) but the header status word actually reads ``PROCESSED``.
2. Row-width mismatch: the file's own data doesn't line up cleanly at the
   tool's declared row width, which -- when decoded naively -- makes a curve
   appear to drift/duplicate into its neighbours (see ``log_curves.py``).
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Optional

from src.services.log_curves import resolve_row_length
from src.services.log_header import (
    HEADER_READ_BYTES,
    LogHeader,
    UnknownToolError,
    load_tool_config,
    read_header,
)
from src.utils.paths import claims_original, find_hole_id, find_tool_code, is_calibration_path

ORIG_GLOB_PATTERNS = ("*ORIG*.log", "*ORIG*.LOG")


@dataclass
class LogCheckResult:
    file_path: str
    file_name: str
    hole_id: str
    tool_code: Optional[str]
    header_status: Optional[str]
    naming_mismatch: bool          # filename says ORIG, header says PROCESSED
    logging_unit: str
    operator: str
    tool_no: str
    serial_no: str
    log_date: str
    log_time: str
    declared_row_length: Optional[int]
    resolved_row_length: Optional[int]
    row_width_mismatch: bool       # likely mis-decoded / "duplicated" curves
    note: str


def _iter_orig_files(root: Path) -> Iterable[Path]:
    seen: set[str] = set()
    for pattern in ORIG_GLOB_PATTERNS:
        for path in root.rglob(pattern):
            key = str(path).lower()
            if key in seen:
                continue
            seen.add(key)
            yield path


def check_bytes(file_name: str, file_bytes: bytes, file_path: str | None = None) -> Optional[LogCheckResult]:
    """Run both checks on a single *_ORIG.log file's raw bytes. Returns None
    if the file can't be identified (no tool code in the filename, or config
    missing). Used by both the folder scanner and the drag-and-drop uploader."""
    tool_code = find_tool_code(file_name)
    if tool_code is None:
        return None

    try:
        config = load_tool_config(tool_code)
    except UnknownToolError as exc:
        return LogCheckResult(
            file_path=file_path or file_name,
            file_name=file_name,
            hole_id=find_hole_id(file_name),
            tool_code=tool_code,
            header_status=None,
            naming_mismatch=False,
            logging_unit="",
            operator="",
            tool_no="",
            serial_no="",
            log_date="",
            log_time="",
            declared_row_length=None,
            resolved_row_length=None,
            row_width_mismatch=False,
            note=str(exc),
        )

    header_bytes = file_bytes[:HEADER_READ_BYTES]
    header: LogHeader = read_header(header_bytes, tool_code)

    # Only a mismatch if the filename itself claims to be original data --
    # a correctly-named "_PROC.log" with header PROCESSED is fine, not flagged.
    naming_mismatch = claims_original(file_name) and header.status == "PROCESSED"

    row_result = None
    row_width_mismatch = False
    if naming_mismatch:
        row_result = resolve_row_length(file_bytes, config)
        row_width_mismatch = row_result.mismatch

    if row_result is not None:
        note_parts = []
        if naming_mismatch:
            note_parts.append("filename says ORIG but header says PROCESSED")
        if row_width_mismatch:
            note_parts.append(
                f"row width looks wrong (declared {row_result.declared_row_length}, "
                f"actual data lines up at {row_result.resolved_row_length}) "
                "-- curves will likely display as shifted/duplicated"
            )
        note = "; ".join(note_parts) if note_parts else "ok"
    else:
        note = "filename says ORIG but header says PROCESSED" if naming_mismatch else "ok"

    return LogCheckResult(
        file_path=file_path or file_name,
        file_name=file_name,
        hole_id=find_hole_id(file_name),
        tool_code=tool_code,
        header_status=header.status,
        naming_mismatch=naming_mismatch,
        logging_unit=header.logging_unit,
        operator=header.operator,
        tool_no=header.tool_no,
        serial_no=header.serial_no,
        log_date=header.date,
        log_time=header.time,
        declared_row_length=row_result.declared_row_length if row_result else None,
        resolved_row_length=row_result.resolved_row_length if row_result else None,
        row_width_mismatch=row_width_mismatch,
        note=note,
    )


def check_file(path: Path) -> Optional[LogCheckResult]:
    """Run both checks on a single *_ORIG.log file on disk."""
    return check_bytes(path.name, path.read_bytes(), file_path=str(path))


def check_uploads(files, flagged_only: bool = False) -> list[dict]:
    """Check a list of Streamlit ``UploadedFile`` objects (drag-and-dropped).

    Filenames don't need to contain "ORIG" -- every dropped file is checked;
    ``naming_mismatch``/``row_width_mismatch`` in the result tell you what's
    wrong, if anything.
    """
    rows: list[dict] = []
    for uploaded in files:
        result = check_bytes(uploaded.name, uploaded.getvalue())
        if result is None:
            continue
        if flagged_only and not result.naming_mismatch:
            continue
        rows.append(asdict(result))
    rows.sort(key=lambda r: (r["hole_id"], r["log_date"], r["log_time"]))
    return rows


def scan_folder(
    root: str | Path,
    skip_calibration: bool = True,
    flagged_only: bool = True,
) -> list[dict]:
    """Scan ``root`` recursively for *_ORIG.log files and check each one.

    Returns a list of plain dicts (one per file), ready for a DataFrame.
    ``flagged_only`` (default True) keeps only files with a naming mismatch --
    set False to get every ORIG-named file's status, mismatched or not.
    """
    root_path = Path(root)
    if not root_path.exists():
        raise FileNotFoundError(f"Folder not found: {root_path}")

    rows: list[dict] = []
    for path in _iter_orig_files(root_path):
        if skip_calibration and is_calibration_path(path.relative_to(root_path)):
            continue
        result = check_file(path)
        if result is None:
            continue
        if flagged_only and not result.naming_mismatch:
            continue
        row = asdict(result)
        row["file_path"] = str(Path(row["file_path"]).relative_to(root_path))
        rows.append(row)

    rows.sort(key=lambda r: (r["hole_id"], r["log_date"], r["log_time"]))
    return rows
