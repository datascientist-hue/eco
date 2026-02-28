import streamlit as st
import pandas as pd
from datetime import datetime
from data_loader import load_csv_from_ftp

# --- PAGE CONFIG ---
st.set_page_config(page_title="Daily Overdue Sale Orders", layout="wide")

# --- CUSTOM STYLING (Power BI Look) ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border-top: 4px solid #d32f2f; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    h1 { color: #d32f2f; font-weight: 800; }
    .overdue-table { font-size: 0.9em; }
    </style>
    """, unsafe_allow_html=True)

# --- DATA LOADING ---
@st.cache_data
def load_data():
    try:
        df = load_csv_from_ftp("Sale_Order_Analysis_Report.csv", encoding="latin1")
    except Exception as e:
        st.error(f"File load failed from FTP: {e}")
        return None
    
    # 1. Standardize Column Names (remove hidden spaces)
    df.columns = df.columns.str.strip()
    
    # 2. Filter for Open Orders only ('O')
    df = df[df['LineStatus'].astype(str).str.strip().str.upper() == 'O'].copy()
    
    # 3. Clean Numeric Data
    num_cols = ['OpenQty', 'Qty in Nos', 'LineTotalBeforeTax', 'COGS']
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(r'[₹,]', '', regex=True), errors='coerce').fillna(0)
    
    # 4. Convert Posting Date
    df['Posting Date'] = pd.to_datetime(df['Posting Date'], dayfirst=True, errors='coerce')
    df = df.dropna(subset=['Posting Date'])
    
    return df

df_raw = load_data()

if df_raw is not None:
    # --- LOGIC: OVERDUE CALCULATION ---
    today = pd.to_datetime(datetime.now().date())
    
    # An order is overdue if Posting Date < Today
    df_raw['Days Overdue'] = (today - df_raw['Posting Date']).dt.days
    df_overdue = df_raw[df_raw['Days Overdue'] > 0].copy()
    
    # Calculate Pending Value (Value of the items not yet shipped)
    # Logic: (Total Line Value / Original Qty) * Remaining Qty
    df_overdue['Pending Value'] = (df_overdue['LineTotalBeforeTax'] / df_overdue['Qty in Nos']) * df_overdue['OpenQty']
    df_overdue['Pending Value'] = df_overdue['Pending Value'].fillna(0)

    # Aging Buckets
    def get_bucket(d):
        if d <= 3: return "1. 0-3 Days"
        if d <= 7: return "2. 4-7 Days"
        if d <= 15: return "3. 8-15 Days"
        return "4. 15+ Days"
    df_overdue['Aging Bucket'] = df_overdue['Days Overdue'].apply(get_bucket)

    # --- SIDEBAR FILTERS ---
    st.sidebar.header("Overdue Filters")
    
    # Warehouse Filter
    all_whse = sorted([str(x) for x in df_overdue['WhsCode'].unique()])
    sel_whse = st.sidebar.multiselect("Warehouse", options=all_whse, default=all_whse)
    
    # State Filter
    all_states = sorted([str(x) for x in df_overdue['Ship-To-State'].dropna().unique()])
    sel_states = st.sidebar.multiselect("Ship-to State", options=all_states, default=all_states)

    # Apply Filters
    df_f = df_overdue[
        (df_overdue['WhsCode'].astype(str).isin(sel_whse)) & 
        (df_overdue['Ship-To-State'].astype(str).isin(sel_states))
    ]

    # --- HEADER ---
    st.title("🚨 Daily Overdue Sale Orders")
    st.markdown(f"Status: **Showing Open ('O') orders posted before {today.strftime('%d-%b-%Y')}**")

    # --- KPI METRICS ---
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Overdue Order Lines", f"{len(df_f)}")
    with m2:
        total_val = df_f['Pending Value'].sum()
        st.metric("Total Overdue Value", f"₹{total_val:,.0f}")
    with m3:
        avg_delay = df_f['Days Overdue'].mean() if not df_f.empty else 0
        st.metric("Avg. Delay", f"{int(avg_delay)} Days")
    with m4:
        critical = len(df_f[df_f['Days Overdue'] > 7])
        st.metric("Critical (>7 Days)", f"{critical}")

    st.divider()

    # --- CHARTS ---
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("Overdue by Aging Bucket")
        aging_grp = df_f.groupby('Aging Bucket')['Pending Value'].sum().reset_index()
        import plotly.express as px
        fig_aging = px.bar(aging_grp, x='Aging Bucket', y='Pending Value', 
                           color='Aging Bucket', 
                           color_discrete_map={
                               "1. 0-3 Days": "#4caf50", 
                               "2. 4-7 Days": "#ffeb3b", 
                               "3. 8-15 Days": "#ff9800", 
                               "4. 15+ Days": "#f44336"
                           })
        st.plotly_chart(fig_aging, use_container_width=True)

    with c2:
        st.subheader("Top Customers with Overdue")
        cust_grp = df_f.groupby('BP Name')['Pending Value'].sum().nlargest(10).reset_index()
        fig_cust = px.bar(cust_grp, x='Pending Value', y='BP Name', orientation='h')
        fig_cust.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_cust, use_container_width=True)

    # --- DETAILED LIST ---
    st.subheader("📋 Detailed Overdue Line Items")
    
    # Formatting for display
    disp_df = df_f[[
        'Document Number', 'Posting Date', 'BP Name', 'ItemName', 
        'WhsCode', 'OpenQty', 'Pending Value', 'Days Overdue'
    ]].copy()
    
    disp_df['Posting Date'] = disp_df['Posting Date'].dt.strftime('%d-%m-%Y')
    disp_df['Pending Value'] = disp_df['Pending Value'].map('₹{:,.0f}'.format)
    
    st.dataframe(disp_df.sort_values('Days Overdue', ascending=False), use_container_width=True, hide_index=True)

else:
    st.info("Upload or fix the file path to see the dashboard.")