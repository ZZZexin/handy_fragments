from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="Handy Tools",
    page_icon=":hammer:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.title("Handy Tools")

# Automatically find all Python files inside pages/ (resolved relative to
# this file, not the process cwd, so it works regardless of where
# `streamlit run` was launched from).
pages_dir = Path(__file__).resolve().parent / "pages"
tool_pages = {
    page_file.stem.replace("_", " ").title(): f"pages/{page_file.name}"
    for page_file in sorted(pages_dir.glob("*.py"))
}

if not tool_pages:
    st.info("No tools yet -- add a page under pages/ to get started.")
    st.stop()

container_func = st.container(border=True)
selected_tool = container_func.selectbox(
    "",
    list(tool_pages.keys()),
    placeholder="Select a tool",
    index=None,
    key="selected_tool",
)

if container_func.button("Open selected tool", type="primary"):
    if selected_tool is None:
        st.warning("Please select a tool first.")
    else:
        st.switch_page(tool_pages[selected_tool])
