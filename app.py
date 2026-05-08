import streamlit as st
from pathlib import Path

st.set_page_config(
                    page_title="Handy Tools", 
                    page_icon = ":hammer:",
                    layout = "wide",
                   initial_sidebar_state="collapsed" 
                   )

st.title("Handy Tools")

# Automatically find all Python files inside pages/
pages_dir = Path("pages")
tool_pages = {}

for page_file in pages_dir.glob("*.py"):
    page_name = page_file.stem.replace("_", " ").title()
    tool_pages[page_name] = str(page_file)

# Default remembered selection
if "selected_tool" not in st.session_state:
    st.session_state.selected_tool = None

# container for function options
container_func=st.container(border=True)
selected_tool = container_func.selectbox(
    "",
    list(tool_pages.keys()),
    placeholder = "Select a tool",
    key="selected_tool"
)

if container_func.button("Open selected tool", type='primary'):
    if selected_tool is None:
        st.warning("Please select a tool first.")
    else:
        st.switch_page(tool_pages[selected_tool])


st.write("Selected tool:", selected_tool)

if selected_tool == "Weekly DPC":
    st.markdown("Weekly DPC tool selected.")

elif selected_tool == "TV DEPTH MATCH":
    st.markdown("TV Depth Match tool selected.")

else:
    st.markdown("Under construction.")