"""Binary well-log (.log) header parsing.

Byte offsets and the ORIGINAL/PROCESSED status-word convention are taken from
the field logging tool's own fixed header layout, cross-checked against the
Cloud-App project's ``config/<tool>_config.json`` files and confirmed against
real Roy Hill log files. Each tool code (9622, 9138, 9238, 0037, ...) has its
own JSON config under this project's ``config/`` folder describing where each
header field and each data curve lives in the file.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config"

STATUS_RE = re.compile(rb"(ORIGINAL|PROCESSED)")

HEADER_READ_BYTES = 4096


class UnknownToolError(Exception):
    pass


@dataclass(frozen=True)
class ToolConfig:
    tool_code: str
    header_addresses: dict
    data_start_offset: int
    data_step: int
    declared_row_length: int
    depth_increment: float
    columns: list[str]
    raw: dict


_CONFIG_CACHE: dict[str, ToolConfig] = {}


def load_tool_config(tool_code: str) -> ToolConfig:
    """Load and cache the config for a 4-digit tool code, e.g. '9622'."""
    if tool_code in _CONFIG_CACHE:
        return _CONFIG_CACHE[tool_code]

    path = CONFIG_DIR / f"{tool_code}_config.json"
    if not path.exists():
        raise UnknownToolError(
            f"No config/{tool_code}_config.json -- this tool code isn't set up yet."
        )

    raw = json.loads(path.read_text())
    header_addresses = {
        key: {"start": int(info["start"], 16), "length": info["length"]}
        for key, info in raw["header_addresses"].items()
    }
    data = raw.get("data", {})
    config = ToolConfig(
        tool_code=tool_code,
        header_addresses=header_addresses,
        data_start_offset=int(data.get("start_offset", "0x0"), 16),
        data_step=int(data.get("step", 4)),
        declared_row_length=int(data.get("row_length", 0)),
        depth_increment=float(data.get("depth_increment", 0.1)),
        columns=list(raw.get("columns", [])),
        raw=raw,
    )
    _CONFIG_CACHE[tool_code] = config
    return config


def available_tool_codes() -> list[str]:
    return sorted(p.stem.replace("_config", "") for p in CONFIG_DIR.glob("*_config.json"))


@dataclass
class LogHeader:
    status: Optional[str]          # "ORIGINAL" | "PROCESSED" | None (not found)
    tool_no: str
    serial_no: str
    logging_unit: str
    operator: str
    date: str                      # as stored, e.g. "07/14/26"
    time: str
    start_depth: Optional[float]
    stop_depth: Optional[float]


def _read_field(data: bytes, start: int, length: int) -> str:
    return data[start:start + length].decode("ascii", errors="replace").strip()


def read_header(file_bytes: bytes, tool_code: str) -> LogHeader:
    config = load_tool_config(tool_code)
    addrs = config.header_addresses

    def field(key: str) -> str:
        info = addrs.get(key)
        if not info:
            return ""
        return _read_field(file_bytes, info["start"], info["length"])

    status_match = STATUS_RE.search(file_bytes[:400])
    status = status_match.group(1).decode() if status_match else None

    def as_float(value: str) -> Optional[float]:
        try:
            return float(value)
        except ValueError:
            return None

    return LogHeader(
        status=status,
        tool_no=field("Tool No."),
        serial_no=field("Serial No."),
        logging_unit=field("LogU"),
        operator=field("Operator"),
        date=field("Date"),
        time=field("Time"),
        start_depth=as_float(field("Start Depth")),
        stop_depth=as_float(field("Stop Depth")),
    )
