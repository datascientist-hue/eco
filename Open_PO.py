import streamlit as st
import pandas as pd
from datetime import timedelta
from data_loader import load_csv_from_ftp

# --- PAGE SETUP ---
# configure wide layout with custom theme if needed
st.set_page_config(page_title="Purchase Order Analysis", layout="wide", initial_sidebar_state="expanded")

# --- POWER BI STYLE CSS ---
power_bi_css = """
<style>
    * {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    [data-testid="stMarkdownContainer"] {
        padding: 0;
    }
    
    /* Main container */
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    /* Title styling */
    h1 {
        color: #1f3a93;
        font-size: 2.5em;
        font-weight: 700;
        margin-bottom: 0.5em;
        letter-spacing: -0.5px;
    }
    
    h2 {
        color: #1f3a93;
        font-size: 1.5em;
        font-weight: 600;
        margin-top: 1.5em;
    }
    
    h3 {
        color: #2d5aa1;
        font-size: 1.2em;
        font-weight: 600;
    }
    
    /* KPI Card styling */
    .kpi-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        border-radius: 12px;
        padding: 1.5em;
        border-left: 5px solid #0078d4;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        transition: all 0.3s ease;
        text-align: center;
    }
    
    .kpi-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
        border-left-color: #00a4ef;
    }
    
    .kpi-value {
        font-size: 2em;
        font-weight: 700;
        color: #0078d4;
        margin: 0.5em 0;
    }
    
    .kpi-label {
        font-size: 0.9em;
        color: #666;
        font-weight: 500;
        margin-top: 0.5em;
    }
    
    /* Status card */
    .status-card-good {
        border-left-color: #107c10;
    }
    
    .status-card-good .kpi-value {
        color: #107c10;
    }
    
    .status-card-warning {
        border-left-color: #ffc000;
    }
    
    .status-card-warning .kpi-value {
        color: #ffc000;
    }
    
    .status-card-critical {
        border-left-color: #d13438;
        background: linear-gradient(135deg, #fef5f5 0%, #fff8f8 100%);
    }
    
    .status-card-critical .kpi-value {
        color: #d13438;
    }
    
    /* Table styling */
    .dataframe {
        border-collapse: collapse !important;
        width: 100% !important;
        font-size: 0.95em;
    }
    
    .dataframe thead {
        background-color: #0078d4;
        color: white;
        font-weight: 600;
    }
    
    .dataframe tbody tr:nth-child(even) {
        background-color: #f5f5f5;
    }
    
    .dataframe tbody tr:hover {
        background-color: #e8f4f8;
    }
    
    /* Divider */
    hr {
        border: none;
        height: 2px;
        background: linear-gradient(to right, rgba(0, 120, 212, 0), rgba(0, 120, 212, 0.4), rgba(0, 120, 212, 0));
        margin: 2em 0;
    }
</style>
"""

st.markdown(power_bi_css, unsafe_allow_html=True)

def format_inr(x):
    """Format number according to Indian number system with rupee symbol.

    Large values are abbreviated: lakhs (L) and crores (Cr) to avoid excessive
    digit length. Otherwise numbers are shown with full comma separation.
    """
    try:
        x = float(x)
    except Exception:
        return x
    sign = "" if x >= 0 else "-"
    x = abs(x)
    # abbreviate
    if x >= 1e7:  # crore
        return f"{sign}₹ {x/1e7:,.2f}Cr"
    if x >= 1e5:  # lakh
        return f"{sign}₹ {x/1e5:,.2f}L"
    # normal formatting
    int_part, _, dec_part = f"{x:.2f}".partition('.')
    int_part = int_part.replace(',', '')
    if len(int_part) > 3:
        result = int_part[-3:]
        int_part = int_part[:-3]
        while len(int_part) > 2:
            result = int_part[-2:] + "," + result
            int_part = int_part[:-2]
        if int_part:
            result = int_part + "," + result
    else:
        result = int_part
    return f"{sign}₹ {result}.{dec_part}"

# --- DATA LOADING AND CLEANING ---
FILE_NAME = "Open_Purchase_Order_Report.csv"

@st.cache_data
def load_data(file_name):
    try:
        df = load_csv_from_ftp(file_name, encoding="latin1")
        
        # --- Data Cleaning ---
        numeric_columns = ['LineTotalBeforeTax', 'Qty in Nos', 'Qty in Cases/Bags']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(r'[₹,]', '', regex=True)
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            else:
                df[col] = 0

        df['Posting Date'] = pd.to_datetime(df['Posting Date'], errors='coerce')
        df.dropna(subset=['Posting Date'], inplace=True)
        
        if 'LineStatus' in df.columns:
            status_map = {'O': 'Open', 'C': 'Closed'}
            df['StatusDescription'] = df['LineStatus'].str.strip().str.upper().map(status_map).fillna('Unknown')
        else:
            df['StatusDescription'] = 'Open'
            
        return df
    except Exception as e:
        st.error(f"Error: CSV file ah load panrathula problem: {e}")
        st.stop()

df = load_data(FILE_NAME)

if df.empty:
    st.warning("No valid posting date records available in the dataset.")
    st.stop()

latest_available_date = df['Posting Date'].dt.date.max()

# --- SIDEBAR FILTERS ---
st.sidebar.header("Filter Options")

# Overdue calculation ku thevayana lead time
lead_time_days = st.sidebar.number_input("Lead Time for Delivery (in days)", min_value=1, max_value=90, value=15)

min_date = df['Posting Date'].min().date()
max_date = df['Posting Date'].max().date()
date_range = st.sidebar.date_input("Select Posting Date Range", value=(min_date, max_date), min_value=min_date, max_value=max_date)
start_date, end_date = date_range

# single-selection filters with "All" option
all_bp_names = sorted(df['BP Name'].unique())
customer_options = ["All"] + all_bp_names
selected_bp = st.sidebar.selectbox("Select Customer", options=customer_options, index=0)

all_item_names = sorted(df['ItemName'].unique())
product_options = ["All"] + all_item_names
selected_item = st.sidebar.selectbox("Select Product Category", options=product_options, index=0)

# --- DATA FILTERING ---
df_filtered = df[
    (df['Posting Date'].dt.date >= start_date) &
    (df['Posting Date'].dt.date <= end_date)
]
if selected_bp != "All":
    df_filtered = df_filtered[df_filtered['BP Name'] == selected_bp]
if selected_item != "All":
    df_filtered = df_filtered[df_filtered['ItemName'] == selected_item]

# --- CALCULATIONS ---
if not df_filtered.empty:
    # Sub-dataframes for easier calculation
    df_open = df_filtered[df_filtered['StatusDescription'] == 'Open']
    df_closed = df_filtered[df_filtered['StatusDescription'] == 'Closed']

    # Overdue Calculation
    # use latest available date in full dataset as 'today'
    today = latest_available_date
    df_open['DueDate'] = df_open['Posting Date'].dt.date + timedelta(days=lead_time_days)
    df_overdue = df_open[df_open['DueDate'] <= today]

    # KPI Values
    total_po_value = df_filtered['LineTotalBeforeTax'].sum()
    total_po_count = df_filtered['Document Number'].nunique()
    total_po_qty = df_filtered['Qty in Nos'].sum()

    open_po_value = df_open['LineTotalBeforeTax'].sum()
    open_po_count = df_open['Document Number'].nunique()
    open_po_qty = df_open['Qty in Nos'].sum()

    closed_po_value = df_closed['LineTotalBeforeTax'].sum()
    closed_po_count = df_closed['Document Number'].nunique()
    closed_po_qty = df_closed['Qty in Nos'].sum()

    overdue_po_value = df_overdue['LineTotalBeforeTax'].sum()
    overdue_po_count = df_overdue['Document Number'].nunique()
    overdue_po_qty = df_overdue['Qty in Nos'].sum()
else:
    # Data illana ella values um 0
    today = latest_available_date
    df_open = pd.DataFrame(columns=df.columns)
    df_closed = pd.DataFrame(columns=df.columns)
    total_po_value, total_po_count, total_po_qty = 0, 0, 0
    open_po_value, open_po_count, open_po_qty = 0, 0, 0
    closed_po_value, closed_po_count, closed_po_qty = 0, 0, 0
    overdue_po_value, overdue_po_count, overdue_po_qty = 0, 0, 0
    df_overdue = pd.DataFrame()
    # create empty daywise table to avoid errors later
    daywise = pd.DataFrame()


# --- MAIN DASHBOARD DISPLAY ---
st.title("📈 Purchase Order Performance Dashboard")
st.caption(f"Today is set to latest available dataset date: {today.strftime('%d-%b-%Y')}")

# Pre-calculate values needed for both sections
open_upto_today = df_open[df_open['Posting Date'].dt.date <= today]
open_count_today = open_upto_today['Document Number'].nunique()
open_value_today = open_upto_today['LineTotalBeforeTax'].sum()
open_qty_today = open_upto_today['Qty in Nos'].sum()

# Helper to generate HTML cards
def create_kpi_card(label, value, icon, status_class=""):
    html = f"""
    <div class="kpi-card {status_class}">
        <div style="font-size: 2.5em; margin-bottom: 0.5em;">{icon}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-label">{label}</div>
    </div>
    """
    return html

# --- Overdue focus section (FIRST) ---

# Display reference date info in styled box
st.markdown("""
<div style="background: linear-gradient(135deg, #fff5f5 0%, #ffe8e8 100%); padding: 1.5em; border-radius: 8px; border-left: 5px solid #d13438; margin: 1em 0;">
    <div style="font-size: 0.95em; color: #666; margin-bottom: 0.5em;"><strong>Data Reference Date:</strong> {}</div>
    <div style="font-size: 0.95em; color: #666;"><strong>Open POs up to Reference Date:</strong> {} POs | Value: {} | Qty: {}</div>
</div>
""".format(today.strftime('%d-%b-%Y'), open_count_today, format_inr(open_value_today), f"{open_qty_today:,.0f}"), unsafe_allow_html=True)

if not df_overdue.empty:
    # metrics for overdue up to reference date
    overdue_upto_today = df_overdue[df_overdue['DueDate'] <= today]
    today_value = overdue_upto_today['LineTotalBeforeTax'].sum()
    today_count = overdue_upto_today['Document Number'].nunique()
    days_overdue = df_overdue['DueDate'].nunique()
    
    # Calculate max days overdue
    df_overdue['DaysOverdue_Calc'] = df_overdue['DueDate'].apply(lambda d: (today - d).days)
    max_days_overdue = df_overdue['DaysOverdue_Calc'].max()
    
    col_a, col_b, col_c, col_d = st.columns(4, gap="small")
    with col_a:
        st.markdown(create_kpi_card("Overdue Value Today", format_inr(today_value), "💱", "status-card-critical"), unsafe_allow_html=True)
    with col_b:
        st.markdown(create_kpi_card("Overdue Count Today", f"{today_count}", "🗏", "status-card-critical"), unsafe_allow_html=True)
    with col_c:
        st.markdown(create_kpi_card("Distinct Overdue Days", f"{days_overdue}", "📅", "status-card-warning"), unsafe_allow_html=True)
    with col_d:
        st.markdown(create_kpi_card("Max Days Overdue", f"{max_days_overdue}", "📍", "status-card-critical"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    overdue_summary = df_overdue.groupby('DueDate').agg(
        Value=('LineTotalBeforeTax','sum'),
        Count=('Document Number','nunique')
    ).reset_index()
    overdue_summary['DueDate'] = pd.to_datetime(overdue_summary['DueDate']).dt.date
    overdue_summary['DaysOverdue'] = overdue_summary['DueDate'].apply(lambda d: (today - d).days)
    overdue_summary['Value'] = overdue_summary['Value'].apply(format_inr)
    st.dataframe(overdue_summary, use_container_width=True)
    with st.expander("See individual overdue records"):
        styled = df_overdue[['Posting Date', 'DueDate', 'Document Number', 'BP Name', 'ItemName', 'LineTotalBeforeTax']].copy()
        styled['DueDate'] = pd.to_datetime(styled['DueDate']).dt.date
        styled['DaysOverdue'] = styled['DueDate'].apply(lambda d: (today - d).days)
        styled['LineTotalBeforeTax'] = styled['LineTotalBeforeTax'].apply(format_inr)
        st.dataframe(styled, use_container_width=True)
else:
    st.info("Excellent! No overdue POs found for the selected filters.")

st.markdown("---")

# --- KPI Section (collapsed) ---
with st.expander("📊 Overall Summary (click to expand)", expanded=False):
    
    # Row 1: Total count, Total value, Total qty, Open count
    r1c1, r1c2, r1c3, r1c4 = st.columns(4, gap="small")

    with r1c1:
        st.markdown(create_kpi_card("Total PO Count", f"{total_po_count}", "🧾"), unsafe_allow_html=True)

    with r1c2:
        st.markdown(create_kpi_card("Total PO Value", format_inr(total_po_value), "💰"), unsafe_allow_html=True)

    with r1c3:
        st.markdown(create_kpi_card("Total Qty", f"{total_po_qty:,.0f}", "📦"), unsafe_allow_html=True)

    with r1c4:
        st.markdown(create_kpi_card("Open PO Count", f"{open_po_count}", "📂", "status-card-good"), unsafe_allow_html=True)
    
    # Row 2: Open value, Open qty, Closed count, Closed value
    r2c1, r2c2, r2c3, r2c4 = st.columns(4, gap="small")

    with r2c1:
        st.markdown(create_kpi_card("Open PO Value", format_inr(open_po_value), "📤", "status-card-good"), unsafe_allow_html=True)

    with r2c2:
        st.markdown(create_kpi_card("Open Qty", f"{open_po_qty:,.0f}", "🎯", "status-card-good"), unsafe_allow_html=True)

    with r2c3:
        st.markdown(create_kpi_card("Closed PO Count", f"{closed_po_count}", "✅"), unsafe_allow_html=True)

    with r2c4:
        st.markdown(create_kpi_card("Closed PO Value", format_inr(closed_po_value), "✔️"), unsafe_allow_html=True)
    
    # Row 3: Overdue count, Overdue value, Overdue qty, Closed qty
    r3c1, r3c2, r3c3, r3c4 = st.columns(4, gap="small")

    with r3c1:
        st.markdown(create_kpi_card("Overdue PO Count", f"{overdue_po_count}", "⏳", "status-card-critical"), unsafe_allow_html=True)

    with r3c2:
        st.markdown(create_kpi_card("Overdue PO Value", format_inr(overdue_po_value), "🚨", "status-card-critical"), unsafe_allow_html=True)
    
    with r3c3:
        st.markdown(create_kpi_card("Overdue Qty", f"{overdue_po_qty:,.0f}", "⚠️", "status-card-critical"), unsafe_allow_html=True)

    with r3c4:
        st.markdown(create_kpi_card("Closed PO Qty", f"{closed_po_qty:,.0f}", "📊"), unsafe_allow_html=True)

st.markdown("---")

# --- Tabs for Analysis Sections ---
tab1, tab2, tab3, tab4 = st.tabs([
    "📅 Product Category Daily",
    "👥 Customer Summary",
    "📦 Product Summary",
    "📋 Full Data"
])

with tab1:
    st.subheader("Product Category-wise Open PO Day-wise")
    if not df_open.empty:
        pivot = df_open.groupby([df_open['Posting Date'].dt.date, 'ItemName'])['LineTotalBeforeTax'].sum().unstack(fill_value=0)
        # format each cell with INR formatting using map
        formatted = pivot.copy()
        formatted = formatted.apply(lambda col: col.map(format_inr))
        st.dataframe(formatted, use_container_width=True)
    else:
        st.info("No open POs to display.")

with tab2:
    st.subheader("Customer-wise Summary")
    if not df_filtered.empty:
        summary_customer = df_filtered.groupby('BP Name').agg(
            Total_Value=('LineTotalBeforeTax', 'sum'),
            Total_POs=('Document Number', 'nunique')
        ).reset_index()
        
        open_summary_customer = df_open.groupby('BP Name').agg(Open_Value=('LineTotalBeforeTax', 'sum')).reset_index()
        overdue_summary_customer = df_overdue.groupby('BP Name').agg(Overdue_Value=('LineTotalBeforeTax', 'sum')).reset_index()

        # Merging the summaries
        summary_customer = pd.merge(summary_customer, open_summary_customer, on='BP Name', how='left').fillna(0)
        summary_customer = pd.merge(summary_customer, overdue_summary_customer, on='BP Name', how='left').fillna(0)
        
        # format values for display
        for col in ['Total_Value', 'Open_Value', 'Overdue_Value']:
            summary_customer[col] = summary_customer[col].apply(format_inr)

        st.dataframe(summary_customer, use_container_width=True)
    else:
        st.info("No data to summarize.")

with tab3:
    st.subheader("Product Category-wise Summary")
    if not df_filtered.empty:
        summary_product = df_filtered.groupby('ItemName').agg(
            Total_Value=('LineTotalBeforeTax', 'sum'),
            Total_Nos=('Qty in Nos', 'sum')
        ).reset_index()

        open_summary_product = df_open.groupby('ItemName').agg(Open_Value=('LineTotalBeforeTax', 'sum')).reset_index()
        overdue_summary_product = df_overdue.groupby('ItemName').agg(Overdue_Value=('LineTotalBeforeTax', 'sum')).reset_index()

        summary_product = pd.merge(summary_product, open_summary_product, on='ItemName', how='left').fillna(0)
        summary_product = pd.merge(summary_product, overdue_summary_product, on='ItemName', how='left').fillna(0)

        for col in ['Total_Value', 'Open_Value', 'Overdue_Value']:
            summary_product[col] = summary_product[col].apply(format_inr)

        st.dataframe(summary_product, use_container_width=True)
    else:
        st.info("No data to summarize.")

with tab4:
    st.subheader("Full Filtered Data (Formatted)")
    if not df_filtered.empty:
        full = df_filtered.copy()
        if 'LineTotalBeforeTax' in full.columns:
            full['LineTotalBeforeTax'] = full['LineTotalBeforeTax'].apply(format_inr)
        st.dataframe(full, use_container_width=True)
    else:
        st.info("No records to show.")
