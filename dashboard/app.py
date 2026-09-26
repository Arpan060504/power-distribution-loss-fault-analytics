"""
Power Distribution Loss & Fault Analytics System
Interactive SCADA / AMI Operations Dashboard (Power BI Style)
Built with Streamlit & Plotly
"""

import sqlite3
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from pathlib import Path
import sys

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from src.utils.config import DB_PATH, NOMINAL_VOLTAGE_LL, PROCESSED_DATA_DIR
from src.fault_analysis.fault_engine import EngineeringInsightGenerator, RecommendationEngine

# Page Configuration with wide layout & dark/modern engineering styling
st.set_page_config(
    page_title="Power Distribution Loss & Fault Analytics",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Power BI / SCADA CSS styling
st.markdown("""
<style>
.block-container { padding-top: 1.4rem; padding-bottom: 2.5rem; max-width: 1600px; }
h1, h2, h3 { color: #e7edf5; font-family: "Segoe UI", Roboto, sans-serif; letter-spacing: -0.02em; }
h1 { margin-bottom: 0.25rem; }
section[data-testid="stSidebar"] { border-right: 1px solid #293241; }
section[data-testid="stSidebar"] .block-container { padding-top: 1.25rem; }

div[data-testid="stMetric"] {
    background: linear-gradient(145deg, #1c2430 0%, #171d27 100%);
    border: 1px solid #303b4d; border-radius: 12px; padding: 14px 15px;
    min-height: 112px; box-shadow: 0 6px 18px rgba(0,0,0,0.18);
    transition: border-color .15s ease, transform .15s ease;
}
div[data-testid="stMetric"]:hover { border-color: #4a5a70; transform: translateY(-1px); }
div[data-testid="stMetric"] label {
    color: #9aa8ba !important; font-size: .74rem !important; font-weight: 700;
    text-transform: uppercase; letter-spacing: .06em; white-space: normal !important;
}
div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
    color: #f8fafc !important; font-size: clamp(1.35rem, 2vw, 1.9rem) !important;
    font-weight: 750; line-height: 1.15; white-space: normal !important;
    overflow-wrap: anywhere;
}
div[data-testid="stMetric"] div[data-testid="stMetricDelta"] { font-size: .73rem !important; margin-top: .25rem; }

button[data-baseweb="tab"] { font-weight: 650; color: #9aa8ba; padding-left: 12px; padding-right: 12px; }
button[data-baseweb="tab"][aria-selected="true"] { color: #f8fafc; }
div[data-testid="stExpander"] { border: 1px solid #303b4d; border-radius: 10px; overflow: hidden; }
div[data-testid="stDataFrame"] { border: 1px solid #303b4d; border-radius: 10px; overflow: hidden; }

.dashboard-status { display: flex; gap: 8px; flex-wrap: wrap; margin: .15rem 0 1rem 0; }
.status-chip {
    display: inline-flex; align-items: center; gap: 6px; padding: 5px 10px;
    border-radius: 999px; border: 1px solid #334155; background: #151c26;
    color: #cbd5e1; font-size: .78rem; font-weight: 600;
}
.status-dot { width: 7px; height: 7px; border-radius: 50%; background: #48bb78; display: inline-block; }

.kpi-badge { display: inline-block; padding: 4px 9px; border-radius: 999px; font-size: .75rem; font-weight: 700; }
.badge-critical { background-color: #742a2a; color: #feb2b2; }
.badge-warning { background-color: #744210; color: #fbd38d; }
.badge-normal { background-color: #22543d; color: #9ae6b4; }

@media (max-width: 1100px) {
    div[data-testid="stMetric"] { min-height: 100px; padding: 11px 12px; }
}
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=3600)
def load_data():
    """Loads relational data from SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    
    dim_sub = pd.read_sql("SELECT * FROM dim_substation", conn)
    dim_tr = pd.read_sql("SELECT * FROM dim_transformer", conn)
    dim_fdr = pd.read_sql("SELECT * FROM dim_feeder", conn)
    dim_load = pd.read_sql("SELECT * FROM dim_load", conn)
    dim_fault = pd.read_sql("SELECT * FROM dim_fault", conn)
    dim_cal = pd.read_sql("SELECT * FROM dim_calendar", conn)
    
    # Load fact measurements (select essential columns for dashboard performance)
    meas_query = """
    SELECT 
        measurement_id, timestamp, date_key, feeder_id, substation_id, transformer_id,
        load_type_id, voltage_avg, voltage_deviation_pct, current_avg,
        current_imbalance_pct, active_power_kw, reactive_power_kvar, apparent_power_kva,
        power_factor, pf_category, frequency_hz, feeder_loss_kw, feeder_loss_pct,
        energy_kwh, transformer_loading_pct, ambient_temperature_c, equipment_temperature_c,
        thermal_rise_c, pf_penalty_incurred, fault_status, fault_type_id,
        stat_anomaly_flag, stat_anomaly_reason, ml_anomaly_flag, ml_anomaly_score,
        anomaly_consensus, is_any_anomaly, anomaly_type_engineering
    FROM fact_electrical_measurements
    """
    df_meas = pd.read_sql(meas_query, conn)
    df_faults = pd.read_sql("SELECT * FROM fact_fault_events", conn)
    df_maint = pd.read_sql("SELECT * FROM fact_maintenance", conn)
    
    # Load authentic RIL field telemetry
    try:
        df_ril = pd.read_sql("SELECT * FROM fact_ril_field_measurements", conn)
    except Exception:
        from src.utils.ril_data import process_ril_telemetry
        df_ril = process_ril_telemetry()
    
    conn.close()
    
    df_meas["timestamp"] = pd.to_datetime(df_meas["timestamp"])
    df_faults["timestamp"] = pd.to_datetime(df_faults["timestamp"])
    
    return dim_sub, dim_tr, dim_fdr, dim_load, dim_fault, dim_cal, df_meas, df_faults, df_maint, df_ril


# Load datasets
dim_sub, dim_tr, dim_fdr, dim_load, dim_fault, dim_cal, df_meas, df_faults, df_maint, df_ril = load_data()

# =====================================================================
# SIDEBAR CONTROLS & HIERARCHICAL FILTERS
# =====================================================================
st.sidebar.image("https://img.icons8.com/fluency/96/electricity.png", width=64)
st.sidebar.title("Grid Control Center")
st.sidebar.caption("Electrical Distribution SCADA / AMI System")

# Use the measurement fact table as the source of truth for valid
# asset/load combinations. This prevents impossible filter combinations.
load_map = (
    dim_load[["load_type_id", "load_category"]]
    .drop_duplicates()
    .copy()
)

df_filter_base = df_meas.merge(
    load_map,
    on="load_type_id",
    how="left",
    validate="many_to_one"
)
df_filter_base["load_category"] = df_filter_base["load_category"].fillna("Unknown")

# 1. Substation
substation_values = (
    df_filter_base["substation_id"]
    .dropna()
    .drop_duplicates()
    .sort_values()
    .tolist()
)
sel_sub = st.sidebar.selectbox(
    "Substation",
    ["All Substations"] + substation_values,
    key="main_substation_filter"
)

# 2. Transformer depends on Substation
tr_pool = df_filter_base.copy()
if sel_sub != "All Substations":
    tr_pool = tr_pool[tr_pool["substation_id"] == sel_sub]

transformer_values = (
    tr_pool["transformer_id"]
    .dropna()
    .drop_duplicates()
    .sort_values()
    .tolist()
)
sel_tr = st.sidebar.selectbox(
    "Transformer",
    ["All Transformers"] + transformer_values,
    key="main_transformer_filter"
)

# 3. Load Category depends on Substation + Transformer
load_pool = tr_pool.copy()
if sel_tr != "All Transformers":
    load_pool = load_pool[load_pool["transformer_id"] == sel_tr]

load_values = (
    load_pool["load_category"]
    .dropna()
    .drop_duplicates()
    .sort_values()
    .tolist()
)
sel_load = st.sidebar.selectbox(
    "Load Category",
    ["All Load Types"] + load_values,
    key="main_load_category_filter"
)

# 4. Feeder depends on Substation + Transformer + Load Category
feeder_pool = load_pool.copy()
if sel_load != "All Load Types":
    feeder_pool = feeder_pool[
        feeder_pool["load_category"] == sel_load
    ]

feeder_values = (
    feeder_pool["feeder_id"]
    .dropna()
    .drop_duplicates()
    .sort_values()
    .tolist()
)
sel_feeder = st.sidebar.selectbox(
    "Feeder",
    ["All Feeders"] + feeder_values,
    key="main_feeder_filter"
)

# 5. Observation window
min_date = df_meas["timestamp"].min().date()
max_date = df_meas["timestamp"].max().date()

date_range = st.sidebar.date_input(
    "Observation Window",
    (min_date, max_date),
    min_value=min_date,
    max_value=max_date,
    key="main_date_filter"
)

if isinstance(date_range, tuple):
    if len(date_range) == 1:
        start_date = end_date = date_range[0]
    else:
        start_date, end_date = date_range[0], date_range[1]
else:
    start_date = end_date = date_range

# Apply telemetry filters
mask = (
    (df_meas["timestamp"].dt.date >= start_date) &
    (df_meas["timestamp"].dt.date <= end_date)
)

if sel_sub != "All Substations":
    mask &= df_meas["substation_id"] == sel_sub

if sel_tr != "All Transformers":
    mask &= df_meas["transformer_id"] == sel_tr

if sel_feeder != "All Feeders":
    mask &= df_meas["feeder_id"] == sel_feeder

if sel_load != "All Load Types":
    selected_load_ids = load_map.loc[
        load_map["load_category"] == sel_load,
        "load_type_id"
    ].drop_duplicates().tolist()
    mask &= df_meas["load_type_id"].isin(selected_load_ids)

df_filtered = df_meas.loc[mask].copy()

# Apply fault filters
f_mask = (
    (df_faults["timestamp"].dt.date >= start_date) &
    (df_faults["timestamp"].dt.date <= end_date)
)

if sel_sub != "All Substations":
    f_mask &= df_faults["substation_id"] == sel_sub

if sel_tr != "All Transformers":
    f_mask &= df_faults["transformer_id"] == sel_tr

if sel_feeder != "All Feeders":
    f_mask &= df_faults["feeder_id"] == sel_feeder

df_faults_filtered = df_faults.loc[f_mask].copy()

# Sidebar status
st.sidebar.markdown("---")
st.sidebar.info(
    f"**Loaded Telemetry:** {len(df_filtered):,} intervals\n"
    f"**Active Faults:** {len(df_faults_filtered):,} events"
)

if df_filtered.empty:
    st.sidebar.warning("No telemetry in selected observation window.")
    st.warning(
        "No electrical telemetry records match the selected filters and "
        "observation window. The asset combination is valid, but there are "
        "no records in the selected date range."
    )
    st.info(
        "Try widening the Observation Window or selecting a broader asset "
        "filter. For a full-system view use All Substations / All Transformers "
        "/ All Feeders / All Load Types."
    )
    st.stop()

# Compact operational context bar
active_filter_count = sum([
    sel_sub != "All Substations",
    sel_tr != "All Transformers",
    sel_load != "All Load Types",
    sel_feeder != "All Feeders"
])
filter_state = "Filtered view" if active_filter_count else "Full system view"
latest_ts = df_filtered["timestamp"].max()
latest_label = latest_ts.strftime("%d %b %Y, %H:%M") if pd.notna(latest_ts) else "N/A"

st.markdown(
    f"""
    <div class="dashboard-status">
        <span class="status-chip"><span class="status-dot"></span>{filter_state}</span>
        <span class="status-chip">📡 {len(df_filtered):,} telemetry intervals</span>
        <span class="status-chip">🚨 {len(df_faults_filtered):,} fault events</span>
        <span class="status-chip">🕒 Latest record: {latest_label}</span>
    </div>
    """,
    unsafe_allow_html=True
)

# Navigation Tabs
nav_tabs = st.tabs([
    "📊 Overview",
    "⚡ Losses",
    "🔌 Power Quality",
    "🚨 Faults",
    "🔍 Anomalies",
    "🛠️ Maintenance",
    "📥 Data Export",
    "🏭 RIL Field Study"
])

# =====================================================================
# TAB 1: SYSTEM OVERVIEW
# =====================================================================
with nav_tabs[0]:
    st.title("Distribution Grid Operations")
    st.caption("Executive overview of telemetry, technical losses, power factor, fault activity, and asset loading.")
    
    # Calculate Executive KPIs
    total_energy_mwh = df_filtered["energy_kwh"].sum() / 1000.0
    total_loss_mwh = (df_filtered["feeder_loss_kw"] * 0.5).sum() / 1000.0
    overall_loss_pct = (total_loss_mwh / (total_energy_mwh + total_loss_mwh)) * 100.0 if total_energy_mwh > 0 else 0.0
    avg_pf = df_filtered["power_factor"].mean()
    total_faults_count = len(df_faults_filtered)
    total_anomalies_count = df_filtered["is_any_anomaly"].sum()
    peak_tr_loading = df_filtered["transformer_loading_pct"].max()
    
    # Identify Worst Performing Feeder (Highest average loss %)
    feeder_loss_rank = df_filtered.groupby("feeder_id")["feeder_loss_pct"].mean().sort_values(ascending=False)
    worst_feeder_id = feeder_loss_rank.index[0] if len(feeder_loss_rank) > 0 else "N/A"
    worst_feeder_val = feeder_loss_rank.iloc[0] if len(feeder_loss_rank) > 0 else 0.0
    
    # Executive KPI grid: four primary metrics + three diagnostics.
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Delivered Energy", f"{total_energy_mwh:,.1f} MWh")
    k2.metric("Feeder Losses", f"{total_loss_mwh:,.1f} MWh", f"{overall_loss_pct:.2f}% of input", delta_color="inverse")
    k3.metric("System Avg PF", f"{avg_pf:.3f}", "Tariff target ≥ 0.95")
    k4.metric("Fault Events", f"{total_faults_count:,}")

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    k5, k6, k7 = st.columns(3)
    k5.metric(
        "Detected Anomalies",
        f"{total_anomalies_count:,}",
        f"{(total_anomalies_count / len(df_filtered) * 100):.1f}% of telemetry"
        if len(df_filtered) > 0 else "0%"
    )
    k6.metric(
        "Peak Transformer Load",
        f"{peak_tr_loading:.1f}%",
        "Threshold: 100%",
        delta_color="inverse" if peak_tr_loading > 100 else "normal"
    )
    k7.metric(
        "Highest-Loss Feeder",
        f"{worst_feeder_id}",
        f"{worst_feeder_val:.2f}% average loss",
        delta_color="inverse"
    )
    
    st.markdown("---")
    
    st.caption(
        f"Current scope: {sel_sub} • {sel_tr} • {sel_load} • {sel_feeder} • "
        f"{start_date} to {end_date}"
    )

    # Row 1: System Load & Loss Profile (Daily Resampling for smooth interactive visualization)
    c1, c2 = st.columns([7, 5])
    
    with c1:
        st.subheader("Daily System Demand & Conductor Loss Trend")
        df_daily = df_filtered.set_index("timestamp").resample("D").agg({
            "active_power_kw": "mean",
            "feeder_loss_kw": "mean",
            "apparent_power_kva": "mean",
            "feeder_loss_pct": "mean"
        }).reset_index()
        
        fig_trend = make_subplots(specs=[[{"secondary_y": True}]])
        fig_trend.add_trace(
            go.Scatter(x=df_daily["timestamp"], y=df_daily["active_power_kw"], name="Active Power (kW)", line=dict(color="#3182ce", width=2.5)),
            secondary_y=False
        )
        fig_trend.add_trace(
            go.Scatter(x=df_daily["timestamp"], y=df_daily["feeder_loss_kw"], name="Feeder Loss (kW)", line=dict(color="#e53e3e", width=2, dash="dot")),
            secondary_y=True
        )
        fig_trend.update_layout(
            template="plotly_dark",
            hovermode="x unified",
            margin=dict(l=20, r=20, t=30, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        fig_trend.update_yaxes(title_text="Active Power Demand (kW)", secondary_y=False)
        fig_trend.update_yaxes(title_text="Feeder Conductor Loss (kW)", secondary_y=True)
        st.plotly_chart(fig_trend, use_container_width=True)
        
    with c2:
        st.subheader("Transformer Capacity Loading Gauge / Status")
        tr_stats = df_filtered.groupby("transformer_id")["transformer_loading_pct"].agg(["mean", "max"]).reset_index()
        fig_tr = go.Figure()
        fig_tr.add_trace(go.Bar(
            x=tr_stats["transformer_id"],
            y=tr_stats["mean"],
            name="Average Loading %",
            marker_color="#4299e1"
        ))
        fig_tr.add_trace(go.Bar(
            x=tr_stats["transformer_id"],
            y=tr_stats["max"],
            name="Peak Loading %",
            marker_color="#f56565"
        ))
        fig_tr.add_hline(y=100.0, line_dash="dash", line_color="#feb2b2", annotation_text="Rated 100% Capacity")
        fig_tr.add_hline(y=80.0, line_dash="dot", line_color="#fbd38d", annotation_text="High Alert 80%")
        fig_tr.update_layout(
            barmode="group",
            template="plotly_dark",
            yaxis_title="Loading % of Rated MVA",
            margin=dict(l=20, r=20, t=30, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_tr, use_container_width=True)

    # Row 2: Active vs Reactive Power Flow and Power Factor Distribution
    r2_c1, r2_c2 = st.columns(2)
    
    with r2_c1:
        st.subheader("Active Power (kW) vs Reactive Power (kVAR) Balance")
        df_sample = df_filtered.sample(min(2000, len(df_filtered)), random_state=42)
        fig_pq = px.scatter(
            df_sample,
            x="active_power_kw",
            y="reactive_power_kvar",
            color="pf_category",
            color_discrete_map={
                "Excellent (>=0.95)": "#48bb78",
                "Acceptable (0.90-0.94)": "#38b2ac",
                "Poor (0.80-0.89)": "#ecc94b",
                "Critical (<0.80)": "#f56565"
            },
            hover_data=["feeder_id", "power_factor", "current_avg"],
            template="plotly_dark"
        )
        fig_pq.update_layout(
            xaxis_title="Active Power P (kW)",
            yaxis_title="Reactive Power Q (kVAR)",
            margin=dict(l=20, r=20, t=30, b=20)
        )
        st.plotly_chart(fig_pq, use_container_width=True)
        
    with r2_c2:
        st.subheader("Hourly Average System Load Profile (Diurnal Curve)")
        df_hourly = df_filtered.copy()
        df_hourly["hour"] = df_hourly["timestamp"].dt.hour
        hourly_curve = df_hourly.groupby("hour").agg({
            "active_power_kw": "mean",
            "feeder_loss_kw": "mean"
        }).reset_index()
        
        fig_hr = go.Figure()
        fig_hr.add_trace(go.Scatter(
            x=hourly_curve["hour"],
            y=hourly_curve["active_power_kw"],
            mode="lines+markers",
            name="Active Load (kW)",
            line=dict(color="#63b3ed", width=3)
        ))
        fig_hr.update_layout(
            template="plotly_dark",
            xaxis=dict(tickmode="linear", tick0=0, dtick=2, title="Hour of Day (00:00 - 23:00)"),
            yaxis_title="Mean Active Demand (kW)",
            margin=dict(l=20, r=20, t=30, b=20)
        )
        st.plotly_chart(fig_hr, use_container_width=True)


# =====================================================================
# TAB 2: FEEDER LOSS & PERFORMANCE
# =====================================================================
with nav_tabs[1]:
    st.title("Feeder Loss Analytics")
    st.markdown("Rigorous physical evaluation of $P_{loss} = 3 \\cdot I_{avg}^2 \\cdot R_{feeder}$ across distribution circuits.")
    
    # Feeder Performance Scorecard Table
    fdr_perf = df_filtered.groupby("feeder_id").agg({
        "energy_kwh": "sum",
        "feeder_loss_kw": lambda s: (s * 0.5).sum(),
        "feeder_loss_pct": "mean",
        "power_factor": "mean",
        "current_avg": ["mean", "max"],
        "current_imbalance_pct": "mean"
    }).reset_index()
    
    fdr_perf.columns = [
        "Feeder ID", "Delivered Energy (kWh)", "Loss (kWh)", "Avg Loss %",
        "Avg PF", "Avg Current (A)", "Peak Current (A)", "Avg Imbalance %"
    ]
    fdr_perf["Delivered MWh"] = (fdr_perf["Delivered Energy (kWh)"] / 1000.0).round(2)
    fdr_perf["Loss MWh"] = (fdr_perf["Loss (kWh)"] / 1000.0).round(2)
    fdr_perf["Avg Loss %"] = fdr_perf["Avg Loss %"].round(2)
    fdr_perf["Avg PF"] = fdr_perf["Avg PF"].round(3)
    fdr_perf["Avg Current (A)"] = fdr_perf["Avg Current (A)"].round(1)
    fdr_perf["Peak Current (A)"] = fdr_perf["Peak Current (A)"].round(1)
    fdr_perf["Avg Imbalance %"] = fdr_perf["Avg Imbalance %"].round(2)
    
    # Merge with feeder metadata for line length and resistance
    fdr_perf = fdr_perf.merge(dim_fdr[["feeder_id", "feeder_name", "load_category", "length_km", "total_resistance_ohm"]], left_on="Feeder ID", right_on="feeder_id")
    fdr_perf = fdr_perf.sort_values(by="Avg Loss %", ascending=False)
    
    st.subheader("Feeder Performance Ranking & Conductor Characteristics")
    
    # Display styled dataframe
    display_cols = [
        "Feeder ID", "feeder_name", "load_category", "length_km", "total_resistance_ohm",
        "Delivered MWh", "Loss MWh", "Avg Loss %", "Avg PF", "Peak Current (A)", "Avg Imbalance %"
    ]
    st.dataframe(
        fdr_perf[display_cols].rename(columns={
            "feeder_name": "Feeder Name",
            "load_category": "Load Type",
            "length_km": "Length (km)",
            "total_resistance_ohm": "Resistance R (Ω)"
        }),
        use_container_width=True,
        hide_index=True
    )
    
    st.markdown("---")
    
    f_c1, f_c2 = st.columns(2)
    
    with f_c1:
        st.subheader("Physical Law Verification: Loss ∝ I² (Quadratic Proportionality)")
        st.caption("Scatter plot demonstrating that conductor loss scales quadratically with current.")
        f_sample = df_filtered.sample(min(2500, len(df_filtered)), random_state=42)
        fig_i2r = px.scatter(
            f_sample,
            x="current_avg",
            y="feeder_loss_kw",
            color="feeder_id",
            hover_data=["feeder_id", "power_factor", "equipment_temperature_c"],
            template="plotly_dark"
        )
        fig_i2r.update_layout(
            xaxis_title="Feeder Current I_avg (A)",
            yaxis_title="Feeder Copper Loss P_loss (kW)",
            margin=dict(l=20, r=20, t=30, b=20)
        )
        st.plotly_chart(fig_i2r, use_container_width=True)
        
    with f_c2:
        st.subheader("Feeder Conductor Loss vs Line Resistance & Length")
        st.caption("Feeders with high line resistance (long overhead lines) suffer severe technical losses.")
        fig_r = px.scatter(
            fdr_perf,
            x="total_resistance_ohm",
            y="Avg Loss %",
            size="Delivered MWh",
            color="Avg PF",
            text="Feeder ID",
            template="plotly_dark",
            color_continuous_scale="Viridis"
        )
        fig_r.update_traces(textposition="top center")
        fig_r.update_layout(
            xaxis_title="Total Feeder Loop Resistance R (Ω)",
            yaxis_title="Average Loss Percentage (%)",
            margin=dict(l=20, r=20, t=30, b=20)
        )
        st.plotly_chart(fig_r, use_container_width=True)

    # Loss Heatmap by Day of Week and Hour of Day
    st.subheader("Diurnal Loss Intensity Heatmap (Day of Week vs Hour of Day)")
    df_hm = df_filtered.copy()
    df_hm["hour"] = df_hm["timestamp"].dt.hour
    df_hm["day_name"] = df_hm["timestamp"].dt.day_name()
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    heatmap_matrix = df_hm.pivot_table(
        index="day_name",
        columns="hour",
        values="feeder_loss_pct",
        aggfunc="mean"
    ).reindex(day_order)
    
    fig_hm = px.imshow(
        heatmap_matrix,
        labels=dict(x="Hour of Day", y="Day of Week", color="Avg Loss %"),
        x=heatmap_matrix.columns,
        y=heatmap_matrix.index,
        color_continuous_scale="Magma",
        template="plotly_dark"
    )
    fig_hm.update_layout(margin=dict(l=20, r=20, t=30, b=20))
    st.plotly_chart(fig_hm, use_container_width=True)


# =====================================================================
# TAB 3: POWER QUALITY & IEEE 141
# =====================================================================
with nav_tabs[2]:
    st.title("Power Quality & Phase Balance")
    st.markdown("Auditing voltage regulation, negative-sequence current imbalance, and reactive energy penalties.")
    
    pq_c1, pq_c2 = st.columns(2)
    
    with pq_c1:
        st.subheader("Voltage Deviation Distribution vs IEEE Std 1159 (±5% Limits)")
        fig_v = px.histogram(
            df_filtered,
            x="voltage_deviation_pct",
            nbins=60,
            color="feeder_id",
            template="plotly_dark",
            marginal="box"
        )
        fig_v.add_vline(x=-5.0, line_dash="dash", line_color="#ecc94b", annotation_text="Lower Tol -5%")
        fig_v.add_vline(x=5.0, line_dash="dash", line_color="#ecc94b", annotation_text="Upper Tol +5%")
        fig_v.add_vline(x=-10.0, line_dash="dot", line_color="#f56565", annotation_text="Critical Sag -10%")
        fig_v.update_layout(
            xaxis_title="Voltage Deviation % from Nominal (11 kV)",
            yaxis_title="Record Count",
            margin=dict(l=20, r=20, t=30, b=20)
        )
        st.plotly_chart(fig_v, use_container_width=True)
        
    with pq_c2:
        st.subheader("IEEE Std 141 Phase Current Imbalance Distribution")
        fig_imb = px.box(
            df_filtered,
            x="feeder_id",
            y="current_imbalance_pct",
            color="feeder_id",
            template="plotly_dark"
        )
        fig_imb.add_hline(y=5.0, line_dash="dash", line_color="#ecc94b", annotation_text="IEEE 141 Max Recommended (5%)")
        fig_imb.add_hline(y=10.0, line_dash="dot", line_color="#f56565", annotation_text="Severe Unbalance (10%)")
        fig_imb.update_layout(
            xaxis_title="Feeder",
            yaxis_title="Current Imbalance %",
            showlegend=False,
            margin=dict(l=20, r=20, t=30, b=20)
        )
        st.plotly_chart(fig_imb, use_container_width=True)

    # Power Factor Compliance & Commercial Penalty Exposure
    st.subheader("Power Factor Compliance Breakdown & Reactive Energy Tariff Penalty")
    pf_c1, pf_c2 = st.columns([5, 7])
    
    with pf_c1:
        pf_counts = df_filtered["pf_category"].value_counts().reset_index()
        pf_counts.columns = ["Category", "Intervals"]
        fig_pf_pie = px.pie(
            pf_counts,
            values="Intervals",
            names="Category",
            hole=0.45,
            color="Category",
            color_discrete_map={
                "Excellent (>=0.95)": "#48bb78",
                "Acceptable (0.90-0.94)": "#38b2ac",
                "Poor (0.80-0.89)": "#ecc94b",
                "Critical (<0.80)": "#f56565"
            },
            template="plotly_dark"
        )
        fig_pf_pie.update_layout(margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_pf_pie, use_container_width=True)
        
    with pf_c2:
        penalty_by_feeder = df_filtered.groupby("feeder_id").agg({
            "pf_penalty_incurred": ["sum", lambda s: s.sum() * 0.5, lambda s: (s.sum() / len(s)) * 100.0],
            "reactive_power_kvar": "mean"
        }).reset_index()
        penalty_by_feeder.columns = ["Feeder ID", "Penalty Intervals", "Penalty Exposure (Hours)", "Penalty Time %", "Mean Reactive kVAR"]
        penalty_by_feeder["Penalty Time %"] = penalty_by_feeder["Penalty Time %"].round(1)
        penalty_by_feeder["Mean Reactive kVAR"] = penalty_by_feeder["Mean Reactive kVAR"].round(1)
        
        fig_pen = px.bar(
            penalty_by_feeder.sort_values(by="Penalty Exposure (Hours)", ascending=False),
            x="Feeder ID",
            y="Penalty Exposure (Hours)",
            color="Penalty Time %",
            color_continuous_scale="Reds",
            template="plotly_dark"
        )
        fig_pen.update_layout(
            xaxis_title="Feeder ID",
            yaxis_title="Hours Operating Below 0.85 PF (Commercial Penalty Zone)",
            margin=dict(l=20, r=20, t=30, b=20)
        )
        st.plotly_chart(fig_pen, use_container_width=True)


# =====================================================================
# TAB 4: FAULT ANALYTICS
# =====================================================================
with nav_tabs[3]:
    st.title("Fault Analytics & Reliability")
    st.markdown("Analysis of unscheduled breaker trips, protection relay operations (IEEE 50/51/27/59), and severity scores.")
    
    flt_c1, flt_c2, flt_c3 = st.columns(3)
    
    with flt_c1:
        st.subheader("Fault Incidents by Type")
        flt_type_counts = df_faults_filtered["fault_type_id"].value_counts().reset_index()
        flt_type_counts.columns = ["Fault Type", "Count"]
        fig_f_type = px.bar(
            flt_type_counts,
            x="Count",
            y="Fault Type",
            orientation="h",
            color="Count",
            color_continuous_scale="Turbo",
            template="plotly_dark"
        )
        fig_f_type.update_layout(margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_f_type, use_container_width=True)
        
    with flt_c2:
        st.subheader("Rule-Based Fault Severity Score Distribution")
        fig_f_sev = px.histogram(
            df_faults_filtered,
            x="severity_score",
            nbins=25,
            color="fault_type_id",
            template="plotly_dark"
        )
        fig_f_sev.update_layout(
            xaxis_title="Fault Severity Score (0 - 100)",
            yaxis_title="Incident Count",
            margin=dict(l=20, r=20, t=30, b=20)
        )
        st.plotly_chart(fig_f_sev, use_container_width=True)
        
    with flt_c3:
        st.subheader("Fault Trip Concentration by Feeder")
        fdr_f_counts = df_faults_filtered["feeder_id"].value_counts().reset_index()
        fdr_f_counts.columns = ["Feeder ID", "Incidents"]
        fig_fdr_f = px.bar(
            fdr_f_counts,
            x="Feeder ID",
            y="Incidents",
            color="Incidents",
            color_continuous_scale="YlOrRd",
            template="plotly_dark"
        )
        fig_fdr_f.update_layout(margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_fdr_f, use_container_width=True)

    # Monthly Fault Trend & Seasonal Progression
    st.subheader("Monthly Incident Progression & Root-Cause Distribution")
    df_f_monthly = df_faults_filtered.copy()
    df_f_monthly["Month"] = df_f_monthly["timestamp"].dt.strftime("%Y-%m (%B)")
    monthly_summary = df_f_monthly.groupby(["Month", "fault_type_id"]).size().reset_index(name="Count")
    
    fig_f_trend = px.bar(
        monthly_summary,
        x="Month",
        y="Count",
        color="fault_type_id",
        barmode="stack",
        template="plotly_dark"
    )
    fig_f_trend.update_layout(
        xaxis_title="Month",
        yaxis_title="Total Fault Incidents",
        margin=dict(l=20, r=20, t=30, b=20)
    )
    st.plotly_chart(fig_f_trend, use_container_width=True)
    
    # Recent Fault Log
    st.subheader("Detailed Fault Event Log & Root Cause Attribution")
    st.dataframe(
        df_faults_filtered[[
            "event_id", "timestamp", "feeder_id", "transformer_id", "fault_type_id",
            "severity_score", "duration_minutes", "peak_current_a", "voltage_sag_pct",
            "root_cause_category", "maintenance_required"
        ]].sort_values(by="timestamp", ascending=False).head(50),
        use_container_width=True,
        hide_index=True
    )


# =====================================================================
# TAB 5: DUAL ANOMALY DETECTION
# =====================================================================
with nav_tabs[4]:
    st.title("Anomaly Detection & Telemetry Diagnostics")
    st.markdown("Benchmarking Statistical Anomaly Detection (Z-Score & IQR) against Machine Learning (Multivariate Isolation Forest).")
    
    anom_c1, anom_c2 = st.columns([5, 7])
    
    with anom_c1:
        st.subheader("Consensus Classification Breakdown")
        consensus_counts = df_filtered["anomaly_consensus"].value_counts().reset_index()
        consensus_counts.columns = ["Consensus Tier", "Count"]
        
        fig_anom_pie = px.pie(
            consensus_counts,
            values="Count",
            names="Consensus Tier",
            hole=0.4,
            color="Consensus Tier",
            color_discrete_map={
                "Dual-Method Confirmed (High Confidence)": "#e53e3e",
                "Statistical Outlier Only": "#dd6b20",
                "ML Multivariate Outlier Only": "#3182ce",
                "Normal Operation": "#2d3748"
            },
            template="plotly_dark"
        )
        fig_anom_pie.update_layout(margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_anom_pie, use_container_width=True)
        
    with anom_c2:
        st.subheader("Primary Statistical Anomaly Causal Attribution")
        stat_reasons_df = df_filtered[df_filtered["stat_anomaly_flag"] == 1]["stat_anomaly_reason"].value_counts().head(10).reset_index()
        stat_reasons_df.columns = ["Attributed Anomaly Reason", "Occurrences"]
        
        fig_reasons = px.bar(
            stat_reasons_df,
            x="Occurrences",
            y="Attributed Anomaly Reason",
            orientation="h",
            color="Occurrences",
            color_continuous_scale="Purples",
            template="plotly_dark"
        )
        fig_reasons.update_layout(margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_reasons, use_container_width=True)

    # Interactive Feeder Telemetry Deep Dive
    st.subheader("Interactive Feeder Time-Series Drill-Down with Anomaly Markers")
    drill_feeders = (
        df_filtered["feeder_id"]
        .dropna()
        .drop_duplicates()
        .sort_values()
        .tolist()
    )
    drill_feeder = st.selectbox(
        "Select Feeder for Telemetry Inspection",
        drill_feeders,
        key="drill_feeder_sel"
    )
    
    df_drill = df_filtered[df_filtered["feeder_id"] == drill_feeder].sort_values("timestamp")
    
    fig_drill = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08, subplot_titles=["Current Load (A) with Anomaly Flags", "Voltage Profile (V)"])
    
    # Current Trace
    fig_drill.add_trace(
        go.Scatter(x=df_drill["timestamp"], y=df_drill["current_avg"], mode="lines", name="Current (A)", line=dict(color="#4299e1", width=1.5)),
        row=1, col=1
    )
    
    # Anomaly Markers on Current
    df_drill_anom = df_drill[df_drill["anomaly_consensus"] == "Dual-Method Confirmed (High Confidence)"]
    fig_drill.add_trace(
        go.Scatter(
            x=df_drill_anom["timestamp"],
            y=df_drill_anom["current_avg"],
            mode="markers",
            name="Confirmed Anomaly",
            marker=dict(color="#e53e3e", size=8, symbol="x")
        ),
        row=1, col=1
    )
    
    # Voltage Trace
    fig_drill.add_trace(
        go.Scatter(x=df_drill["timestamp"], y=df_drill["voltage_avg"], mode="lines", name="Voltage (V)", line=dict(color="#ed8936", width=1.5)),
        row=2, col=1
    )
    fig_drill.add_hline(y=11000, line_dash="dash", line_color="#a0aec0", row=2, col=1, annotation_text="Nominal 11 kV")
    
    fig_drill.update_layout(
        template="plotly_dark",
        height=550,
        margin=dict(l=20, r=20, t=40, b=20),
        hovermode="x unified"
    )
    st.plotly_chart(fig_drill, use_container_width=True)


# =====================================================================
# TAB 6: MAINTENANCE INTELLIGENCE & RECOMMENDATIONS
# =====================================================================
with nav_tabs[5]:
    st.title("Maintenance Intelligence & Explainable Engineering Recommendations")
    st.markdown("Automated engineering synthesis translating operational telemetry into prioritized capital & operating actions.")
    
    # Generate dynamic insights and recommendations
    insights = EngineeringInsightGenerator.generate_insights(df_filtered, df_faults_filtered)
    recommendations = RecommendationEngine.generate_recommendations(
        df_filtered,
        df_faults_filtered
    )
    
    st.subheader("Dynamic Analytical Insights Derived from Data")
    for ins in insights:
        sev_color = "badge-critical" if ins["severity"] in ["High", "Critical"] else "badge-warning"
        with st.expander(f"📌 [{ins['category']}] {ins['title']}", expanded=True):
            st.markdown(f"<span class='kpi-badge {sev_color}'>{ins['severity']} Severity</span>", unsafe_allow_html=True)
            st.write(f"**Operational Observation:** {ins['observation']}")
            st.write(f"**Root-Cause Electrical Relationship:** {ins['engineering_cause']}")
            
    st.markdown("---")
    
    st.subheader("Actionable, Rule-Based Recommendation Queue")
    st.caption("Prioritized operational and asset-management decisions with expected financial and engineering payoffs.")
    
    rec_df = pd.DataFrame(recommendations)
    if len(rec_df) > 0:
        st.dataframe(
            rec_df[[
                "rec_id", "priority", "asset_id", "category",
                "trigger_condition", "engineering_action", "expected_benefit", "estimated_payback_months"
            ]].rename(columns={
                "rec_id": "Action ID",
                "priority": "Priority",
                "asset_id": "Asset",
                "category": "Intervention Category",
                "trigger_condition": "Operational Trigger",
                "engineering_action": "Recommended Engineering Action",
                "expected_benefit": "Expected Electrical & Economic Benefit",
                "estimated_payback_months": "Payback (Mo)"
            }),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.success("All distribution feeders and transformers operating within optimal nominal parameters.")

    st.markdown("---")
    
    # Historical Work Orders Log
    st.subheader("Historical Maintenance & Corrective Work Orders")
    st.dataframe(
        df_maint.sort_values(by="timestamp", ascending=False),
        use_container_width=True,
        hide_index=True
    )


# =====================================================================
# TAB 7: POWER BI DATA MODEL & EXPORT
# =====================================================================
with nav_tabs[6]:
    st.title("Power BI Architecture, Star Schema & Data Model Guide")
    st.markdown("""
    This project is engineered with an enterprise **Star Schema** architecture specifically designed for direct import into **Microsoft Power BI**.
    All dimension and fact tables are exported in both relational SQL and normalized CSV formats.
    """)
    
    pbi_c1, pbi_c2 = st.columns([6, 6])
    
    with pbi_c1:
        st.subheader("Relational Star Schema Design")
        st.code("""
        ==================== ENTERPRISE STAR SCHEMA ====================
        
               [dim_substation]
                      | (1:N)
               [dim_transformer]
                      | (1:N)
               [dim_feeder] -------------------+
                      | (1:N)                  |
                      v                        v
        [fact_electrical_measurements]    [fact_fault_events]
              ^              ^                 ^
              | (N:1)        | (N:1)           | (N:1)
        [dim_calendar]   [dim_load]       [dim_fault]
        
        ================================================================
        """, language="text")
        
        st.subheader("Power BI DAX Formulas Ready for Copy-Paste")
        st.code("""
        // 1. Total Technical Loss %
        Loss % = 
        DIVIDE(
            SUM(fact_electrical_measurements[feeder_loss_kw]) * 0.5,
            SUM(fact_electrical_measurements[energy_kwh]) + (SUM(fact_electrical_measurements[feeder_loss_kw]) * 0.5),
            0
        ) * 100

        // 2. Average Operating Power Factor
        Weighted PF = 
        DIVIDE(
            SUM(fact_electrical_measurements[active_power_kw]),
            SUM(fact_electrical_measurements[apparent_power_kva]),
            1.0
        )

        // 3. Chronic Phase Imbalance Flag
        Severe Imbalance Count = 
        CALCULATE(
            COUNTROWS(fact_electrical_measurements),
            fact_electrical_measurements[current_imbalance_pct] > 10.0
        )
        """, language="sql")
        
    with pbi_c2:
        st.subheader("Available Exported Clean Datasets")
        st.markdown(f"""
        The following files in `{PROCESSED_DATA_DIR.relative_to(BASE_DIR)}` can be loaded directly into Power BI via *Get Data -> Folder / CSV*:
        - `fact_electrical_measurements.csv` (Clean SCADA/AMI fact table, 104k+ rows)
        - `fact_fault_events.csv` (Protection relay trip records)
        - `fact_maintenance.csv` (Work orders & maintenance expenditure)
        - `dim_feeder.csv` (Physical line impedance, conductor type, length)
        - `dim_transformer.csv` (MVA ratings, vector group, losses)
        - `dim_substation.csv` (Substation locations and GIS coordinates)
        - `dim_load.csv` (Load characterization & harmonic profiles)
        - `dim_fault.csv` (Standard IEEE relay fault codes)
        - `dim_calendar.csv` (Calendar master with seasonal definitions)
        """)
        
        st.info("💡 **Power BI Connection:** You can also connect Power BI directly to the SQLite database `database/power_distribution.db` using the standard ODBC driver for SQLite!")


# =====================================================================
# TAB 8: RIL REFINERY SUBSTATION 600-30 FIELD CASE STUDY
# =====================================================================
with nav_tabs[7]:
    st.title("🏭 Reliance Industries Limited (RIL) Substation 600-30 Field Telemetry Case Study")
    st.markdown("""
    **Authentic Field Telemetry Benchmark:** Collected on-site during an electrical engineering internship at a major 
    **Reliance Industries Limited (RIL) Refinery & Petrochemical Complex**.
    Analyzes medium-voltage **6.6 kV distribution switchboards** (Substation 600-30 Bus A & B) and low-voltage **415 V Motor Control Centers** (Substations 600-31 & 600-32).
    """)
    
    # RIL KPIs
    if df_ril.empty:
        st.warning("RIL field telemetry is unavailable; no RIL records were loaded.")
    else:
        ril_active = df_ril[df_ril["status"] == "ACTIVE"]
        ril_total_kw = ril_active["active_power_kw"].sum()
        ril_total_kvar = ril_active["reactive_power_kvar"].sum()
        ril_total_loss_kw = ril_active["conductor_loss_kw"].sum()
        ril_max_imb = df_ril["current_imbalance_pct"].max()

        ril_worst_imb_fdr = df_ril.sort_values(
            by="current_imbalance_pct", ascending=False
        ).iloc[0]
        ril_worst_loss_fdr = df_ril.sort_values(
            by="feeder_loss_pct", ascending=False
        ).iloc[0]

        r_col1, r_col2, r_col3, r_col4, r_col5, r_col6 = st.columns(6)
        r_col1.metric("Active Process Load", f"{ril_total_kw:,.1f} kW")
        r_col2.metric("Reactive Demand", f"{ril_total_kvar:,.1f} kVAR")
        r_col3.metric("Conductor Loss", f"{ril_total_loss_kw:,.2f} kW")
        r_col4.metric(
            "Active Circuits",
            f"{len(ril_active)} / {len(df_ril)}",
            "Feeders & Motors"
        )
        r_col5.metric(
            "Peak Imbalance",
            f"{ril_max_imb:.1f}%",
            f"{ril_worst_imb_fdr['feeder_tag']} ({ril_worst_imb_fdr['substation']})",
            delta_color="inverse"
        )
        r_col6.metric(
            "Worst Loss Rate",
            f"{ril_worst_loss_fdr['feeder_loss_pct']:.2f}%",
            f"{ril_worst_loss_fdr['feeder_tag']} (415V Loading)",
            delta_color="inverse"
        )

    # Substation and Bus Bar Filters
    flt_col1, flt_col2, flt_col3 = st.columns([4, 4, 4])
    with flt_col1:
        ril_sub_opts = ["All Substations"] + sorted(list(df_ril["substation"].unique()))
        sel_ril_sub = st.selectbox("Filter RIL Substation", ril_sub_opts, key="ril_sub_sel")
    with flt_col2:
        ril_bus_opts = ["All Bus Bars"] + sorted(list(df_ril["bus_bar"].unique()))
        sel_ril_bus = st.selectbox("Filter Bus Bar", ril_bus_opts, key="ril_bus_sel")
    with flt_col3:
        ril_status_opts = ["All Statuses", "ACTIVE", "ACTIVE_INCOMER", "OFF_STANDBY", "OFF_SPARE"]
        sel_ril_status = st.selectbox("Operating Status", ril_status_opts, key="ril_status_sel")
        
    df_ril_view = df_ril.copy()
    if sel_ril_sub != "All Substations":
        df_ril_view = df_ril_view[df_ril_view["substation"] == sel_ril_sub]
    if sel_ril_bus != "All Bus Bars":
        df_ril_view = df_ril_view[df_ril_view["bus_bar"] == sel_ril_bus]
    if sel_ril_status != "All Statuses":
        df_ril_view = df_ril_view[df_ril_view["status"] == sel_ril_status]
        
    # Visualizations Row 1
    vz1_c1, vz1_c2 = st.columns(2)
    
    with vz1_c1:
        st.subheader("Conductor Loss % (Joule Dissipation across RIL Feeders)")
        st.caption("Notice how 415 V high-current product loading pumps experience up to 9.6% loss rate!")
        df_loss_sorted = df_ril_view[df_ril_view["status"].isin(["ACTIVE", "ACTIVE_INCOMER"])].sort_values(by="feeder_loss_pct", ascending=False).head(15)
        
        fig_ril_loss = px.bar(
            df_loss_sorted,
            x="feeder_loss_pct",
            y="feeder_tag",
            orientation="h",
            color="feeder_loss_pct",
            color_continuous_scale="Reds",
            hover_data=["description", "substation", "voltage_level_kv", "length_m", "current_avg_a"],
            template="plotly_dark"
        )
        fig_ril_loss.update_layout(
            xaxis_title="Conductor Technical Loss Percentage (%)",
            yaxis_title="RIL Feeder Tag",
            margin=dict(l=20, r=20, t=30, b=20)
        )
        st.plotly_chart(fig_ril_loss, use_container_width=True)
        
    with vz1_c2:
        st.subheader("IEEE Std 141 Phase Current Imbalance Audit")
        st.caption("Comparison of Ir, Iy, Ib asymmetry against the IEEE Std 141 5% Warning Threshold.")
        df_imb_sorted = df_ril_view[df_ril_view["status"].isin(["ACTIVE", "ACTIVE_INCOMER"])].sort_values(by="current_imbalance_pct", ascending=False).head(15)
        
        fig_ril_imb = px.bar(
            df_imb_sorted,
            x="feeder_tag",
            y="current_imbalance_pct",
            color="current_imbalance_pct",
            color_continuous_scale="YlOrRd",
            hover_data=["description", "current_r_a", "current_y_a", "current_b_a"],
            template="plotly_dark"
        )
        fig_ril_imb.add_hline(y=5.0, line_dash="dash", line_color="#ecc94b", annotation_text="IEEE 141 5% Warning")
        fig_ril_imb.update_layout(
            xaxis_title="RIL Feeder Tag",
            yaxis_title="Phase Current Imbalance (%)",
            margin=dict(l=20, r=20, t=30, b=20)
        )
        st.plotly_chart(fig_ril_imb, use_container_width=True)
        
    # Visualizations Row 2
    vz2_c1, vz2_c2 = st.columns(2)
    
    with vz2_c1:
        st.subheader("Cable Run Length vs Conductor Copper Loss (kW)")
        st.caption("Demonstrating the impact of XLPE route length (up to 3.6 km staff housing) and current.")
        df_active_cables = df_ril_view[(df_ril_view["status"] == "ACTIVE") & (df_ril_view["length_m"] > 0)]
        fig_ril_cables = px.scatter(
            df_active_cables,
            x="length_m",
            y="conductor_loss_kw",
            color="voltage_level_kv",
            size="current_avg_a",
            hover_name="description",
            hover_data=["feeder_tag", "area_sqmm", "power_factor"],
            color_continuous_scale="Viridis",
            template="plotly_dark"
        )
        fig_ril_cables.update_layout(
            xaxis_title="XLPE Cable Run Length (Meters)",
            yaxis_title="Conductor Loss P_loss (kW)",
            margin=dict(l=20, r=20, t=30, b=20)
        )
        st.plotly_chart(fig_ril_cables, use_container_width=True)
        
    with vz2_c2:
        st.subheader("RIL Product Dispatch Pumps: Active (kW) vs Reactive (kVAR)")
        st.caption("Refinery loading pumps (Naphtha, LPG, ATF, HSD, SFD) and operating power factors.")
        fig_ril_pq = px.scatter(
            df_ril_view[df_ril_view["status"] == "ACTIVE"],
            x="active_power_kw",
            y="reactive_power_kvar",
            color="pf_category",
            hover_name="description",
            hover_data=["feeder_tag", "power_factor", "current_avg_a"],
            color_discrete_map={
                "Excellent (>=0.95)": "#48bb78",
                "Acceptable (0.90-0.94)": "#38b2ac",
                "Moderate (0.85-0.89)": "#ecc94b",
                "Critical / Penalty (<0.85)": "#f56565"
            },
            template="plotly_dark"
        )
        fig_ril_pq.update_layout(
            xaxis_title="Active Power P (kW)",
            yaxis_title="Reactive Power Q (kVAR)",
            margin=dict(l=20, r=20, t=30, b=20)
        )
        st.plotly_chart(fig_ril_pq, use_container_width=True)
        
    # Detailed RIL Telemetry Master Table
    st.subheader("Authentic Reliance Industries Limited (RIL) Feeder Master Data")
    st.dataframe(
        df_ril_view[[
            "substation", "bus_bar", "feeder_tag", "description", "service",
            "length_m", "area_sqmm", "voltage_v", "current_r_a", "current_y_a", "current_b_a",
            "current_avg_a", "current_imbalance_pct", "power_factor", "active_power_kw",
            "reactive_power_kvar", "conductor_loss_kw", "feeder_loss_pct", "status"
        ]].rename(columns={
            "substation": "Substation",
            "bus_bar": "Bus",
            "feeder_tag": "Feeder Tag",
            "description": "Equipment Description",
            "service": "Service / Duty",
            "length_m": "Length (m)",
            "area_sqmm": "Area (mm²)",
            "voltage_v": "Voltage (V)",
            "current_r_a": "Ir (A)",
            "current_y_a": "Iy (A)",
            "current_b_a": "Ib (A)",
            "current_avg_a": "Iavg (A)",
            "current_imbalance_pct": "Imbalance %",
            "power_factor": "PF",
            "active_power_kw": "Active (kW)",
            "reactive_power_kvar": "Reactive (kVAR)",
            "conductor_loss_kw": "Loss (kW)",
            "feeder_loss_pct": "Loss %",
            "status": "Status"
        }),
        use_container_width=True,
        hide_index=True
    )

