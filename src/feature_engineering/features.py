"""
Electrical Feature Engineering & Power Quality Metrics
Power Distribution Loss & Fault Analytics System
"""

import pandas as pd
import numpy as np
from src.utils.config import (
    NOMINAL_VOLTAGE_LL, VOLTAGE_NORMAL_BAND_PCT, VOLTAGE_UNDERVOLTAGE_PCT,
    VOLTAGE_OVERVOLTAGE_PCT, VOLTAGE_CRITICAL_LOW_PCT,
    PF_EXCELLENT, PF_ACCEPTABLE, PF_POOR,
    CURRENT_IMBALANCE_NORMAL_PCT, CURRENT_IMBALANCE_WARNING_PCT
)


def compute_engineering_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes rigorous power engineering metrics and statistical features:
    - IEEE Std 1159 Voltage Deviation Bands
    - IEEE Std 141 Current Imbalance Severity
    - Regulatory Power Factor Tariff Bands
    - Thermal Rise / Conductor Stress Index
    - Rolling 24-hour Statistics (Current mean/std, PF trend)
    - Commercial Reactive Energy Penalty Flags
    """
    df = df.copy()
    
    # 1. Voltage Deviation Band
    conditions_v = [
        df["voltage_deviation_pct"] > VOLTAGE_OVERVOLTAGE_PCT,
        (df["voltage_deviation_pct"] >= VOLTAGE_UNDERVOLTAGE_PCT) & (df["voltage_deviation_pct"] <= VOLTAGE_OVERVOLTAGE_PCT),
        (df["voltage_deviation_pct"] < VOLTAGE_UNDERVOLTAGE_PCT) & (df["voltage_deviation_pct"] >= VOLTAGE_CRITICAL_LOW_PCT),
        df["voltage_deviation_pct"] < VOLTAGE_CRITICAL_LOW_PCT
    ]
    choices_v = [
        "Overvoltage (>+5%)",
        "Normal (+/-5%)",
        "Undervoltage (-5% to -10%)",
        "Critical Undervoltage (<-10%)"
    ]
    df["voltage_quality_band"] = np.select(conditions_v, choices_v, default="Normal (+/-5%)")
    
    # 2. Current Imbalance Severity (IEEE Std 141)
    conditions_i = [
        df["current_imbalance_pct"] <= CURRENT_IMBALANCE_NORMAL_PCT,
        (df["current_imbalance_pct"] > CURRENT_IMBALANCE_NORMAL_PCT) & (df["current_imbalance_pct"] <= CURRENT_IMBALANCE_WARNING_PCT),
        df["current_imbalance_pct"] > CURRENT_IMBALANCE_WARNING_PCT
    ]
    choices_i = [
        "Normal (<=5%)",
        "Warning (5-10%)",
        "Critical Unbalance (>10%)"
    ]
    df["current_imbalance_severity"] = np.select(conditions_i, choices_i, default="Normal (<=5%)")
    
    # 3. Thermal Rise (Conductor / Equipment Copper Heat Dissipation)
    df["thermal_rise_c"] = np.round(df["equipment_temperature_c"] - df["ambient_temperature_c"], 1)
    
    # 4. Reactive Energy Surcharge / Tariff Penalty Flag
    # Many utilities impose heavy penalties when PF drops below 0.85
    df["pf_penalty_incurred"] = np.where(df["power_factor"] < 0.85, 1, 0)
    
    # 5. Sort chronologically for rolling computations
    df["timestamp_dt"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values(by=["feeder_id", "timestamp_dt"]).reset_index(drop=True)
    
    # 6. Feeder-wise Rolling 24-Hour (48 intervals) Averages and Volatilities
    grouped = df.groupby("feeder_id")
    
    df["rolling_current_avg_24h"] = grouped["current_avg"].transform(
        lambda s: s.rolling(window=48, min_periods=1).mean().round(2)
    )
    df["rolling_current_std_24h"] = grouped["current_avg"].transform(
        lambda s: s.rolling(window=48, min_periods=1).std().fillna(0).round(2)
    )
    df["rolling_pf_avg_24h"] = grouped["power_factor"].transform(
        lambda s: s.rolling(window=48, min_periods=1).mean().round(3)
    )
    df["rolling_loss_pct_24h"] = grouped["feeder_loss_pct"].transform(
        lambda s: s.rolling(window=48, min_periods=1).mean().round(2)
    )
    
    # Drop temporary datetime
    df = df.drop(columns=["timestamp_dt"])
    
    return df
