"""Decode the fixed-width curve data table inside a binary .log file, and
detect when it's been decoded with the wrong row width.

Background: each row of a log's data section is a fixed number of 4-byte
floats (one per curve). The tool config declares that number, but a handful
of files -- either short a curve, or from a tool variant the shared config
doesn't know about -- actually have a different row width. Decoding those
with the wrong width doesn't fail outright: it silently reads each row a few
bytes into the next one, so a value that should stay in a single curve's
column instead drifts sideways by one column every row. On screen that looks
exactly like a curve got duplicated into its neighbour's track.

``resolve_row_length`` tries a small window of candidate row widths around
the declared value and picks whichever one makes the decoded curves
*smoothest* -- real depth-logged measurements change gradually row to row;
decoding at the wrong row width scrambles bytes across curve boundaries and
produces sharp, noisy jumps instead. The "roughness" of a candidate is the
median absolute row-to-row jump, averaged across columns; the real row width
is the one with the lowest roughness by a wide margin.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass

from src.services.log_header import ToolConfig

NULL_VALUE = -999999.0


@dataclass
class RowLayoutResult:
    declared_row_length: int
    resolved_row_length: int
    n_rows: int
    roughness_at_declared: float | None
    roughness_at_resolved: float | None
    mismatch: bool  # True if resolved != declared -> likely mis-decoded / "duplicated" curves


def _decode_columns(data: bytes, start: int, step: int, row_length: int) -> list[list[float]]:
    if row_length <= 0:
        return []
    n_rows = (len(data) - start) // (row_length * step)
    columns: list[list[float]] = [[0.0] * n_rows for _ in range(row_length)]
    for i in range(n_rows):
        base = start + i * row_length * step
        for j in range(row_length):
            columns[j][i] = struct.unpack_from("<f", data, base + j * step)[0]
    return columns


def _median(values: list[float]) -> float:
    values = sorted(values)
    return values[len(values) // 2]


def _roughness(columns: list[list[float]]) -> float | None:
    """Median absolute row-to-row jump, averaged across usable columns.
    Lower = smoother = more likely the true row width."""
    totals = []
    for col in columns:
        vals = [v for v in col if -1e6 < v < 1e6]  # drop the null-value sentinel
        if len(vals) < 10:
            continue
        diffs = [abs(vals[i + 1] - vals[i]) for i in range(len(vals) - 1)]
        totals.append(_median(diffs))
    return (sum(totals) / len(totals)) if totals else None


def resolve_row_length(file_bytes: bytes, config: ToolConfig, search_radius: int = 2) -> RowLayoutResult:
    """Find the row width that best explains this file's own data, by
    minimising row-to-row roughness near the declared width."""
    declared = config.declared_row_length
    start = config.data_start_offset
    step = config.data_step

    best_len = declared
    best_score = None
    declared_score = None

    for candidate in range(max(1, declared - search_radius), declared + search_radius + 1):
        bytes_available = len(file_bytes) - start
        if bytes_available < candidate * step * 20:
            continue
        columns = _decode_columns(file_bytes, start, step, candidate)
        score = _roughness(columns)
        if candidate == declared:
            declared_score = score
        if score is not None and (best_score is None or score < best_score):
            best_score = score
            best_len = candidate

    n_rows = (len(file_bytes) - start) // (max(best_len, 1) * step)

    # Only call it a mismatch if the declared width is clearly worse (not
    # just noise) -- require at least a 3x roughness gap.
    mismatch = (
        best_len != declared
        and best_score is not None
        and declared_score is not None
        and declared_score > best_score * 3
    )

    return RowLayoutResult(
        declared_row_length=declared,
        resolved_row_length=best_len,
        n_rows=n_rows,
        roughness_at_declared=declared_score,
        roughness_at_resolved=best_score,
        mismatch=mismatch,
    )


def decode_curves(file_bytes: bytes, config: ToolConfig, row_length: int) -> dict[str, list[float]]:
    """Decode curve columns using an explicit row_length, named per the
    tool's declared column order (best-effort past the declared width)."""
    start = config.data_start_offset
    step = config.data_step
    columns = _decode_columns(file_bytes, start, step, row_length)

    names = list(config.columns[1:])  # columns[0] is DEPTH, computed not stored
    out: dict[str, list[float]] = {}
    for j, col in enumerate(columns):
        name = names[j] if j < len(names) else f"COL_{j}"
        out[name] = col
    return out
