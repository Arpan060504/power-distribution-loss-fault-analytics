-- =====================================================================
-- POWER DISTRIBUTION LOSS & FAULT ANALYTICS SYSTEM
-- ADVANCED ANALYTICAL SQL SUITE (25 Production-Grade Queries)
-- Compatible with PostgreSQL and SQLite
-- =====================================================================

-- =====================================================================
-- SECTION 1: FEEDER PERFORMANCE & LOSS RANKINGS
-- =====================================================================

-- Query 1: Comprehensive Feeder Energy & Loss Performance Scorecard
-- Calculates total delivered energy, cumulative technical losses, average loss %, and power factor.
SELECT 
    f.feeder_id,
    f.feeder_code,
    f.feeder_name,
    f.load_category,
    f.total_resistance_ohm,
    ROUND(SUM(m.energy_kwh) / 1000.0, 2) AS total_delivered_mwh,
    ROUND(SUM(m.feeder_loss_kw * 0.5) / 1000.0, 2) AS total_feeder_loss_mwh,
    ROUND(AVG(m.feeder_loss_pct), 2) AS avg_loss_pct,
    ROUND(MAX(m.feeder_loss_pct), 2) AS peak_loss_pct,
    ROUND(AVG(m.power_factor), 3) AS avg_power_factor,
    ROUND(AVG(m.current_avg), 1) AS avg_current_a,
    ROUND(MAX(m.current_avg), 1) AS peak_current_a
FROM fact_electrical_measurements m
JOIN dim_feeder f ON m.feeder_id = f.feeder_id
GROUP BY f.feeder_id, f.feeder_code, f.feeder_name, f.load_category, f.total_resistance_ohm
ORDER BY total_feeder_loss_mwh DESC;


-- Query 2: Feeder Technical Loss Ranking using DENSE_RANK Window Function
-- Partitions feeders by load category and ranks them by average loss percentage.
WITH FeederCategoryLoss AS (
    SELECT 
        f.load_category,
        f.feeder_id,
        f.feeder_name,
        ROUND(AVG(m.feeder_loss_pct), 2) AS avg_loss_pct,
        ROUND(SUM(m.feeder_loss_kw * 0.5) / 1000.0, 2) AS total_loss_mwh
    FROM fact_electrical_measurements m
    JOIN dim_feeder f ON m.feeder_id = f.feeder_id
    GROUP BY f.load_category, f.feeder_id, f.feeder_name
)
SELECT 
    load_category,
    feeder_id,
    feeder_name,
    avg_loss_pct,
    total_loss_mwh,
    DENSE_RANK() OVER (PARTITION BY load_category ORDER BY avg_loss_pct DESC) AS rank_within_category,
    DENSE_RANK() OVER (ORDER BY avg_loss_pct DESC) AS global_loss_rank
FROM FeederCategoryLoss
ORDER BY global_loss_rank;


-- Query 3: Peak vs Off-Peak Loading & Conductor Loss Comparison
-- Categorizes intervals into Peak (18:00-22:30), Daytime (08:30-18:00), and Night (23:00-08:00).
WITH IntervalBuckets AS (
    SELECT 
        feeder_id,
        CASE 
            WHEN CAST(STRFTIME('%H', timestamp) AS INTEGER) BETWEEN 18 AND 22 THEN 'Peak Hours (18-22h)'
            WHEN CAST(STRFTIME('%H', timestamp) AS INTEGER) BETWEEN 8 AND 17 THEN 'Business / Daytime (08-17h)'
            ELSE 'Off-Peak / Night (23-07h)'
        END AS time_bucket,
        current_avg,
        active_power_kw,
        feeder_loss_kw,
        feeder_loss_pct
    FROM fact_electrical_measurements
)
SELECT 
    feeder_id,
    time_bucket,
    ROUND(AVG(current_avg), 1) AS avg_current_a,
    ROUND(AVG(active_power_kw), 1) AS avg_active_kw,
    ROUND(SUM(feeder_loss_kw * 0.5) / 1000.0, 2) AS loss_mwh,
    ROUND(AVG(feeder_loss_pct), 2) AS avg_loss_pct
FROM IntervalBuckets
GROUP BY feeder_id, time_bucket
ORDER BY feeder_id, avg_loss_pct DESC;


-- Query 4: 7-Day Rolling Moving Average of Feeder Conductor Losses
-- Evaluates loss trends across time using a window frame of preceding intervals.
WITH DailyFeederLoss AS (
    SELECT 
        feeder_id,
        SUBSTR(timestamp, 1, 10) AS log_date,
        ROUND(SUM(feeder_loss_kw * 0.5) / 1000.0, 3) AS daily_loss_mwh,
        ROUND(AVG(current_avg), 1) AS daily_avg_current
    FROM fact_electrical_measurements
    GROUP BY feeder_id, SUBSTR(timestamp, 1, 10)
)
SELECT 
    feeder_id,
    log_date,
    daily_loss_mwh,
    ROUND(AVG(daily_loss_mwh) OVER (
        PARTITION BY feeder_id 
        ORDER BY log_date 
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ), 3) AS rolling_7d_loss_mwh,
    daily_avg_current,
    ROUND(AVG(daily_avg_current) OVER (
        PARTITION BY feeder_id 
        ORDER BY log_date 
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ), 1) AS rolling_7d_avg_current
FROM DailyFeederLoss
ORDER BY feeder_id, log_date DESC;


-- Query 5: Month-over-Month Energy and Conductor Loss Growth Rate using LAG
-- Quantifies monthly progression in feeder losses and demand.
WITH MonthlyStats AS (
    SELECT 
        f.feeder_id,
        c.month_name,
        c.month,
        ROUND(SUM(m.energy_kwh) / 1000.0, 1) AS monthly_energy_mwh,
        ROUND(SUM(m.feeder_loss_kw * 0.5) / 1000.0, 2) AS monthly_loss_mwh
    FROM fact_electrical_measurements m
    JOIN dim_calendar c ON m.date_key = c.date_key
    JOIN dim_feeder f ON m.feeder_id = f.feeder_id
    GROUP BY f.feeder_id, c.month, c.month_name
)
SELECT 
    feeder_id,
    month_name,
    monthly_energy_mwh,
    LAG(monthly_energy_mwh) OVER (PARTITION BY feeder_id ORDER BY month) AS prev_month_energy_mwh,
    monthly_loss_mwh,
    LAG(monthly_loss_mwh) OVER (PARTITION BY feeder_id ORDER BY month) AS prev_month_loss_mwh,
    ROUND(
        (monthly_loss_mwh - LAG(monthly_loss_mwh) OVER (PARTITION BY feeder_id ORDER BY month)) /
        NULLIF(LAG(monthly_loss_mwh) OVER (PARTITION BY feeder_id ORDER BY month), 0) * 100.0, 
        2
    ) AS mom_loss_growth_pct
FROM MonthlyStats
ORDER BY feeder_id, month;


-- =====================================================================
-- SECTION 2: TRANSFORMER LOADING & ASSET UTILIZATION
-- =====================================================================

-- Query 6: Transformer Loading Profile, Utilization Tiers, and Overload Audit
-- Groups transformer operation into Under-utilized (<40%), Optimal (40-80%), High (80-100%), and Overload (>100%).
SELECT 
    t.transformer_id,
    t.transformer_name,
    t.rated_mva,
    ROUND(AVG(m.transformer_loading_pct), 2) AS avg_loading_pct,
    ROUND(MAX(m.transformer_loading_pct), 2) AS peak_loading_pct,
    ROUND(MIN(m.transformer_loading_pct), 2) AS min_loading_pct,
    SUM(CASE WHEN m.transformer_loading_pct > 100.0 THEN 1 ELSE 0 END) AS overload_interval_count,
    ROUND(SUM(CASE WHEN m.transformer_loading_pct > 100.0 THEN 1 ELSE 0 END) * 0.5, 1) AS overload_hours,
    SUM(CASE WHEN m.transformer_loading_pct BETWEEN 80.0 AND 100.0 THEN 1 ELSE 0 END) AS high_loading_interval_count,
    SUM(CASE WHEN m.transformer_loading_pct < 40.0 THEN 1 ELSE 0 END) AS underutilized_interval_count
FROM fact_electrical_measurements m
JOIN dim_transformer t ON m.transformer_id = t.transformer_id
GROUP BY t.transformer_id, t.transformer_name, t.rated_mva
ORDER BY peak_loading_pct DESC;


-- Query 7: Daily Peak Loading Time for Each Transformer using ROW_NUMBER
-- Pinpoints the exact hour and measurement when each transformer reached its highest daily stress.
WITH RankedDailyLoads AS (
    SELECT 
        m.transformer_id,
        SUBSTR(m.timestamp, 1, 10) AS log_date,
        m.timestamp,
        m.transformer_loading_pct,
        m.apparent_power_kva,
        ROW_NUMBER() OVER (
            PARTITION BY m.transformer_id, SUBSTR(m.timestamp, 1, 10) 
            ORDER BY m.transformer_loading_pct DESC
        ) AS rank_order
    FROM fact_electrical_measurements m
)
SELECT 
    transformer_id,
    log_date,
    timestamp AS peak_timestamp,
    transformer_loading_pct AS peak_loading_pct,
    apparent_power_kva AS peak_kva
FROM RankedDailyLoads
WHERE rank_order = 1
ORDER BY peak_loading_pct DESC
LIMIT 20;


-- Query 8: Coincident Peak Demand and Substation Transformer Loading
-- Aggregates simultaneous demand across transformers to evaluate substation head-room.
SELECT 
    s.substation_name,
    c.month_name,
    ROUND(AVG(m.apparent_power_kva), 1) AS avg_substation_demand_kva,
    ROUND(MAX(m.apparent_power_kva), 1) AS peak_coincident_demand_kva,
    ROUND(AVG(m.transformer_loading_pct), 2) AS avg_transformer_stress_pct,
    ROUND(MAX(m.transformer_loading_pct), 2) AS max_transformer_stress_pct
FROM fact_electrical_measurements m
JOIN dim_substation s ON m.substation_id = s.substation_id
JOIN dim_calendar c ON m.date_key = c.date_key
GROUP BY s.substation_name, c.month, c.month_name
ORDER BY s.substation_name, c.month;


-- =====================================================================
-- SECTION 3: POWER QUALITY, IMBALANCE & VOLTAGE ANOMALIES
-- =====================================================================

-- Query 9: Chronic Phase Current Imbalance Audit (IEEE Std 141 Compliance)
-- Flags feeders exhibiting chronic imbalance > 5% and severe imbalance > 10%.
SELECT 
    f.feeder_id,
    f.feeder_name,
    f.load_category,
    ROUND(AVG(m.current_imbalance_pct), 2) AS avg_imbalance_pct,
    ROUND(MAX(m.current_imbalance_pct), 2) AS peak_imbalance_pct,
    SUM(CASE WHEN m.current_imbalance_pct > 10.0 THEN 1 ELSE 0 END) AS severe_unbalance_intervals,
    ROUND(SUM(CASE WHEN m.current_imbalance_pct > 10.0 THEN 1 ELSE 0 END) * 0.5, 1) AS severe_unbalance_hours,
    ROUND(
        SUM(CASE WHEN m.current_imbalance_pct > 5.0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 
        2
    ) AS pct_time_in_unbalance
FROM fact_electrical_measurements m
JOIN dim_feeder f ON m.feeder_id = f.feeder_id
GROUP BY f.feeder_id, f.feeder_name, f.load_category
ORDER BY avg_imbalance_pct DESC;


-- Query 10: Voltage Deviation Distribution & IEEE 1159 Quality Band Violations
-- Aggregates intervals in Overvoltage (>+5%), Undervoltage (<-5%), and Critical Sags (<-10%).
SELECT 
    m.feeder_id,
    f.feeder_name,
    COUNT(*) AS total_intervals,
    SUM(CASE WHEN m.voltage_deviation_pct > 5.0 THEN 1 ELSE 0 END) AS overvoltage_intervals,
    SUM(CASE WHEN m.voltage_deviation_pct BETWEEN -5.0 AND 5.0 THEN 1 ELSE 0 END) AS normal_voltage_intervals,
    SUM(CASE WHEN m.voltage_deviation_pct BETWEEN -10.0 AND -5.0 THEN 1 ELSE 0 END) AS undervoltage_intervals,
    SUM(CASE WHEN m.voltage_deviation_pct < -10.0 THEN 1 ELSE 0 END) AS critical_sag_intervals,
    ROUND(
        SUM(CASE WHEN m.voltage_deviation_pct NOT BETWEEN -5.0 AND 5.0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 
        2
    ) AS voltage_noncompliance_pct
FROM fact_electrical_measurements m
JOIN dim_feeder f ON m.feeder_id = f.feeder_id
GROUP BY m.feeder_id, f.feeder_name
ORDER BY voltage_noncompliance_pct DESC;


-- Query 11: Power Factor Compliance and Commercial Penalty Exposure
-- Calculates the duration feeders operated below the commercial 0.85 PF penalty threshold.
SELECT 
    f.feeder_id,
    f.feeder_name,
    f.load_category,
    ROUND(AVG(m.power_factor), 3) AS avg_pf,
    ROUND(MIN(m.power_factor), 3) AS min_pf,
    SUM(CASE WHEN m.power_factor < 0.85 THEN 1 ELSE 0 END) AS penalty_interval_count,
    ROUND(SUM(CASE WHEN m.power_factor < 0.85 THEN 1 ELSE 0 END) * 0.5, 1) AS penalty_exposure_hours,
    ROUND(SUM(CASE WHEN m.power_factor < 0.85 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS penalty_time_pct,
    ROUND(AVG(m.reactive_power_kvar), 1) AS avg_reactive_demand_kvar
FROM fact_electrical_measurements m
JOIN dim_feeder f ON m.feeder_id = f.feeder_id
GROUP BY f.feeder_id, f.feeder_name, f.load_category
ORDER BY penalty_interval_count DESC;


-- Query 12: Simultaneous Low Power Factor and High Thermal Rise Correlation
-- Explores whether poor PF directly contributes to conductor overheating.
SELECT 
    m.pf_category,
    COUNT(*) AS interval_count,
    ROUND(AVG(m.current_avg), 1) AS avg_current_a,
    ROUND(AVG(m.thermal_rise_c), 1) AS avg_thermal_rise_c,
    ROUND(MAX(m.equipment_temperature_c), 1) AS max_equipment_temp_c,
    ROUND(AVG(m.feeder_loss_pct), 2) AS avg_loss_pct
FROM fact_electrical_measurements m
GROUP BY m.pf_category
ORDER BY avg_loss_pct DESC;


-- =====================================================================
-- SECTION 4: FAULT ANALYTICS & RELIABILITY METRICS
-- =====================================================================

-- Query 13: Distribution Fault Epidemiology by Fault Type & Severity Score
-- Analyzes frequency, average severity score, and cumulative outage downtime.
SELECT 
    flt.fault_type_id,
    flt.fault_name,
    flt.category AS fault_category,
    COUNT(e.event_id) AS total_incidents,
    ROUND(AVG(e.severity_score), 1) AS avg_severity_score,
    ROUND(MAX(e.severity_score), 1) AS peak_severity_score,
    ROUND(AVG(e.duration_minutes), 1) AS avg_duration_mins,
    ROUND(SUM(e.duration_minutes) / 60.0, 1) AS total_downtime_hours,
    ROUND(AVG(e.voltage_sag_pct), 1) AS avg_voltage_sag_pct,
    SUM(e.maintenance_required) AS corrective_work_orders_triggered
FROM fact_fault_events e
JOIN dim_fault flt ON e.fault_type_id = flt.fault_type_id
GROUP BY flt.fault_type_id, flt.fault_name, flt.category
ORDER BY total_incidents DESC;


-- Query 14: Feeder Fault Concentration & Mean Time Between Failures (MTBF)
-- Ranks feeders by fault trip frequency and calculates approximate MTBF.
WITH FeederFaultStats AS (
    SELECT 
        feeder_id,
        COUNT(event_id) AS total_faults,
        ROUND(AVG(severity_score), 1) AS avg_severity,
        ROUND(SUM(duration_minutes) / 60.0, 1) AS cumulative_downtime_hours
    FROM fact_fault_events
    GROUP BY feeder_id
)
SELECT 
    f.feeder_id,
    f.feeder_name,
    f.load_category,
    COALESCE(s.total_faults, 0) AS total_fault_trips,
    COALESCE(s.avg_severity, 0) AS avg_fault_severity,
    COALESCE(s.cumulative_downtime_hours, 0) AS cumulative_downtime_hours,
    ROUND(182.0 * 24.0 / NULLIF(COALESCE(s.total_faults, 0), 0), 1) AS mtbf_hours
FROM dim_feeder f
LEFT JOIN FeederFaultStats s ON f.feeder_id = s.feeder_id
ORDER BY total_fault_trips DESC;


-- Query 15: Monthly Fault Trends & Seasonal Escalation
-- Evaluates how faults correlate with summer pre-monsoon heat vs monsoon weather.
SELECT 
    c.year,
    c.month,
    c.month_name,
    c.season,
    COUNT(e.event_id) AS monthly_fault_count,
    ROUND(AVG(e.severity_score), 1) AS avg_monthly_severity,
    ROUND(SUM(e.duration_minutes) / 60.0, 1) AS total_downtime_hours,
    SUM(CASE WHEN e.fault_type_id = 'FLT_OVERCURRENT' THEN 1 ELSE 0 END) AS overcurrent_trips,
    SUM(CASE WHEN e.fault_type_id = 'FLT_UNDERVOLT' THEN 1 ELSE 0 END) AS voltage_sags,
    SUM(CASE WHEN e.fault_type_id = 'FLT_TR_OVERLOAD' THEN 1 ELSE 0 END) AS tr_overloads
FROM fact_fault_events e
JOIN dim_calendar c ON e.date_key = c.date_key
GROUP BY c.year, c.month, c.month_name, c.season
ORDER BY c.year, c.month;


-- Query 16: Consecutive Fault Recurrence Detection using LAG and Window Duration
-- Identifies feeders experiencing rapid recurring faults (< 72 hours between incidents).
WITH FaultIntervals AS (
    SELECT 
        event_id,
        feeder_id,
        fault_type_id,
        timestamp,
        severity_score,
        LAG(timestamp) OVER (PARTITION BY feeder_id ORDER BY timestamp) AS prev_fault_timestamp
    FROM fact_fault_events
)
SELECT 
    feeder_id,
    fault_type_id,
    timestamp AS current_fault_time,
    prev_fault_timestamp,
    ROUND(
        (JULIANDAY(timestamp) - JULIANDAY(prev_fault_timestamp)) * 24.0, 
        1
    ) AS hours_since_last_fault,
    severity_score
FROM FaultIntervals
WHERE prev_fault_timestamp IS NOT NULL
  AND (JULIANDAY(timestamp) - JULIANDAY(prev_fault_timestamp)) * 24.0 <= 72.0
ORDER BY hours_since_last_fault ASC;


-- =====================================================================
-- SECTION 5: ANOMALY DETECTION BENCHMARKING (STATISTICAL VS ML)
-- =====================================================================

-- Query 17: Anomaly Detection Engine Consensus Analysis
-- Quantifies overlap between Statistical Z-Score and Machine Learning Isolation Forest.
SELECT 
    anomaly_consensus,
    anomaly_type_engineering,
    COUNT(*) AS record_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM fact_electrical_measurements), 2) AS pct_of_total_dataset,
    ROUND(AVG(current_avg), 1) AS avg_current_a,
    ROUND(AVG(voltage_avg), 1) AS avg_voltage_v,
    ROUND(AVG(feeder_loss_pct), 2) AS avg_loss_pct,
    ROUND(AVG(equipment_temperature_c), 1) AS avg_equip_temp_c
FROM fact_electrical_measurements
GROUP BY anomaly_consensus, anomaly_type_engineering
ORDER BY record_count DESC;


-- Query 18: Anomaly Attribution Breakdown (Why Statistical Outliers Were Flagged)
-- Groups statistical anomaly explanations to identify primary physical drivers.
SELECT 
    CASE 
        WHEN stat_anomaly_reason LIKE '%Current Spike%' THEN 'Current Spike Surge'
        WHEN stat_anomaly_reason LIKE '%Voltage Sag%' THEN 'Voltage Sag / Undervoltage'
        WHEN stat_anomaly_reason LIKE '%Thermal Hotspot%' THEN 'Thermal Hotspot'
        WHEN stat_anomaly_reason LIKE '%Severe Unbalance%' THEN 'Phase Unbalance'
        WHEN stat_anomaly_reason LIKE '%Elevated Loss%' THEN 'Excessive Technical Loss'
        ELSE 'Normal Operating Range'
    END AS primary_anomaly_driver,
    COUNT(*) AS total_flagged_intervals,
    ROUND(AVG(feeder_loss_pct), 2) AS avg_feeder_loss_pct,
    ROUND(AVG(thermal_rise_c), 1) AS avg_thermal_rise_c
FROM fact_electrical_measurements
WHERE stat_anomaly_flag = 1
GROUP BY primary_anomaly_driver
ORDER BY total_flagged_intervals DESC;


-- Query 19: High-Risk Feeder Anomaly Density
-- Evaluates which feeders have the highest concentration of confirmed anomalies.
SELECT 
    m.feeder_id,
    f.feeder_name,
    f.load_category,
    COUNT(*) AS total_records,
    SUM(m.stat_anomaly_flag) AS stat_anomalies,
    SUM(m.ml_anomaly_flag) AS ml_anomalies,
    SUM(CASE WHEN m.anomaly_consensus LIKE '%Dual-Method%' THEN 1 ELSE 0 END) AS high_confidence_anomalies,
    ROUND(
        SUM(CASE WHEN m.anomaly_consensus LIKE '%Dual-Method%' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 
        2
    ) AS high_confidence_anomaly_pct
FROM fact_electrical_measurements m
JOIN dim_feeder f ON m.feeder_id = f.feeder_id
GROUP BY m.feeder_id, f.feeder_name, f.load_category
ORDER BY high_confidence_anomalies DESC;


-- =====================================================================
-- SECTION 6: HIGH-RISK FEEDER COMPOSITE INDEX & MAINTENANCE INTELLIGENCE
-- =====================================================================

-- Query 20: Composite Feeder Risk Ranking Matrix
-- Combines loss percentage, fault count, chronic unbalance, and thermal stress into a unified composite score.
WITH FeederLossSummary AS (
    SELECT feeder_id, AVG(feeder_loss_pct) AS avg_loss, AVG(current_imbalance_pct) AS avg_imb, AVG(thermal_rise_c) AS avg_therm
    FROM fact_electrical_measurements GROUP BY feeder_id
),
FeederFaultSummary AS (
    SELECT feeder_id, COUNT(event_id) AS fault_count, AVG(severity_score) AS avg_sev
    FROM fact_fault_events GROUP BY feeder_id
)
SELECT 
    f.feeder_id,
    f.feeder_name,
    f.load_category,
    ROUND(l.avg_loss, 2) AS avg_loss_pct,
    ROUND(l.avg_imb, 2) AS avg_unbalance_pct,
    COALESCE(flt.fault_count, 0) AS total_faults,
    ROUND(l.avg_therm, 1) AS avg_thermal_rise_c,
    ROUND(
        (l.avg_loss * 5.0) + 
        (l.avg_imb * 3.0) + 
        (COALESCE(flt.fault_count, 0) * 2.0) + 
        (l.avg_therm * 1.5), 
        1
    ) AS composite_risk_score,
    DENSE_RANK() OVER (
        ORDER BY (l.avg_loss * 5.0) + (l.avg_imb * 3.0) + (COALESCE(flt.fault_count, 0) * 2.0) + (l.avg_therm * 1.5) DESC
    ) AS risk_rank
FROM dim_feeder f
JOIN FeederLossSummary l ON f.feeder_id = l.feeder_id
LEFT JOIN FeederFaultSummary flt ON f.feeder_id = flt.feeder_id
ORDER BY risk_rank;


-- Query 21: Corrective Maintenance Downtime and Expenditure by Asset
-- Summarizes total maintenance dollars spent and equipment downtime.
SELECT 
    maint.transformer_id,
    t.transformer_name,
    maint.maintenance_type,
    COUNT(maint.maintenance_id) AS work_order_count,
    ROUND(SUM(maint.cost_usd), 2) AS total_expenditure_usd,
    ROUND(SUM(maint.downtime_hours), 1) AS total_downtime_hours,
    ROUND(AVG(maint.cost_usd), 2) AS avg_work_order_cost_usd
FROM fact_maintenance maint
JOIN dim_transformer t ON maint.transformer_id = t.transformer_id
GROUP BY maint.transformer_id, t.transformer_name, maint.maintenance_type
ORDER BY total_expenditure_usd DESC;


-- Query 22: Conductor Loss vs Square of Current (Empirical Verification of Loss ∝ I²)
-- Aggregates current into 25 Ampere deciles and computes mean conductor loss to prove quadratic proportionality.
SELECT 
    ROUND(current_avg / 25.0) * 25 AS current_bin_a,
    COUNT(*) AS observations,
    ROUND(AVG(current_avg), 1) AS avg_i,
    ROUND(AVG(current_avg * current_avg), 1) AS avg_i_squared,
    ROUND(AVG(feeder_loss_kw), 2) AS avg_loss_kw,
    ROUND(AVG(feeder_loss_kw) / NULLIF(AVG(current_avg * current_avg), 0) * 1000.0, 4) AS empirical_r_factor
FROM fact_electrical_measurements
GROUP BY ROUND(current_avg / 25.0) * 25
HAVING COUNT(*) > 50
ORDER BY current_bin_a;


-- Query 23: Top 10 Most Severe Fault Incidents with Transformer Association
-- Retrieves the highest severity incidents requiring immediate root-cause inspection.
SELECT 
    e.event_id,
    e.timestamp,
    e.feeder_id,
    f.feeder_name,
    e.transformer_id,
    e.fault_type_id,
    e.severity_score,
    e.peak_current_a,
    e.voltage_sag_pct,
    e.duration_minutes,
    e.root_cause_category,
    e.maintenance_required
FROM fact_fault_events e
JOIN dim_feeder f ON e.feeder_id = f.feeder_id
ORDER BY e.severity_score DESC
LIMIT 10;


-- Query 24: Day-of-Week Load & Loss Variance Analysis
-- Compares weekday industrial demand against weekend residential and commercial shifts.
SELECT 
    c.day_name,
    c.is_weekend,
    ROUND(AVG(m.active_power_kw), 1) AS avg_active_power_kw,
    ROUND(AVG(m.apparent_power_kva), 1) AS avg_apparent_power_kva,
    ROUND(AVG(m.power_factor), 3) AS avg_pf,
    ROUND(AVG(m.feeder_loss_pct), 2) AS avg_loss_pct,
    ROUND(SUM(m.feeder_loss_kw * 0.5) / 1000.0, 2) AS total_loss_mwh
FROM fact_electrical_measurements m
JOIN dim_calendar c ON m.date_key = c.date_key
GROUP BY c.day_of_week, c.day_name, c.is_weekend
ORDER BY c.day_of_week;


-- Query 25: Hourly System-Wide Load & Conductor Loss Heatmap Aggregation
-- Provides matrix aggregation for 24-hour diurnal loss profiling.
SELECT 
    CAST(STRFTIME('%H', timestamp) AS INTEGER) AS hour_of_day,
    ROUND(AVG(active_power_kw), 1) AS avg_system_active_power_kw,
    ROUND(AVG(reactive_power_kvar), 1) AS avg_system_reactive_kvar,
    ROUND(AVG(feeder_loss_kw), 2) AS avg_conductor_loss_kw,
    ROUND(AVG(feeder_loss_pct), 2) AS avg_conductor_loss_pct,
    ROUND(AVG(transformer_loading_pct), 1) AS avg_transformer_loading_pct
FROM fact_electrical_measurements
GROUP BY CAST(STRFTIME('%H', timestamp) AS INTEGER)
ORDER BY hour_of_day;
