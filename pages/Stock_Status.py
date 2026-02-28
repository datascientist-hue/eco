import streamlit as st
import pandas as pd
import altair as alt
from data_loader import load_csv_from_ftp

# -----------------------------
# Page Config
# -----------------------------
st.set_page_config(page_title="Stock Status Dashboard", layout="wide")

# Custom CSS for professional blue sidebar
st.markdown("""
<style>
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f2f63 0%, #0b2550 100%);
    border-right: 1px solid rgba(255, 255, 255, 0.14);
}
[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
    padding-top: 1rem;
}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div {
    color: #FFFFFF;
}
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
    color: #FFFFFF;
    font-weight: 700;
    letter-spacing: 0.2px;
}
[data-testid="stSidebar"] label {
    color: #e9f1ff !important;
    font-weight: 600 !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background-color: rgba(255, 255, 255, 0.14) !important;
    border: 1px solid rgba(255, 255, 255, 0.35) !important;
    border-radius: 8px !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] * {
    color: #ffffff !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] svg {
    fill: #ffffff !important;
}
[data-testid="stSidebar"] hr {
    border-color: rgba(255, 255, 255, 0.22);
}
</style>
""", unsafe_allow_html=True)

st.title("📦 Stock Status Dashboard")

# -----------------------------
# Load Data
# -----------------------------
FILE_NAME = "Stock_Status.csv"

@st.cache_data
def load_data(file_name):
    """Read the CSV file with a safe encoding and normalize column names.

    The function first attempts utf-8 and falls back to latin-1 on failure. After
    loading we rename any "Item No." column so downstream code can rely on a
    consistent name; doing this inside the cached function ensures the cached
    result already has the correct columns.
    """
    try:
        df = load_csv_from_ftp(file_name, encoding="utf-8")
    except UnicodeDecodeError:
        # fallback for files with non-UTF-8 characters (e.g. Windows-1252)
        df = load_csv_from_ftp(file_name, encoding="latin-1")

    # normalize column names once
    if "Item No." in df.columns:
        df.rename(columns={"Item No.": "Item No"}, inplace=True)

    # convert numeric-like columns to proper numbers (strip commas, stray text)
    for col in ["Cost/Unit", "Inventory Value", "Quantity"]:
        if col in df.columns:
            # remove commas used as thousands separators and any unwanted chars
            df[col] = (
                df[col]
                .astype(str)
                .str.replace(",", "", regex=False)
                .str.replace(r"[^0-9.\-]", "", regex=True)
            )
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df

df = load_data(FILE_NAME)

# -----------------------------
# Sidebar Filters
# -----------------------------
st.sidebar.header("🔍 Filters")

# single-select filters: user can choose a specific value or "All" to include everything
warehouse_options = ["All"] + sorted(df["Warehouse Code"].unique())
warehouse_filter = st.sidebar.selectbox("Select Warehouse Code", warehouse_options)

group_options = ["All"] + sorted(df["Group Name"].unique())
group_filter = st.sidebar.selectbox(
    "Select Group Name (Product Category)",
    group_options
)

# apply filters sequentially to avoid scalar boolean masks
filtered_df = df
if warehouse_filter != "All":
    filtered_df = filtered_df[filtered_df["Warehouse Code"] == warehouse_filter]
if group_filter != "All":
    filtered_df = filtered_df[filtered_df["Group Name"] == group_filter]

# -----------------------------
# KPI CARDS
# -----------------------------
# helper to format numbers in Indian metric (Crore, Lakh)
def _indian_format(x):
    try:
        x = float(x)
    except Exception:
        return ""
    absx = abs(x)
    if absx >= 1e7:  # crore (10 million)
        return f"{x/1e7:.2f} Cr"
    if absx >= 1e5:  # lakh (1 00,000)
        return f"{x/1e5:.2f} L"
    if absx >= 1e3:  # thousand
        return f"{x/1e3:.2f}K"
    return f"{x:,.2f}"

# helper to format currency in Indian Rupees with abbreviated format (Cr, L, K)
def _format_indian_currency(x):
    """Format numbers in Indian currency style with ₹ symbol and abbreviated format"""
    try:
        x = float(x)
    except Exception:
        return ""
    
    # Handle negative values
    is_negative = x < 0
    x = abs(x)
    
    # Use abbreviated format for large values
    if x >= 1e7:  # crore (10 million)
        return f"₹ {x/1e7:.2f} Cr" if not is_negative else f"-₹ {x/1e7:.2f} Cr"
    if x >= 1e5:  # lakh (100,000)
        return f"₹ {x/1e5:.2f} L" if not is_negative else f"-₹ {x/1e5:.2f} L"
    if x >= 1e3:  # thousand
        return f"₹ {x/1e3:.2f}K" if not is_negative else f"-₹ {x/1e3:.2f}K"
    
    # For smaller values, show with 2 decimal places
    result = f"₹ {x:.2f}"
    if is_negative:
        result = f"-{result}"
    
    return result

# calculate
total_qty = filtered_df["Quantity"].sum()
avg_cost = filtered_df["Cost/Unit"].mean()
total_value = filtered_df["Inventory Value"].sum()


col1, col2, col3 = st.columns(3)

col1.metric("📦 Total Quantity", _indian_format(total_qty))
col2.metric("💰 Avg Cost / Unit", _format_indian_currency(avg_cost))
col3.metric("🏷️ Total Inventory Value", _format_indian_currency(total_value))

st.divider()

# compute summary tables once for reuse
warehouse_table = (
    filtered_df
    .groupby("Warehouse Code", as_index=False)
    .agg({
        "Quantity": "sum",
        "Inventory Value": "sum"
    })
)

group_table = (
    filtered_df
    .groupby("Group Name", as_index=False)
    .agg({
        "Quantity": "sum",
        "Inventory Value": "sum"
    })
)

# format numeric columns for display (avoid extremely long numbers)
def _format_nums(df, cols):
    df = df.copy()
    for c in cols:
        if c in df:
            if c == "Inventory Value":
                df[c] = df[c].map(lambda x: _format_indian_currency(x))
            else:
                df[c] = df[c].map(lambda x: f"{x:,.2f}")
    return df

warehouse_display = _format_nums(warehouse_table, ["Quantity", "Inventory Value"])
group_display = _format_nums(group_table, ["Quantity", "Inventory Value"])

# bar chart with descriptive labels
st.subheader("📊 Inventory Value by Product Category")
chart = alt.Chart(group_table).mark_bar().encode(
    x=alt.X('Group Name', title='Product Category', sort='-y'),
    y=alt.Y('Inventory Value', title='Inventory Value')
)
st.altair_chart(chart, use_container_width=True)

# dropdown to choose which table to display
report_choice = st.selectbox("Select report", [
    "Product Category (Group Name) Wise Summary",
    "Top 5 High Inventory Value Products",
    "Low Stock Alert (Quantity < 10)"
])

# prepare data for the reports
if report_choice == "Product Category (Group Name) Wise Summary":
    st.table(group_display)
elif report_choice == "Top 5 High Inventory Value Products":
    top_products = (
        filtered_df
        .sort_values("Inventory Value", ascending=False)
        .head(5)[[
            "Item No", "Item Description",
            "Group Name", "Inventory Value"
        ]]
    )
    if not top_products.empty:
        top_products = top_products.copy()
        top_products["Inventory Value"] = top_products["Inventory Value"].map(lambda x: _format_indian_currency(x))
    st.subheader("🔥 Top 5 High Inventory Value Products")
    st.table(top_products)
else:  # low stock
    low_stock = filtered_df[filtered_df["Quantity"] < 10]
    st.subheader("⚠️ Low Stock Alert (Quantity < 10)")
    if low_stock.empty:
        st.success("✅ No Low Stock Items")
    else:
        st.dataframe(
            low_stock[[
                "Warehouse Code",
                "Item No",
                "Item Description",
                "Quantity"
            ]],
            use_container_width=True
        )


# -----------------------------
# Export & Full Data View
# provide download button for filtered dataset
csv = filtered_df.to_csv(index=False).encode("utf-8")
st.download_button(
    label="📥 Download Filtered Data as CSV",
    data=csv,
    file_name="stock_data.csv",
    mime="text/csv",
)

# -----------------------------
# Full Data View
# -----------------------------
with st.expander("📄 View Full Stock Data"):
    st.dataframe(filtered_df, use_container_width=True)