"""Reusable Streamlit UI pieces, shared across tool pages."""

from __future__ import annotations

import pandas as pd
import streamlit as st


def folder_picker(label: str, key: str, default: str = "") -> str:
    """A plain text input for a folder path (Streamlit has no native folder
    dialog outside a packaged desktop app -- paste-the-path is the reliable
    cross-platform option)."""
    return st.text_input(label, value=default, key=key, placeholder=r"C:\path\to\folder")


def results_table(df: pd.DataFrame, highlight_col: str | None = None) -> None:
    if df.empty:
        st.info("Nothing to show yet.")
        return

    def _row_style(row: pd.Series) -> list[str]:
        if highlight_col and bool(row.get(highlight_col)):
            return ["background-color: #ffe4e0"] * len(row)
        return [""] * len(row)

    st.dataframe(
        df.style.apply(_row_style, axis=1) if highlight_col else df,
        use_container_width=True,
        hide_index=True,
    )


def download_csv_button(df: pd.DataFrame, filename: str, label: str = "Download CSV") -> None:
    if df.empty:
        return
    csv_bytes = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(label, data=csv_bytes, file_name=filename, mime="text/csv")


def metric_row(metrics: dict[str, int | str]) -> None:
    cols = st.columns(len(metrics))
    for col, (label, value) in zip(cols, metrics.items()):
        col.metric(label, value)
