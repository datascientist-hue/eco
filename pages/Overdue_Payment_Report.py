import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from data_loader import load_csv_from_ftp

st.set_page_config(page_title="Customer Aging Report", layout="wide")

# Custom CSS for Power BI style
st.markdown("""
<style>
    body {
        background-color: #f8f9fa;
        font-family: 'Segoe UI', sans-serif;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 8px;
        text-align: center;
        border-left: 4px solid #1f77b4;
    }
    .header-title {
        color: #1f77b4;
        font-size: 32px;
        font-weight: 700;
        margin-bottom: 25px;
        text-align: center;
        background: linear-gradient(135deg, #1f77b4 0%, #2e9cca 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .stMetric {
        background-color: white;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border-left: 4px solid #1f77b4;
    }
    h3 {
        color: #1f77b4;
        font-weight: 600;
    }
    .streamlit-expanderHeader {
        background-color: #f0f2f6;
        border-radius: 5px;
    }
    [data-testid="stDataFrameContainer"] {
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="header-title">📊 Customer Aging & Payment Overdue Report</div>', unsafe_allow_html=True)

# Load Data from FTP
df = load_csv_from_ftp("Overdue_Payment_Report.csv", encoding="latin-1")

# rename column for clarity
if "BP Name" in df.columns:
    df.rename(columns={"BP Name": "Customer Name"}, inplace=True)

aging_columns = [
    "0 To 10 Days",
    "11 To 25 Days",
    "26 To 45 Days",
    "46 To 60 Days",
    "61 To 90 Days",
    "91 To 120 Days",
    "121 Days and above",
    "Balance/G.Total"
]

for col in aging_columns:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

# 🔥 Risk Logic
def risk_category(row):
    if row["121 Days and above"] > 0:
        return "Critical"
    elif row["91 To 120 Days"] > 0:
        return "High"
    elif row["61 To 90 Days"] > 0:
        return "Medium"
    else:
        return "Low"

df["Risk Level"] = df.apply(risk_category, axis=1)

# ---------------- FILTERS ----------------

st.sidebar.header("🔎 Advanced Filters")

search_customer = st.sidebar.text_input("Search Customer Name")

# customer dropdown filter with All option
customer_options = ["All"] + sorted(df["Customer Name"].dropna().unique().tolist())
customer_filter = st.sidebar.multiselect(
    "Select Customer",
    options=customer_options,
    default=["All"]
)

aging_bucket = st.sidebar.selectbox(
    "Focus Aging Bucket",
    options=aging_columns[:-1]
)

if search_customer:
    df = df[df["Customer Name"].str.contains(search_customer, case=False, na=False)]

# apply customer dropdown filter
if customer_filter and "All" not in customer_filter:
    df = df[df["Customer Name"].isin(customer_filter)]

# ---------------- KPI SECTION ----------------
# Calculate metrics before filtering for better insights
total_outstanding = df["Balance/G.Total"].sum()
overdue_total = df[["11 To 25 Days", "26 To 45 Days", "46 To 60 Days", "61 To 90 Days", "91 To 120 Days", "121 Days and above"]].sum().sum()
critical_90_plus = df[["91 To 120 Days", "121 Days and above"]].sum().sum()
critical_121 = df["121 Days and above"].sum()
total_customers = len(df)
overdue_percent = (overdue_total / total_outstanding * 100) if total_outstanding > 0 else 0

# Aging summary KPI values
aging_0_30 = df[["0 To 10 Days", "11 To 25 Days"]].sum().sum()
aging_31_60 = df[["26 To 45 Days", "46 To 60 Days"]].sum().sum()
aging_61_90 = df["61 To 90 Days"].sum()
aging_90_plus = df[["91 To 120 Days", "121 Days and above"]].sum().sum()

# Section 1 - Overall Summary KPIs
st.subheader("Overall Summary")
kpi_col1, kpi_col2, kpi_col3 = st.columns(3)

with kpi_col1:
    st.metric("Total Customers", f"{total_customers}", delta="Tracked")

with kpi_col2:
    st.metric("Total Outstanding", f"₹{total_outstanding:,.0f}", delta=None)

with kpi_col3:
    st.metric("Total Overdue", f"₹{overdue_total:,.0f}", 
              delta=f"{overdue_percent:.1f}% of total")

st.markdown("---")

# Section 2 - Aging KPIs
st.subheader("Aging Summary")
aging_col1, aging_col2, aging_col3, aging_col4 = st.columns(4)

with aging_col1:
    st.metric("0–30 Days", f"₹{aging_0_30:,.0f}")

with aging_col2:
    st.metric("31–60 Days", f"₹{aging_31_60:,.0f}")

with aging_col3:
    st.metric("61–90 Days", f"₹{aging_61_90:,.0f}")

with aging_col4:
    st.metric("90+ Days", f"₹{aging_90_plus:,.0f}")

st.markdown("---")

# Chart 1: Aging Distribution (Horizontal)
st.subheader("💵 Aging Distribution by Bucket")
aging_totals = [df[col].sum() for col in aging_columns[:-1]]

fig, ax = plt.subplots(figsize=(10, 5))
colors = ['#2ecc71', '#3498db', '#1abc9c', '#16a085', '#2980b9', '#8e44ad', '#c0392b']
bars = ax.barh(aging_columns[:-1], aging_totals, color=colors, edgecolor='white', linewidth=1.5)
ax.set_xlabel("Amount (₹)", fontsize=11, fontweight='bold', color='#333')
ax.set_title("Payment Aging Distribution", fontsize=12, fontweight='bold', pad=15, color='#1f77b4')
ax.invert_yaxis()
ax.grid(axis='x', alpha=0.3, linestyle='--')
ax.set_facecolor('#f8f9fa')

# Add value labels on bars (skip zeros)
for i, bar in enumerate(bars):
    width = bar.get_width()
    if width > 0:
        ax.text(width, bar.get_y() + bar.get_height()/2, f'₹{width:,.0f}', 
                ha='left', va='center', fontsize=9, fontweight='bold', color='#333')

plt.tight_layout()
st.pyplot(fig)

st.markdown("---")

# ============ CUSTOMER-WISE AGING REPORT ============

st.subheader("📋 Overdue Payment Report")

# Determine last payment date column if available
possible_payment_date_columns = ["Last Payment Date", "LastPaymentDate", "Last_Payment_Date"]
last_payment_date_col = next((col for col in possible_payment_date_columns if col in df.columns), None)

# Create table with required columns
report_df = df.copy()
report_df["Total Outstanding"] = report_df["Balance/G.Total"]
report_df["Total Overdue"] = report_df[["11 To 25 Days", "26 To 45 Days", "46 To 60 Days", "61 To 90 Days", "91 To 120 Days", "121 Days and above"]].sum(axis=1)

bucket_order = [
    "121 Days and above",
    "91 To 120 Days",
    "61 To 90 Days",
    "46 To 60 Days",
    "26 To 45 Days",
    "11 To 25 Days",
    "0 To 10 Days"
]

def get_aging_bucket(row):
    for bucket in bucket_order:
        if row[bucket] > 0:
            return bucket
    return "No Dues"

report_df["Aging Bucket"] = report_df.apply(get_aging_bucket, axis=1)

# Sort by total outstanding (descending)
report_df = report_df.sort_values("Total Outstanding", ascending=False)

display_columns = ["Customer Name", "Total Outstanding", "Total Overdue", "Aging Bucket"]
if last_payment_date_col:
    display_columns.append(last_payment_date_col)
    report_df = report_df.rename(columns={last_payment_date_col: "Last Payment Date"})
    display_columns[-1] = "Last Payment Date"
else:
    report_df["Last Payment Date"] = ""
    display_columns.append("Last Payment Date")

overdue_payment_report = report_df[display_columns].copy()

# Format numeric columns
overdue_payment_report["Total Outstanding"] = overdue_payment_report["Total Outstanding"].apply(lambda x: f"₹{x:,.0f}")
overdue_payment_report["Total Overdue"] = overdue_payment_report["Total Overdue"].apply(lambda x: f"₹{x:,.0f}")

st.dataframe(overdue_payment_report, use_container_width=True, height=500)

st.markdown("---")

# ============ DOWNLOAD SECTION ============

col_download1, col_download2 = st.columns(2)

with col_download1:
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Download Full Report (CSV)", csv, "Customer_Aging_Report.csv", "text/csv")

with col_download2:
    # Excel export (if openpyxl is available)
    try:
        export_df = df.copy()
        for col in aging_columns[:-1]:
            export_df[col] = export_df[col].apply(lambda x: f"{x:,.0f}")
        export_df["Balance/G.Total"] = export_df["Balance/G.Total"].apply(lambda x: f"{x:,.0f}")
        
        from io import BytesIO
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            export_df.to_excel(writer, index=False, sheet_name='Aging Report')
        buffer.seek(0)
        st.download_button("📊 Download Report (Excel)", buffer.getvalue(), "Customer_Aging_Report.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except:
        st.info("💡 Excel export requires openpyxl library")
