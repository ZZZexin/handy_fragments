"""Small path/filename helpers used by the log-file checker."""

import re
from pathlib import Path

HOLE_ID_RE = re.compile(r"([A-Z]{2,6}\d{6,})")
TOOL_TOKEN_RE = re.compile(r"_(\d{4}[A-Z]{0,2})_\.\d+_")


def find_hole_id(filename: str) -> str:
    """Best-effort hole ID from a log filename; falls back to the leading token."""
    match = HOLE_ID_RE.match(filename)
    if match:
        return match.group(1)
    return filename.split("_")[0]


def claims_original(filename: str) -> bool:
    """True if the filename itself asserts this is raw/original data
    (contains an ``ORIG`` token) rather than a processed export."""
    return "ORIG" in filename.upper()


def find_tool_code(filename: str) -> str | None:
    """4-digit tool code (e.g. '9622') embedded in a log filename, or None."""
    match = TOOL_TOKEN_RE.search(filename)
    if not match:
        return None
    return match.group(1)[:4]


def is_calibration_path(path: Path) -> bool:
    return "CALIBRATION" in str(path).upper()
