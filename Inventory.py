import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from data_loader import load_csv_from_ftp

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Inventory Ageing Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============ PROFESSIONAL POWER BI–STYLE CSS ============
st.markdown("""
<style>
    /* ===== ROOT STYLING ===== */
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #ffffff;
    }
    
    /* ===== MAIN CONTENT AREA ===== */
    [data-testid="stMainBlockContainer"] {
        padding: 2.5rem 2rem;
        background-color: #fafbfc;
        max-width: 1600px;
        margin: 0 auto;
    }
    
    /* ===== SIDEBAR STYLING ===== */
    [data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid #e5e7eb;
        padding: 2rem 0;
    }
    
    [data-testid="stSidebar"] [data-testid="stVerticalBlockBelowGlueContainer"] {
        padding: 0 1.5rem;
    }
    
    /* Sidebar headings */
    [data-testid="stSidebar"] h2 {
        color: #111827 !important;
        font-size: 1.2rem !important;
        font-weight: 700 !important;
        margin-bottom: 1.5rem !important;
        border-bottom: 2px solid #f0f1f3 !important;
        padding-bottom: 1rem !important;
    }
    
    /* Sidebar labels */
    [data-testid="stSidebar"] label {
        color: #374151 !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        margin-bottom: 0.6rem !important;
    }
    
    /* Sidebar selectbox */
    [data-testid="stSidebar"] [data-testid="stSelectbox"] > div > div {
        background-color: #f9fafb !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 6px !important;
    }
    
    /* ===== HEADER SECTION ===== */
    .dashboard-header {
        text-align: left;
        margin-bottom: 2rem;
        padding-bottom: 1.5rem;
    }
    
    .dashboard-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #111827;
        margin-bottom: 0.3rem;
        letter-spacing: -0.5px;
    }
    
    .dashboard-subtitle {
        font-size: 0.95rem;
        color: #6b7280;
        font-weight: 500;
    }
    
    /* ===== KPI CARDS SECTION ===== */
    .kpi-container {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 1rem;
        margin-bottom: 2rem;
    }
    
    .kpi-card {
        background: white;
        border-radius: 8px;
        padding: 1.6rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04);
        border-top: 3px solid;
        transition: all 0.2s ease;
        min-height: 130px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    .kpi-card:hover {
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .kpi-label {
        font-size: 0.8rem;
        font-weight: 700;
        color: #6b7280;
        margin-bottom: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.8px;
    }
    
    .kpi-value {
        font-size: 1.8rem;
        font-weight: 700;
        margin-bottom: 0;
        color: #111827;
    }
    
    /* KPI Color Variants - Top Border Only */
    .kpi-primary { border-top-color: #3b82f6; }
    .kpi-danger { border-top-color: #ef4444; }
    .kpi-info { border-top-color: #06b6d4; }
    .kpi-warning { border-top-color: #f97316; }
    .kpi-secondary { border-top-color: #dc2626; }
    
    /* Value highlights only */
    .kpi-primary .kpi-value { color: #3b82f6; }
    .kpi-danger .kpi-value { color: #dc2626; }
    .kpi-info .kpi-value { color: #0891b2; }
    .kpi-warning .kpi-value { color: #ea580c; }
    .kpi-secondary .kpi-value { color: #991b1b; }
    
    /* ===== SECTION HEADERS ===== */
    .section-header {
        font-size: 1.2rem;
        font-weight: 700;
        color: #111827;
        margin: 2.5rem 0 1.5rem 0;
        padding: 0;
        border-bottom: none;
    }
    
    /* ===== CHARTS & CARDS CONTAINER ===== */
    .chart-container {
        background: white;
        border-radius: 8px;
        padding: 1.5rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04);
        margin-bottom: 2rem;
    }
    
    /* ===== TABS STYLING ===== */
    [data-testid="stTabs"] [role="tablist"] {
        background-color: transparent;
        border-bottom: 1px solid #e5e7eb;
        gap: 2rem;
    }
    
    [data-testid="stTabs"] [role="tab"] {
        font-weight: 600;
        color: #6b7280;
        padding: 0.8rem 1.2rem;
        border-radius: 0;
        border-bottom: 2px solid transparent;
        font-size: 0.95rem;
    }
    
    [data-testid="stTabs"] [role="tab"][aria-selected="true"] {
        color: #111827;
        border-bottom-color: #3b82f6;
    }
    
    [data-testid="stTabs"] [role="tab"]:hover {
        color: #111827;
    }
    
    /* ===== DATAFRAME STYLING ===== */
    [data-testid="dataframe"] {
        border-collapse: collapse !important;
    }
    
    /* ===== FILTER CONTROLS ===== */
    [data-testid="stSelectbox"] > div > div {
        background-color: #f9fafb !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 6px !important;
    }
    
    [data-testid="stTextInput"] > div > div > input {
        background-color: #f9fafb !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 6px !important;
        font-size: 0.95rem !important;
        color: #111827 !important;
    }
    
    [data-testid="stTextInput"] > div > div > input::placeholder {
        color: #9ca3af !important;
    }
    
    /* ===== RESPONSIVE ADJUSTMENTS ===== */
    @media (max-width: 1200px) {
        .kpi-container {
            grid-template-columns: repeat(3, 1fr);
        }
    }
    
    @media (max-width: 768px) {
        .kpi-container {
            grid-template-columns: repeat(2, 1fr);
        }
        .dashboard-title {
            font-size: 1.8rem;
        }
    }
    
    @media (max-width: 480px) {
        .kpi-container {
            grid-template-columns: 1fr;
        }
        .dashboard-title {
            font-size: 1.5rem;
        }
        [data-testid="stMainBlockContainer"] {
            padding: 1.5rem 1rem;
        }
    }
    
</style>
""", unsafe_allow_html=True)

# ============ DASHBOARD HEADER ============
st.markdown("""
<div class="dashboard-header">
    <div class="dashboard-title">📦 Inventory Ageing Dashboard</div>
    <div class="dashboard-subtitle">Real-time inventory analysis • Business insights • Performance metrics</div>
</div>
""", unsafe_allow_html=True)

# ---------------- LOAD DATA ----------------
df = load_csv_from_ftp("Inventory_Ageing_Report.csv", encoding="latin-1")

# Rename Item Description as Product Name
df.rename(columns={"Item Description": "Product Name"}, inplace=True)

# Convert numeric columns to numeric type
numeric_cols = [
    "In Stock", "Inventory Value",
    "0-15Qty", "0-15Value",
    "16-30Qty", "16-30Value",
    "31-60Qty", "31-60Value",
    "61-90Qty", "61-90Value",
    "91-180Qty", "91-180Value",
    "181-360Qty", "181-360Value",
    "361-720Qty", "361-720Value",
    "721+Qty", "721+DaysValue"
]
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# ---------------- NUMBER FORMATTING HELPERS ----------------
def human_format(num):
    try:
        n = float(num)
    except Exception:
        return "-"
    neg = n < 0
    n_abs = abs(n)
    # Indian short-scale formatting: Crore (Cr), Lakh (L), Thousand (K)
    if n_abs >= 1e7:  # crore
        s = f"{n_abs/1e7:.2f} Cr"
    elif n_abs >= 1e5:  # lakh
        s = f"{n_abs/1e5:.2f} L"
    elif n_abs >= 1e3:  # thousand
        s = f"{n_abs/1e3:.2f}K"
    else:
        # show rupee amounts with two decimals for smaller numbers
        s = f"{n_abs:,.2f}"
    return f"-{s}" if neg else s

def human_currency(num):
    if pd.isna(num):
        return "-"
    return f"₹ {human_format(num)}"

# ---------------- SIDEBAR FILTERS (GLOBAL) ----------------
st.sidebar.header("🏭 Main Filters")

# provide 'All' option for both dropdowns
all_wh = ["All"] + df["Warehouse Code"].unique().tolist()
warehouse_filter = st.sidebar.selectbox(
    "Warehouse",
    all_wh,
    index=0
)

if warehouse_filter == "All":
    prod_options = ["All"] + df["Product Name"].unique().tolist()
else:
    prod_options = ["All"] + df[df["Warehouse Code"] == warehouse_filter]["Product Name"].unique().tolist()

product_filter = st.sidebar.selectbox(
    "Product Name",
    prod_options,
    index=0
)

# apply filters
if warehouse_filter == "All":
    df_filtered = df.copy()
else:
    df_filtered = df[df["Warehouse Code"] == warehouse_filter]

if product_filter != "All":
    df_filtered = df_filtered[df_filtered["Product Name"] == product_filter]

# ---------------- KPI CALCULATIONS ----------------
total_inventory_value = df_filtered["Inventory Value"].sum()
total_stock_qty = df_filtered["In Stock"].sum()
total_items = df_filtered["Item No."].nunique()

slow_moving_value = (
    df_filtered["91-180Value"].sum() +
    df_filtered["181-360Value"].sum() +
    df_filtered["361-720Value"].sum() +
    df_filtered["721+DaysValue"].sum()
)

dead_stock_value = (
    df_filtered["361-720Value"].sum() +
    df_filtered["721+DaysValue"].sum()
)

# ============ KPI DISPLAY FUNCTION ============
def display_kpi_cards():
    """Display KPI cards in a professional grid layout (compact numbers)."""
    inv = human_currency(total_inventory_value)
    stock = human_format(total_stock_qty)
    items = f"{total_items:,}"
    slow = human_currency(slow_moving_value)
    dead = human_currency(dead_stock_value)

    st.markdown(f"""
    <div class="kpi-container">
        <div class="kpi-card kpi-primary">
            <div class="kpi-label">💰 Total Inventory Value</div>
            <div class="kpi-value">{inv}</div>
        </div>
        <div class="kpi-card kpi-danger">
            <div class="kpi-label">📦 Total In Stock Qty</div>
            <div class="kpi-value">{stock}</div>
        </div>
        <div class="kpi-card kpi-info">
            <div class="kpi-label">🏷️ Total Items</div>
            <div class="kpi-value">{items}</div>
        </div>
        <div class="kpi-card kpi-warning">
            <div class="kpi-label">⏰ Slow Moving (91+)</div>
            <div class="kpi-value">{slow}</div>
        </div>
        <div class="kpi-card kpi-secondary">
            <div class="kpi-label">💀 Dead Stock (361+)</div>
            <div class="kpi-value">{dead}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

display_kpi_cards()

st.markdown('<div class="section-header">📊 Inventory Ageing – Value Overview</div>', unsafe_allow_html=True)

ageing_value = {
    "0-15": df_filtered["0-15Value"].sum(),
    "16-30": df_filtered["16-30Value"].sum(),
    "31-60": df_filtered["31-60Value"].sum(),
    "61-90": df_filtered["61-90Value"].sum(),
    "91-180": df_filtered["91-180Value"].sum(),
    "181-360": df_filtered["181-360Value"].sum(),
    "361-720": df_filtered["361-720Value"].sum(),
    "721+": df_filtered["721+DaysValue"].sum(),
}

ageing_df = pd.DataFrame.from_dict(
    ageing_value, orient="index", columns=["Inventory Value"]
)

# Create professional minimal chart
fig, ax = plt.subplots(figsize=(12, 5.5), facecolor='white', edgecolor='none')
ax.set_facecolor('#ffffff')
colors = ['#10b981' if i < 2 else '#f59e0b' if i < 4 else '#ef4444' for i in range(len(ageing_df))]
ageing_df.plot(kind="bar", ax=ax, legend=False, color=colors, width=0.68)
ax.set_xlabel("Ageing Bucket", fontsize=11, fontweight='600', color='#374151')
ax.set_ylabel("Inventory Value (₹)", fontsize=11, fontweight='600', color='#374151')
ax.set_title("", fontsize=14, fontweight='bold', pad=20)
ax.grid(True, alpha=0.08, linestyle='-', axis='y', color='#d1d5db', linewidth=0.5)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color('#e5e7eb')
ax.spines['bottom'].set_color('#e5e7eb')
ax.spines['left'].set_linewidth(0.5)
ax.spines['bottom'].set_linewidth(0.5)
# Add value labels on top of each bar
for p in ax.patches:
    height = p.get_height()
    if height > 0:
        ax.annotate(human_currency(height),
                    (p.get_x() + p.get_width() / 2, height),
                    ha='center', va='bottom', fontsize=9, fontweight='600', color='#111827')
ax.tick_params(colors='#374151', labelsize=10)
plt.xticks(rotation=45, ha='right', fontsize=10, color='#374151')
plt.yticks(fontsize=10, color='#374151')
plt.tight_layout()

# Display in styled container
st.markdown('<div class="chart-container">', unsafe_allow_html=True)
st.pyplot(fig)
st.markdown('</div>', unsafe_allow_html=True)

# ============ SUMMARY TABLES ============
st.markdown('<div class="section-header">📋 Summary Tables</div>', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["By Product", "By Warehouse"])

with tab1:
    prod_table = (
        df_filtered.groupby("Product Name")["Inventory Value"]
        .sum()
        .reset_index()
        .sort_values("Inventory Value", ascending=False)
    )
    # apply gradient styling with professional colors
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.dataframe(
        prod_table.style
        .background_gradient(subset=["Inventory Value"], cmap="Blues")
        .format({"Inventory Value": lambda x: human_currency(x)}),
        use_container_width=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    wh_table = (
        df_filtered.groupby("Warehouse Code")["Inventory Value"]
        .sum()
        .reset_index()
        .sort_values("Inventory Value", ascending=False)
    )
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.dataframe(
        wh_table.style
        .background_gradient(subset=["Inventory Value"], cmap="Greens")
        .format({"Inventory Value": lambda x: human_currency(x)}),
        use_container_width=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="section-header">🔝 Top 10 High Value Old Stocks (Age > 180 Days)</div>', unsafe_allow_html=True)

old_stock_rows = []

for _, row in df_filtered.iterrows():
    if row["181-360Value"] > 0:
        old_stock_rows.append([
            row["Item No."],
            row["Product Name"],
            row["Warehouse Code"],
            "181-360 Days",
            row["181-360Value"]
        ])
    if row["361-720Value"] > 0:
        old_stock_rows.append([
            row["Item No."],
            row["Product Name"],
            row["Warehouse Code"],
            "361-720 Days",
            row["361-720Value"]
        ])
    if row["721+DaysValue"] > 0:
        old_stock_rows.append([
            row["Item No."],
            row["Product Name"],
            row["Warehouse Code"],
            "721+ Days",
            row["721+DaysValue"]
        ])

old_stock_df = pd.DataFrame(
    old_stock_rows,
    columns=[
        "Item No",
        "Item Description",
        "Warehouse",
        "Age Bucket",
        "Inventory Value"
    ]
)

top10_old_stock = old_stock_df.sort_values(
    by="Inventory Value", ascending=False
).head(10)

st.markdown('<div class="chart-container">', unsafe_allow_html=True)
st.dataframe(
    top10_old_stock.style
    .background_gradient(subset=["Inventory Value"], cmap="Reds")
    .format({"Inventory Value": lambda x: human_currency(x)}),
    use_container_width=True
)
st.markdown('</div>', unsafe_allow_html=True)

# ---------------- AGE BUCKET COLUMN FOR DETAIL TABLE ----------------
def assign_age_bucket(row):
    if row["721+Qty"] > 0:
        return "721+ Days"
    elif row["361-720Qty"] > 0:
        return "361-720 Days"
    elif row["181-360Qty"] > 0:
        return "181-360 Days"
    elif row["91-180Qty"] > 0:
        return "91-180 Days"
    elif row["61-90Qty"] > 0:
        return "61-90 Days"
    elif row["31-60Qty"] > 0:
        return "31-60 Days"
    elif row["16-30Qty"] > 0:
        return "16-30 Days"
    else:
        return "0-15 Days"

df_filtered["Age Bucket"] = df_filtered.apply(assign_age_bucket, axis=1)

st.markdown('---')
st.markdown('<div class="section-header">📋 Inventory Ageing – Detailed Table</div>', unsafe_allow_html=True)

st.markdown('<div class="chart-container">', unsafe_allow_html=True)
f1, f2, f3 = st.columns(3, gap="medium")

with f1:
    wh_options = ["All"] + df_filtered["Warehouse Code"].unique().tolist()
    wh_dt = st.selectbox(
        "🏢 Warehouse",
        wh_options,
        index=0
    )

with f2:
    age_options = ["All"] + df_filtered["Age Bucket"].unique().tolist()
    age_dt = st.selectbox(
        "📅 Age Bucket",
        age_options,
        index=0
    )

with f3:
    item_search = st.text_input("🔍 Item No. Search")

st.markdown('</div>', unsafe_allow_html=True)

detail_df = df_filtered.copy()
if wh_dt != "All":
    detail_df = detail_df[detail_df["Warehouse Code"] == wh_dt]
if age_dt != "All":
    detail_df = detail_df[detail_df["Age Bucket"] == age_dt]

if item_search:
    detail_df = detail_df[
        detail_df["Item No."].astype(str).str.contains(item_search, case=False)
    ]

# ---------------- FINAL DETAIL TABLE ----------------
# apply colour styling based on Age Bucket
bucket_colors = {
    "0-15 Days": "#d4edda",  # greenish
    "16-30 Days": "#fff3cd",  # yellow
    "31-60 Days": "#ffe5b4",  # light orange
    "61-90 Days": "#ffd1cc",  # peach
    "91-180 Days": "#f8d7da",  # pinkish
    "181-360 Days": "#f5c6cb",  # light red
    "361-720 Days": "#f1b0b7",  # darker red
    "721+ Days": "#f8d7da"   # same as 91-180
}

def color_bucket(val):
    return f"background-color: {bucket_colors.get(val, '')}"

detail_cols = [
    "Item No.",
    "Product Name",
    "Warehouse Code",
    "State",
    "In Stock",
    "Inventory Value",
    "0-15Qty", "0-15Value",
    "16-30Qty", "16-30Value",
    "31-60Qty", "31-60Value",
    "61-90Qty", "61-90Value",
    "91-180Qty", "91-180Value",
    "181-360Qty", "181-360Value",
    "361-720Qty", "361-720Value",
    "721+Qty", "721+DaysValue",
    "Age Bucket"
]

styled = detail_df[detail_cols].style.applymap(color_bucket, subset=["Age Bucket"])

# build format map for Value and Qty columns
available_cols = detail_df[detail_cols].columns.tolist()
format_map = {}
for c in available_cols:
    if "Value" in c or c == "Inventory Value":
        format_map[c] = lambda x: human_currency(x)
    elif "Qty" in c:
        format_map[c] = lambda x: human_format(x)

if format_map:
    styled = styled.format(format_map)

st.markdown('<div class="chart-container">', unsafe_allow_html=True)
st.dataframe(styled, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)