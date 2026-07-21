"""Drag-and-drop .log files, flag ORIG-named files whose header says PROCESSED."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.services.log_scanner import check_uploads
from src.ui.components import download_csv_button, metric_row, results_table

st.set_page_config(page_title="Log Header QC", page_icon=":mag:", layout="wide")

st.title("Log Header QC")

files = st.file_uploader("Drop .log files here", type=["log"], accept_multiple_files=True)

if files:
    rows = check_uploads(files)
    df = pd.DataFrame(rows)

    if df.empty:
        st.info("None of these files could be identified (unknown tool code).")
    else:
        metric_row(
            {
                "Files checked": len(df),
                "ORIG named, header = PROCESSED": int(df["naming_mismatch"].sum()),
                "Likely shows duplicated curves": int(df["row_width_mismatch"].sum()),
            }
        )
        st.divider()
        results_table(df, highlight_col="row_width_mismatch")
        download_csv_button(df, filename="log_header_qc_summary.csv")
