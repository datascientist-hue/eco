import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="NK Dashboard Suite",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📊 NK Dashboard Suite")
st.write("Use the sidebar to navigate between dashboard pages.")

st.markdown(
    """
### Available Pages
- Inventory Ageing
- Open Purchase Orders
- Open Sale Orders
- Overdue Creditor Report
- Overdue Payment Report
- Stock Status
"""
)

st.subheader("Quick Navigation")

def safe_page_link(page_file: str, label: str, icon: str, container=st):
    page_path = Path(__file__).parent / "pages" / page_file
    try:
        container.page_link(page_path, label=label, icon=icon)
    except Exception:
        container.caption(f"{icon} {label} (open from sidebar)")

safe_page_link("Inventory.py", "Inventory Ageing", "📦")
safe_page_link("Open_PO.py", "Open Purchase Orders", "📥")
safe_page_link("Open_SO.py", "Open Sale Orders", "📤")
safe_page_link("Overdue_Creditor_Report.py", "Overdue Creditor Report", "💳")
safe_page_link("Overdue_Payment_Report.py", "Overdue Payment Report", "⏰")
safe_page_link("Stock_Status.py", "Stock Status", "📊")

st.sidebar.markdown("### Pages")
safe_page_link("Inventory.py", "Inventory Ageing", "📦", st.sidebar)
safe_page_link("Open_PO.py", "Open Purchase Orders", "📥", st.sidebar)
safe_page_link("Open_SO.py", "Open Sale Orders", "📤", st.sidebar)
safe_page_link("Overdue_Creditor_Report.py", "Overdue Creditor Report", "💳", st.sidebar)
safe_page_link("Overdue_Payment_Report.py", "Overdue Payment Report", "⏰", st.sidebar)
safe_page_link("Stock_Status.py", "Stock Status", "📊", st.sidebar)
