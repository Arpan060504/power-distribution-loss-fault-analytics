"""
Synthetic Distribution Network Time-Series & Fault Generator
Grounded in Electrical Engineering Principles
"""

import math
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

from src.utils.config import (
    NOMINAL_VOLTAGE_LL, NOMINAL_VOLTAGE_LN, GRID_FREQUENCY_HZ,
    INTERVAL_MINUTES, INTERVAL_HOURS,
    SUBSTATIONS, TRANSFORMERS, FEEDERS, LOAD_TYPES, FAULT_TYPES,
    PF_EXCELLENT, PF_ACCEPTABLE, PF_POOR
)
from src.data_generation.network_model import generate_dim_calendar


def _get_diurnal_factor(hour: float, load_category: str) -> float:
    """
    Returns realistic load multiplier based on time-of-day and industrial load type.
    """
    if load_category == "Industrial Process":
        # 3 shifts with short shift-change dips at 06:00, 14:00, 22:00
        base = 0.85 + 0.12 * math.sin((hour - 7) * math.pi / 12)
        if int(hour) in [6, 14, 22]:
            base *= 0.88
        return max(0.65, min(1.05, base))
        
    elif load_category == "Heavy Industrial":
        # Rolling mill / arc furnace: high cyclic variance, peaks 09:00 - 17:00
        base = 0.82 + 0.18 * math.sin((hour - 9) * math.pi / 10)
        return max(0.60, min(1.15, base))
        
    elif load_category == "Induction Motors":
        # Continuous pumping / compressor cycles
        base = 0.80 + 0.15 * math.sin((hour - 8) * math.pi / 12)
        return max(0.65, min(1.08, base))
        
    elif "Residential" in load_category:
        # Dual peaks: Morning (06:30 - 09:30) and Evening peak (18:30 - 23:30)
        morning_peak = 0.40 * math.exp(-((hour - 8.0) ** 2) / 3.0)
        evening_peak = 0.55 * math.exp(-((hour - 20.5) ** 2) / 5.5)
        night_base = 0.45
        return night_base + morning_peak + evening_peak
        
    elif "Commercial" in load_category or "Institutional" in load_category:
        # Commercial / IT park: Heavy load 08:30 - 18:30 (HVAC + servers)
        if 8.5 <= hour <= 18.5:
            return 0.90 + 0.15 * math.sin((hour - 8.5) * math.pi / 10)
        elif 18.5 < hour <= 22.0:
            return 0.55
        else:
            return 0.35  # Server baseline
            
    elif "Lighting" in load_category:
        # High at night (18:30 - 06:00), minimal during day
        if hour >= 18.5 or hour < 6.0:
            return 0.95 + 0.05 * math.sin(hour)
        else:
            return 0.25  # Daytime aeration/auxiliary only
            
    elif "Agricultural" in load_category:
        # Agricultural lift irrigation: Daytime supply 07:00 - 16:00
        if 7.0 <= hour <= 16.5:
            return 0.92 + 0.12 * math.sin((hour - 7) * math.pi / 9.5)
        else:
            return 0.20
            
    else:  # Auxiliary / Utility
        return 0.75 + 0.10 * math.sin((hour - 10) * math.pi / 12)


def _get_ambient_temp(day_of_year: int, hour: float) -> float:
    """
    Simulates seasonal temperature curve (March to August: Pre-monsoon heat to Monsoon humidity).
    Pre-monsoon (March-May): 24°C night to 42°C afternoon.
    Monsoon (June-August): 26°C night to 36°C day with high humidity.
    """
    seasonal_base = 28.0 + 8.0 * math.sin((day_of_year - 60) * math.pi / 180)
    diurnal = 6.0 * math.sin((hour - 9) * math.pi / 12)
    return round(seasonal_base + diurnal + np.random.normal(0, 0.8), 1)


def generate_time_series_data(
    start_date: str = "2026-03-01",
    days: int = 182,
    seed: int = 42,
    inject_defects: bool = True
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Generates 6 months of 30-minute interval SCADA/AMI measurements across all 12 feeders.
    Yields:
      1) fact_electrical_measurements (104,832+ records)
      2) fact_fault_events (~180 realistic fault events)
      3) fact_maintenance (~120 historical maintenance work orders)
    """
    np.random.seed(seed)
    random.seed(seed)
    
    start = pd.to_datetime(start_date)
    total_timestamps = days * 48  # 48 intervals per day
    timestamps = [start + timedelta(minutes=30 * i) for i in range(total_timestamps)]
    
    feeder_dict = {f["feeder_id"]: f for f in FEEDERS}
    transformer_dict = {t["transformer_id"]: t for t in TRANSFORMERS}
    
    # Pre-generate transformer-feeder relationships
    tr_feeders = {}
    for f in FEEDERS:
        tr_feeders.setdefault(f["transformer_id"], []).append(f["feeder_id"])
        
    records = []
    fault_events = []
    fault_id_counter = 1001
    
    print(f"Generating electrical distribution time-series for {days} days ({len(timestamps)} timestamps x {len(FEEDERS)} feeders)...")
    
    # Fault injection schedule: randomly select ~180 (timestamp_idx, feeder_id) fault anchors
    fault_schedule = {}
    candidate_fault_indices = np.random.choice(range(200, total_timestamps - 200), size=190, replace=False)
    for idx in candidate_fault_indices:
        f_pick = random.choice(FEEDERS)["feeder_id"]
        # Pick realistic fault type matching feeder load
        f_type = random.choice(FAULT_TYPES)["fault_type_id"]
        # Duration between 1 and 4 intervals (30 to 120 minutes)
        dur_intervals = random.choices([1, 2, 3, 4], weights=[0.5, 0.3, 0.15, 0.05])[0]
        fault_schedule[(idx, f_pick)] = {
            "fault_type_id": f_type,
            "duration_intervals": dur_intervals,
            "active_until": idx + dur_intervals
        }
    
    # Track active faults across consecutive intervals
    active_faults = {}
    
    for t_idx, ts in enumerate(timestamps):
        date_key = int(ts.strftime("%Y%m%d"))
        hour_float = ts.hour + ts.minute / 60.0
        day_of_year = ts.dayofyear
        is_weekend = 1 if ts.dayofweek >= 5 else 0
        ambient_temp = _get_ambient_temp(day_of_year, hour_float)
        
        # Grid voltage at main substation bus with natural small fluctuations (+/- 1.2%)
        grid_v_bus = NOMINAL_VOLTAGE_LL * (1.0 + 0.012 * math.sin(t_idx / 48.0) + np.random.normal(0, 0.004))
        
        # Temporary dictionary to collect feeder powers for transformer loading
        ts_feeder_kva = {}
        ts_feeder_measurements = []
        
        for f in FEEDERS:
            f_id = f["feeder_id"]
            tr_id = f["transformer_id"]
            sub_id = f["substation_id"]
            load_id = f["load_type_id"]
            category = f["load_category"]
            r_total = f["total_resistance_ohm"]
            rated_current = f["rated_current_a"]
            base_current = f["baseline_current_a"]
            base_pf = f["base_pf"]
            imbalance_base = f["phase_imbalance_base"]
            
            # 1. Base diurnal modulation
            diurnal = _get_diurnal_factor(hour_float, category)
            
            # Weekend reduction for industrial/commercial, increase for residential
            if is_weekend:
                if "Industrial" in category:
                    diurnal *= 0.78
                elif "Commercial" in category:
                    diurnal *= 0.52
                elif "Residential" in category:
                    diurnal *= 1.15
                    
            # Temperature effect: higher ambient increases HVAC / cooling load
            temp_load_boost = 1.0 + max(0.0, (ambient_temp - 30.0) * 0.012)
            current_target = base_current * diurnal * temp_load_boost * np.random.normal(1.0, 0.025)
            
            # Check if fault is scheduled or currently active
            is_fault = False
            current_fault_type = None
            
            if (t_idx, f_id) in fault_schedule:
                active_faults[(t_idx, f_id)] = fault_schedule[(t_idx, f_id)]
                
            # Check active faults
            for (start_t, act_fid), flt_data in list(active_faults.items()):
                if act_fid == f_id and start_t <= t_idx <= flt_data["active_until"]:
                    is_fault = True
                    current_fault_type = flt_data["fault_type_id"]
                    
                    # Record fault event in fact_fault_events at onset
                    if start_t == t_idx:
                        dur_mins = flt_data["duration_intervals"] * 30
                        # Calculate physical impacts based on fault type
                        if current_fault_type == "FLT_OVERCURRENT":
                            peak_i = round(current_target * random.uniform(1.35, 1.85), 1)
                            sag_pct = round(random.uniform(6.0, 14.0), 1)
                        elif current_fault_type == "FLT_UNDERVOLT":
                            peak_i = round(current_target * random.uniform(1.05, 1.20), 1)
                            sag_pct = round(random.uniform(11.0, 22.0), 1)
                        elif current_fault_type == "FLT_IMBALANCE":
                            peak_i = round(current_target * 1.25, 1)
                            sag_pct = round(random.uniform(4.0, 9.0), 1)
                        elif current_fault_type == "FLT_TR_OVERLOAD":
                            peak_i = round(rated_current * 1.18, 1)
                            sag_pct = round(random.uniform(5.0, 10.0), 1)
                        else:
                            peak_i = round(current_target * 1.15, 1)
                            sag_pct = round(random.uniform(2.0, 7.0), 1)
                            
                        # Rule-based Transparent Severity Score (0-100)
                        overcurrent_ratio = min(2.5, peak_i / rated_current)
                        severity_score = min(100.0, round(
                            (overcurrent_ratio / 2.0) * 35.0 +
                            (sag_pct / 20.0) * 25.0 +
                            (dur_mins / 120.0) * 20.0 +
                            20.0,
                            1
                        ))
                        
                        fault_events.append({
                            "event_id": f"EVT_{fault_id_counter}",
                            "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
                            "date_key": date_key,
                            "feeder_id": f_id,
                            "transformer_id": tr_id,
                            "substation_id": sub_id,
                            "fault_type_id": current_fault_type,
                            "severity_score": severity_score,
                            "duration_minutes": dur_mins,
                            "peak_current_a": peak_i,
                            "voltage_sag_pct": sag_pct,
                            "affected_phase": random.choice(["R-Phase", "Y-Phase", "B-Phase", "All 3-Phases"]),
                            "root_cause_category": random.choice([
                                "Transient Tree Branch Contact", "Industrial Motor Inrush", "Insulator Flashover",
                                "Harmonic Overload", "Cable Joint Stress", "Phase Unbalance Surge"
                            ]),
                            "maintenance_required": 1 if severity_score >= 65.0 else 0,
                            "resolved_timestamp": (ts + timedelta(minutes=dur_mins)).strftime("%Y-%m-%d %H:%M:%S"),
                            "resolution_notes": f"Breaker reset and feeder inspected after {current_fault_type}."
                        })
                        fault_id_counter += 1
                        
                elif act_fid == f_id and t_idx > flt_data["active_until"]:
                    active_faults.pop((start_t, act_fid), None)
            
            # Apply electrical fault dynamics if active
            if is_fault:
                if current_fault_type == "FLT_OVERCURRENT":
                    current_target *= random.uniform(1.35, 1.75)
                elif current_fault_type == "FLT_UNDERVOLT":
                    grid_v_bus *= random.uniform(0.85, 0.92)
                elif current_fault_type == "FLT_OVERVOLT":
                    grid_v_bus *= random.uniform(1.08, 1.14)
                elif current_fault_type == "FLT_IMBALANCE":
                    imbalance_base *= 2.8
            
            # 2. Phase Current Synthesis with realistic unbalance
            # Ensure Ir + Iy + Ib is centered around 3 * current_target
            unbalance_noise = np.random.normal(0, imbalance_base / 100.0, 3)
            unbalance_noise -= unbalance_noise.mean()  # Centered
            
            i_r = max(5.0, round(current_target * (1.0 + unbalance_noise[0]), 2))
            i_y = max(5.0, round(current_target * (1.0 + unbalance_noise[1]), 2))
            i_b = max(5.0, round(current_target * (1.0 + unbalance_noise[2]), 2))
            i_avg = round((i_r + i_y + i_b) / 3.0, 2)
            
            # IEEE Std 141 Current Imbalance calculation:
            max_dev = max(abs(i_r - i_avg), abs(i_y - i_avg), abs(i_b - i_avg))
            i_imbalance_pct = round((max_dev / i_avg) * 100.0, 2) if i_avg > 0 else 0.0
            
            # 3. Voltage drop along feeder: Delta_V = sqrt(3) * I * (R*cos_phi + X*sin_phi)
            pf_val = max(0.68, min(0.99, round(base_pf + np.random.normal(0, 0.015), 3)))
            sin_phi = math.sqrt(max(0.0, 1.0 - pf_val ** 2))
            
            v_drop = (3 ** 0.5) * i_avg * (r_total * pf_val + f["reactance_ohm_per_km"] * f["length_km"] * sin_phi)
            v_feeder_avg = max(9000.0, grid_v_bus - v_drop)
            
            # Phase voltages
            v_noise = np.random.normal(0, 15.0, 3)
            v_r = round(v_feeder_avg + v_noise[0], 1)
            v_y = round(v_feeder_avg + v_noise[1], 1)
            v_b = round(v_feeder_avg + v_noise[2], 1)
            v_avg = round((v_r + v_y + v_b) / 3.0, 1)
            v_dev_pct = round(((v_avg - NOMINAL_VOLTAGE_LL) / NOMINAL_VOLTAGE_LL) * 100.0, 2)
            
            # 4. Power calculations
            # S = sqrt(3) * V * I (kVA)
            s_kva = round((3 ** 0.5) * v_avg * i_avg / 1000.0, 2)
            p_kw = round(s_kva * pf_val, 2)
            q_kvar = round(math.sqrt(max(0.0, s_kva ** 2 - p_kw ** 2)), 2)
            energy_kwh = round(p_kw * INTERVAL_HOURS, 2)
            
            # 5. Technical Conductor Loss: P_loss = (Ir^2 + Iy^2 + Ib^2) * R * 10^-3 (kW)
            feeder_loss_kw = round((i_r ** 2 + i_y ** 2 + i_b ** 2) * r_total / 1000.0, 2)
            input_power_kw = p_kw + feeder_loss_kw
            feeder_loss_pct = round((feeder_loss_kw / input_power_kw) * 100.0, 2) if input_power_kw > 0 else 0.0
            
            # 6. Equipment Temperature
            # Thermal rise = Delta_T_rated * (I / I_rated)^1.8
            current_ratio = i_avg / rated_current
            temp_rise = 28.0 * (current_ratio ** 1.8)
            equip_temp = round(ambient_temp + temp_rise + np.random.normal(0, 0.7), 1)
            
            # 7. Grid Frequency
            freq_hz = round(GRID_FREQUENCY_HZ + np.random.normal(0, 0.035), 2)
            
            # Categorize PF
            if pf_val >= PF_EXCELLENT:
                pf_cat = "Excellent (>=0.95)"
            elif pf_val >= PF_ACCEPTABLE:
                pf_cat = "Acceptable (0.90-0.94)"
            elif pf_val >= PF_POOR:
                pf_cat = "Poor (0.80-0.89)"
            else:
                pf_cat = "Critical (<0.80)"
                
            # Collect for transformer loading calculation
            ts_feeder_kva[f_id] = s_kva
            
            measurement_row = {
                "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
                "date_key": date_key,
                "feeder_id": f_id,
                "substation_id": sub_id,
                "transformer_id": tr_id,
                "load_type_id": load_id,
                "voltage_r": v_r,
                "voltage_y": v_y,
                "voltage_b": v_b,
                "voltage_avg": v_avg,
                "voltage_deviation_pct": v_dev_pct,
                "current_r": i_r,
                "current_y": i_y,
                "current_b": i_b,
                "current_avg": i_avg,
                "current_imbalance_pct": i_imbalance_pct,
                "active_power_kw": p_kw,
                "reactive_power_kvar": q_kvar,
                "apparent_power_kva": s_kva,
                "power_factor": pf_val,
                "pf_category": pf_cat,
                "frequency_hz": freq_hz,
                "feeder_loss_kw": feeder_loss_kw,
                "feeder_loss_pct": feeder_loss_pct,
                "energy_kwh": energy_kwh,
                "ambient_temperature_c": ambient_temp,
                "equipment_temperature_c": equip_temp,
                "fault_status": 1 if is_fault else 0,
                "fault_type_id": current_fault_type if is_fault else "NONE",
                "maintenance_flag": 1 if (is_fault and current_fault_type in ["FLT_TR_OVERLOAD", "FLT_OVERCURRENT"]) else 0,
                "is_synthetic_defect": 0
            }
            ts_feeder_measurements.append(measurement_row)
            
        # Compute Transformer Loading % at this timestamp
        for tr in TRANSFORMERS:
            tr_id = tr["transformer_id"]
            tr_capacity_kva = tr["rated_mva"] * 1000.0
            sum_kva = sum(ts_feeder_kva[fid] for fid in tr_feeders.get(tr_id, []))
            tr_loading_pct = round((sum_kva / tr_capacity_kva) * 100.0, 2)
            
            # Assign loading to all feeder records connected to this transformer
            for m in ts_feeder_measurements:
                if m["transformer_id"] == tr_id:
                    m["transformer_loading_pct"] = tr_loading_pct
                    
        records.extend(ts_feeder_measurements)
        
    df_measurements = pd.DataFrame(records)
    df_faults = pd.DataFrame(fault_events)
    
    # Generate Fact Maintenance based on critical faults and scheduled PM
    df_maintenance = _generate_maintenance_records(df_faults)
    
    # Controlled Data Quality Defect Injection (~1.2% realistic sensor and communication errors)
    if inject_defects:
        df_measurements = _inject_controlled_data_defects(df_measurements)
        
    print(f"Generated {len(df_measurements):,} measurement records, {len(df_faults)} fault events, and {len(df_maintenance)} maintenance work orders.")
    return df_measurements, df_faults, df_maintenance


def _inject_controlled_data_defects(df: pd.DataFrame) -> pd.DataFrame:
    """
    Injects ~1.2% controlled, realistic telemetry defects:
    - Missing telemetry values (communication dropouts)
    - Out-of-bounds voltages (PT transducer failure)
    - Inverted / invalid power factors (transducer wiring glitch)
    - Frozen zero current / negative active power glitches
    - Duplicate timestamps
    """
    df = df.copy()
    total_len = len(df)
    
    # 1. Missing telemetry (dropouts) ~0.35%
    missing_indices = np.random.choice(df.index, size=int(total_len * 0.0035), replace=False)
    df.loc[missing_indices, "voltage_r"] = np.nan
    df.loc[missing_indices, "current_avg"] = np.nan
    df.loc[missing_indices, "is_synthetic_defect"] = 1
    
    # 2. Out-of-bounds voltage spike ~0.15% (e.g. 16500V or 420V)
    v_spike_indices = np.random.choice(df.index, size=int(total_len * 0.0015), replace=False)
    for idx in v_spike_indices:
        df.loc[idx, "voltage_avg"] = random.choice([415.0, 16800.0, 0.0])
        df.loc[idx, "is_synthetic_defect"] = 1
        
    # 3. Invalid Power Factor (> 1.0 or negative) ~0.20%
    pf_defect_indices = np.random.choice(df.index, size=int(total_len * 0.0020), replace=False)
    for idx in pf_defect_indices:
        df.loc[idx, "power_factor"] = random.choice([-0.82, 1.45, 2.10, -0.15])
        df.loc[idx, "is_synthetic_defect"] = 1
        
    # 4. Inconsistent calculated power ~0.20%
    power_mismatch_indices = np.random.choice(df.index, size=int(total_len * 0.0020), replace=False)
    for idx in power_mismatch_indices:
        df.loc[idx, "active_power_kw"] = df.loc[idx, "apparent_power_kva"] * 2.5  # Impossible P > S!
        df.loc[idx, "is_synthetic_defect"] = 1
        
    # 5. Duplicate records injection (~150 rows)
    dup_indices = np.random.choice(df.index, size=150, replace=False)
    duplicates = df.loc[dup_indices].copy()
    duplicates["is_synthetic_defect"] = 1
    df = pd.concat([df, duplicates], ignore_index=True)
    
    return df


def _generate_maintenance_records(df_faults: pd.DataFrame) -> pd.DataFrame:
    """
    Generates historical maintenance records tied to fault events and routine preventive schedules.
    """
    maint_records = []
    maint_id = 5001
    
    # Unscheduled corrective maintenance for severe faults
    severe_faults = df_faults[df_faults["maintenance_required"] == 1]
    for _, f in severe_faults.iterrows():
        f_time = pd.to_datetime(f["timestamp"])
        m_time = f_time + timedelta(hours=random.randint(2, 24))
        
        maint_records.append({
            "maintenance_id": f"MNT_{maint_id}",
            "maintenance_date": m_time.strftime("%Y-%m-%d"),
            "timestamp": m_time.strftime("%Y-%m-%d %H:%M:%S"),
            "feeder_id": f["feeder_id"],
            "transformer_id": f["transformer_id"],
            "maintenance_type": "Corrective / Emergency",
            "priority": "High" if f["severity_score"] >= 80 else "Medium",
            "cost_usd": round(random.uniform(450.0, 3200.0), 2),
            "downtime_hours": round(f["duration_minutes"] / 60.0 + random.uniform(0.5, 3.0), 1),
            "work_order_no": f"WO-{m_time.strftime('%Y%m')}-{maint_id}",
            "description": f"Post-fault inspection & remediation following {f['fault_type_id']}. {f['resolution_notes']}",
            "technician_lead": random.choice(["E. Harrison (Sr. Relay Eng.)", "K. Patel (Substation Lead)", "M. Becker (Protection Eng.)"])
        })
        maint_id += 1
        
    # Routine preventive maintenance (transformers and feeder switchgear)
    for tr in TRANSFORMERS:
        for m_month in [3, 5, 7]:
            m_date = datetime(2026, m_month, random.randint(5, 25), 10, 0, 0)
            maint_records.append({
                "maintenance_id": f"MNT_{maint_id}",
                "maintenance_date": m_date.strftime("%Y-%m-%d"),
                "timestamp": m_date.strftime("%Y-%m-%d %H:%M:%S"),
                "feeder_id": "SUBSTATION_LEVEL",
                "transformer_id": tr["transformer_id"],
                "maintenance_type": "Preventive / Condition Monitoring",
                "priority": "Routine",
                "cost_usd": round(random.uniform(250.0, 850.0), 2),
                "downtime_hours": round(random.uniform(1.0, 4.0), 1),
                "work_order_no": f"WO-PM-{m_date.strftime('%Y%m')}-{maint_id}",
                "description": f"Quarterly DGA oil sampling, bushing cleaning, and OLTC contact check for {tr['transformer_name']}.",
                "technician_lead": "A. Sharma (Transformer Specialist)"
            })
            maint_id += 1
            
    return pd.DataFrame(maint_records)
