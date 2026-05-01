import streamlit as st
import pandas as pd
import json
import openpyxl

from src.utils.read_well_report import ReadWellReport



readwellreport = ReadWellReport()
# header 


project_root = Path(__file__).resolve().parent
json_path = project_root / "src" / "config" / "weekly_dpc_sheet_template.json"
with open(json_path, "r", encoding="utf-8") as f:
    summary_template = json.load(f)
    f.close()

summary_col = summary_template["cols"]
formula_cols = summary_template["formula_cols"]

# load module
st.set_page_config(
    "Upload Well Report",
    layout="centered"
)
st.title("Generate Summary")

extraction = st.container(
                        border=True,
                        key = "wellreportextract")
extraction.write("Drop Well Reports")

load_well_reports = st.file_uploader(
                                    "Drop here", 
                                     type = ["xlsx"],
                                     accept_multiple_files=True)
# in-rod to check
inrod = ["NorthGyro", "GVGamma"]
# GPX to check
gpx = ["9622", "9238", "9138"]
# TV to check
tv = ["OBI", "ABI"]
# DGPS to check
dgps = ["DGPS"]

if load_well_reports is not None:
    try:
        for loadedwr in load_well_reports:
            hole_id = readwellreport.header_info(loadedwr)["hole_name"] #

            areainfo = readwellreport.area_info(loadedwr, area_search = "logging")
            







# the page