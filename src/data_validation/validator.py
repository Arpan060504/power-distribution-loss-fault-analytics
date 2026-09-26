"""
Data Quality Engine & Validation Pipeline
Power Distribution Loss & Fault Analytics System
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple
from src.utils.config import NOMINAL_VOLTAGE_LL, TR_LOADING_OVERLOAD_PCT


class DataQualityEngine:
    """
    Automated Data Validation and Quality Assurance Pipeline for SCADA/AMI data.
    Audits incoming time-series telemetry against physical electrical boundaries.
    """
    
    def __init__(self, v_nom: float = NOMINAL_VOLTAGE_LL):
        self.v_nom = v_nom
        # Physical boundary specifications for 11 kV distribution system
        self.min_valid_voltage = 8000.0   # Sub-transmission minimum threshold
        self.max_valid_voltage = 14500.0  # PT saturation/flashover upper bound
        self.min_valid_pf = 0.50          # Practical lower bound for inductive distribution
        self.max_valid_pf = 1.00          # Absolute unity power factor ceiling
        self.min_valid_freq = 47.0        # Grid islanding / trip frequency
        self.max_valid_freq = 53.0        # Extreme overfrequency limit
        
    def run_audit(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Runs complete statistical and boundary audit on raw telemetry records.
        Returns detailed diagnostic report dictionary.
        """
        total_records = len(df)
        
        # 1. Duplicate Records Audit (feeder_id + timestamp primary key uniqueness)
        duplicate_mask = df.duplicated(subset=["feeder_id", "timestamp"], keep="first")
        total_duplicates = int(duplicate_mask.sum())
        
        # 2. Missing Values Audit
        null_counts = df.isnull().sum()
        total_null_cells = int(null_counts.sum())
        rows_with_nulls = int(df.isnull().any(axis=1).sum())
        
        # 3. Voltage Anomaly Audit (Transducer out of physical bounds)
        v_invalid_mask = (
            (df["voltage_avg"] < self.min_valid_voltage) |
            (df["voltage_avg"] > self.max_valid_voltage) |
            df["voltage_avg"].isnull()
        )
        total_voltage_anomalies = int(v_invalid_mask.sum())
        
        # 4. Current Anomaly Audit (Negative or extreme unrealistic currents)
        c_invalid_mask = (
            (df["current_avg"] < 0) |
            (df["current_avg"] > 2500) |
            df["current_avg"].isnull()
        )
        total_current_anomalies = int(c_invalid_mask.sum())
        
        # 5. Invalid Power Factor Audit (Transducer wiring glitch, PF < 0.5 or PF > 1.0)
        pf_invalid_mask = (
            (df["power_factor"] < self.min_valid_pf) |
            (df["power_factor"] > self.max_valid_pf) |
            df["power_factor"].isnull()
        )
        total_invalid_pf = int(pf_invalid_mask.sum())
        
        # 6. Physical Consistency Audit (Active Power P cannot exceed Apparent Power S: P <= S + epsilon)
        # Also P = sqrt(3) * V * I * PF / 1000
        power_inconsistent_mask = (
            (df["active_power_kw"] > (df["apparent_power_kva"] * 1.05 + 5.0)) |
            (df["active_power_kw"] < 0)
        )
        total_inconsistent_power = int(power_inconsistent_mask.sum())
        
        # 7. Transformer Overload Audit (> 100% rated capacity)
        tr_overload_mask = df["transformer_loading_pct"] > TR_LOADING_OVERLOAD_PCT
        total_tr_overloads = int(tr_overload_mask.sum())
        
        # 8. Timestamp Gaps Audit (Per feeder continuity)
        # Check standard 30-minute interval spacing
        total_timestamp_gaps = 0
        for _, group in df.groupby("feeder_id"):
            sorted_ts = pd.to_datetime(group["timestamp"]).sort_values()
            diffs = sorted_ts.diff().dropna()
            # Flag diffs > 35 minutes or < 25 minutes (excluding identical duplicate timestamps)
            gaps = ((diffs > pd.Timedelta(minutes=35)) | ((diffs < pd.Timedelta(minutes=25)) & (diffs > pd.Timedelta(0))))
            total_timestamp_gaps += int(gaps.sum())
            
        # Composite Data Quality Score calculation
        # Defective rows = rows having any defect
        defect_mask = (
            duplicate_mask |
            df.isnull().any(axis=1) |
            v_invalid_mask |
            c_invalid_mask |
            pf_invalid_mask |
            power_inconsistent_mask
        )
        defective_rows_count = int(defect_mask.sum())
        clean_rows_count = total_records - defective_rows_count
        overall_dq_score = round((clean_rows_count / total_records) * 100.0, 2) if total_records > 0 else 0.0
        
        report = {
            "total_records": total_records,
            "duplicate_records": total_duplicates,
            "missing_record_rows": rows_with_nulls,
            "total_null_cells": total_null_cells,
            "voltage_anomalies": total_voltage_anomalies,
            "current_anomalies": total_current_anomalies,
            "invalid_pf_records": total_invalid_pf,
            "inconsistent_power_records": total_inconsistent_power,
            "transformer_overload_events": total_tr_overloads,
            "timestamp_gaps": total_timestamp_gaps,
            "total_defective_rows": defective_rows_count,
            "total_clean_rows": clean_rows_count,
            "overall_data_quality_pct": overall_dq_score
        }
        
        return report

    def print_report(self, report: Dict[str, Any]) -> str:
        """
        Formats the audit report into a professional Data Engineering scorecard.
        """
        divider = "=" * 65
        output = [
            divider,
            "          ELECTRICAL DATA QUALITY ENGINE AUDIT REPORT          ",
            divider,
            f"Total Ingested Records           : {report['total_records']:,}",
            f"Duplicate Records Detected       : {report['duplicate_records']:,}",
            f"Rows with Missing Telemetry      : {report['missing_record_rows']:,}",
            f"Total Null Attribute Cells       : {report['total_null_cells']:,}",
            f"Voltage Sensor Out-of-Bounds     : {report['voltage_anomalies']:,}",
            f"Current Sensor Out-of-Bounds     : {report['current_anomalies']:,}",
            f"Invalid Power Factor (<0.5 or >1): {report['invalid_pf_records']:,}",
            f"Physics Inconsistent Power (P>S) : {report['inconsistent_power_records']:,}",
            f"Transformer Overload Intervals   : {report['transformer_overload_events']:,}",
            f"Feeder Telemetry Timestamp Gaps  : {report['timestamp_gaps']:,}",
            "-" * 65,
            f"Total Defective / Flagged Rows   : {report['total_defective_rows']:,}",
            f"Total Verified Pristine Rows     : {report['total_clean_rows']:,}",
            f"OVERALL DATA QUALITY SCORE       : {report['overall_data_quality_pct']:.2f}%",
            divider
        ]
        text_report = "\n".join(output)
        print(text_report)
        return text_report

    def clean_dataset(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Removes duplicates, rectifies sensor dropouts, re-derives consistent quantities,
        and marks verified clean records.
        """
        report = self.run_audit(df)
        df_clean = df.copy()
        
        # 1. Deduplicate by feeder_id and timestamp
        df_clean = df_clean.drop_duplicates(subset=["feeder_id", "timestamp"], keep="first")
        
        # 2. Filter out extreme impossible sensor glitches (e.g. V = 16800 or 415 on 11kV bus)
        valid_v_mask = (df_clean["voltage_avg"] >= self.min_valid_voltage) & (df_clean["voltage_avg"] <= self.max_valid_voltage)
        valid_i_mask = (df_clean["current_avg"] >= 0) & (df_clean["current_avg"] <= 2500)
        valid_pf_mask = (df_clean["power_factor"] >= self.min_valid_pf) & (df_clean["power_factor"] <= self.max_valid_pf)
        
        # Filter strictly corrupted rows
        clean_mask = valid_v_mask & valid_i_mask & valid_pf_mask & df_clean["voltage_r"].notnull()
        df_clean = df_clean[clean_mask].copy()
        
        # 3. Ensure mathematical physical consistency:
        # S = sqrt(3) * V_avg * I_avg / 1000
        df_clean["apparent_power_kva"] = np.round(
            (3 ** 0.5) * df_clean["voltage_avg"] * df_clean["current_avg"] / 1000.0, 2
        )
        # P = S * PF
        df_clean["active_power_kw"] = np.round(
            df_clean["apparent_power_kva"] * df_clean["power_factor"], 2
        )
        # Q = sqrt(S^2 - P^2)
        df_clean["reactive_power_kvar"] = np.round(
            np.sqrt(np.maximum(0.0, df_clean["apparent_power_kva"] ** 2 - df_clean["active_power_kw"] ** 2)), 2
        )
        # Energy = P * 0.5 hours
        df_clean["energy_kwh"] = np.round(df_clean["active_power_kw"] * 0.5, 2)
        
        # Assign primary key ID
        df_clean = df_clean.reset_index(drop=True)
        df_clean["measurement_id"] = [f"MEAS_{i+1:07d}" for i in range(len(df_clean))]
        
        # Reorder columns to place measurement_id first
        cols = ["measurement_id"] + [c for c in df_clean.columns if c != "measurement_id" and c != "is_synthetic_defect"]
        df_clean = df_clean[cols]
        
        return df_clean, report
