-- =====================================================================
-- POWER DISTRIBUTION LOSS & FAULT ANALYTICS SYSTEM
-- RELATIONAL DATABASE SCHEMA (PostgreSQL / SQLite Compatible DDL)
-- =====================================================================

-- 1. DIMENSION TABLES

CREATE TABLE IF NOT EXISTS dim_substation (
    substation_id VARCHAR(20) PRIMARY KEY,
    substation_name VARCHAR(100) NOT NULL,
    region VARCHAR(100) NOT NULL,
    incoming_voltage_kv NUMERIC(5,2) NOT NULL,
    bus_configuration VARCHAR(100) NOT NULL,
    total_capacity_mva NUMERIC(5,2) NOT NULL,
    commissioned_year INTEGER NOT NULL,
    latitude NUMERIC(9,6),
    longitude NUMERIC(9,6)
);

CREATE TABLE IF NOT EXISTS dim_transformer (
    transformer_id VARCHAR(20) PRIMARY KEY,
    substation_id VARCHAR(20) NOT NULL,
    transformer_name VARCHAR(100) NOT NULL,
    rated_mva NUMERIC(5,2) NOT NULL,
    primary_voltage_kv NUMERIC(5,2) NOT NULL,
    secondary_voltage_kv NUMERIC(5,2) NOT NULL,
    vector_group VARCHAR(20) NOT NULL,
    impedance_pct NUMERIC(4,2) NOT NULL,
    no_load_loss_kw NUMERIC(6,2) NOT NULL,
    full_load_loss_kw NUMERIC(6,2) NOT NULL,
    cooling_type VARCHAR(20) NOT NULL,
    rated_secondary_current_a NUMERIC(7,2) NOT NULL,
    FOREIGN KEY (substation_id) REFERENCES dim_substation(substation_id)
);

CREATE TABLE IF NOT EXISTS dim_feeder (
    feeder_id VARCHAR(20) PRIMARY KEY,
    feeder_code VARCHAR(20) NOT NULL,
    transformer_id VARCHAR(20) NOT NULL,
    substation_id VARCHAR(20) NOT NULL,
    feeder_name VARCHAR(120) NOT NULL,
    load_type_id VARCHAR(30) NOT NULL,
    load_category VARCHAR(60) NOT NULL,
    length_km NUMERIC(5,2) NOT NULL,
    conductor_type VARCHAR(60) NOT NULL,
    resistance_ohm_per_km NUMERIC(6,4) NOT NULL,
    reactance_ohm_per_km NUMERIC(6,4) NOT NULL,
    total_resistance_ohm NUMERIC(6,4) NOT NULL,
    rated_current_a NUMERIC(7,2) NOT NULL,
    nominal_voltage_v NUMERIC(7,2) NOT NULL,
    baseline_current_a NUMERIC(7,2) NOT NULL,
    base_pf NUMERIC(4,3) NOT NULL,
    phase_imbalance_base NUMERIC(4,2) NOT NULL,
    FOREIGN KEY (transformer_id) REFERENCES dim_transformer(transformer_id),
    FOREIGN KEY (substation_id) REFERENCES dim_substation(substation_id),
    FOREIGN KEY (load_type_id) REFERENCES dim_load(load_type_id)
);

CREATE TABLE IF NOT EXISTS dim_load (
    load_type_id VARCHAR(30) PRIMARY KEY,
    load_category VARCHAR(60) NOT NULL,
    typical_pf_min NUMERIC(4,3) NOT NULL,
    typical_pf_max NUMERIC(4,3) NOT NULL,
    harmonic_profile VARCHAR(100),
    sensitivity_level VARCHAR(30),
    description TEXT
);

CREATE TABLE IF NOT EXISTS dim_fault (
    fault_type_id VARCHAR(30) PRIMARY KEY,
    fault_name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    default_severity VARCHAR(20) NOT NULL,
    standard_action TEXT,
    ieee_code VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS dim_calendar (
    date_key INTEGER PRIMARY KEY,
    full_date DATE NOT NULL,
    year INTEGER NOT NULL,
    quarter VARCHAR(5) NOT NULL,
    month INTEGER NOT NULL,
    month_name VARCHAR(20) NOT NULL,
    day INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL,
    day_name VARCHAR(15) NOT NULL,
    is_weekend INTEGER NOT NULL,
    season VARCHAR(40) NOT NULL
);

-- 2. FACT TABLES

CREATE TABLE IF NOT EXISTS fact_electrical_measurements (
    measurement_id VARCHAR(30) PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    date_key INTEGER NOT NULL,
    feeder_id VARCHAR(20) NOT NULL,
    substation_id VARCHAR(20) NOT NULL,
    transformer_id VARCHAR(20) NOT NULL,
    load_type_id VARCHAR(30) NOT NULL,
    voltage_r NUMERIC(8,2) NOT NULL,
    voltage_y NUMERIC(8,2) NOT NULL,
    voltage_b NUMERIC(8,2) NOT NULL,
    voltage_avg NUMERIC(8,2) NOT NULL,
    voltage_deviation_pct NUMERIC(5,2) NOT NULL,
    current_r NUMERIC(7,2) NOT NULL,
    current_y NUMERIC(7,2) NOT NULL,
    current_b NUMERIC(7,2) NOT NULL,
    current_avg NUMERIC(7,2) NOT NULL,
    current_imbalance_pct NUMERIC(5,2) NOT NULL,
    active_power_kw NUMERIC(9,2) NOT NULL,
    reactive_power_kvar NUMERIC(9,2) NOT NULL,
    apparent_power_kva NUMERIC(9,2) NOT NULL,
    power_factor NUMERIC(4,3) NOT NULL,
    pf_category VARCHAR(30) NOT NULL,
    frequency_hz NUMERIC(4,2) NOT NULL,
    feeder_loss_kw NUMERIC(8,2) NOT NULL,
    feeder_loss_pct NUMERIC(5,2) NOT NULL,
    energy_kwh NUMERIC(9,2) NOT NULL,
    ambient_temperature_c NUMERIC(4,1) NOT NULL,
    equipment_temperature_c NUMERIC(4,1) NOT NULL,
    fault_status INTEGER NOT NULL,
    fault_type_id VARCHAR(30) NOT NULL,
    maintenance_flag INTEGER NOT NULL,
    transformer_loading_pct NUMERIC(5,2) NOT NULL,
    voltage_quality_band VARCHAR(40),
    current_imbalance_severity VARCHAR(40),
    thermal_rise_c NUMERIC(5,1),
    pf_penalty_incurred INTEGER,
    rolling_current_avg_24h NUMERIC(7,2),
    rolling_current_std_24h NUMERIC(7,2),
    rolling_pf_avg_24h NUMERIC(4,3),
    rolling_loss_pct_24h NUMERIC(5,2),
    stat_anomaly_flag INTEGER,
    stat_anomaly_reason TEXT,
    ml_anomaly_flag INTEGER,
    ml_anomaly_score NUMERIC(6,3),
    anomaly_consensus VARCHAR(60),
    is_any_anomaly INTEGER,
    anomaly_type_engineering VARCHAR(60),
    FOREIGN KEY (feeder_id) REFERENCES dim_feeder(feeder_id),
    FOREIGN KEY (transformer_id) REFERENCES dim_transformer(transformer_id),
    FOREIGN KEY (substation_id) REFERENCES dim_substation(substation_id),
    FOREIGN KEY (date_key) REFERENCES dim_calendar(date_key)
);

CREATE TABLE IF NOT EXISTS fact_fault_events (
    event_id VARCHAR(30) PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    date_key INTEGER NOT NULL,
    feeder_id VARCHAR(20) NOT NULL,
    transformer_id VARCHAR(20) NOT NULL,
    substation_id VARCHAR(20) NOT NULL,
    fault_type_id VARCHAR(30) NOT NULL,
    severity_score NUMERIC(5,2) NOT NULL,
    duration_minutes INTEGER NOT NULL,
    peak_current_a NUMERIC(7,2) NOT NULL,
    voltage_sag_pct NUMERIC(5,2) NOT NULL,
    affected_phase VARCHAR(30) NOT NULL,
    root_cause_category VARCHAR(80) NOT NULL,
    maintenance_required INTEGER NOT NULL,
    resolved_timestamp TIMESTAMP,
    resolution_notes TEXT,
    FOREIGN KEY (feeder_id) REFERENCES dim_feeder(feeder_id),
    FOREIGN KEY (transformer_id) REFERENCES dim_transformer(transformer_id),
    FOREIGN KEY (fault_type_id) REFERENCES dim_fault(fault_type_id),
    FOREIGN KEY (date_key) REFERENCES dim_calendar(date_key)
);

CREATE TABLE IF NOT EXISTS fact_maintenance (
    maintenance_id VARCHAR(30) PRIMARY KEY,
    maintenance_date DATE NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    feeder_id VARCHAR(30) NOT NULL,
    transformer_id VARCHAR(20) NOT NULL,
    maintenance_type VARCHAR(50) NOT NULL,
    priority VARCHAR(20) NOT NULL,
    cost_usd NUMERIC(8,2) NOT NULL,
    downtime_hours NUMERIC(5,1) NOT NULL,
    work_order_no VARCHAR(40) NOT NULL,
    description TEXT,
    technician_lead VARCHAR(80) NOT NULL,
    FOREIGN KEY (transformer_id) REFERENCES dim_transformer(transformer_id)
);

-- 3. PERFORMANCE INDEXES

CREATE INDEX IF NOT EXISTS idx_meas_feeder_ts ON fact_electrical_measurements (feeder_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_meas_tr_ts ON fact_electrical_measurements (transformer_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_meas_anomaly ON fact_electrical_measurements (is_any_anomaly);
CREATE INDEX IF NOT EXISTS idx_meas_loss ON fact_electrical_measurements (feeder_loss_pct);
CREATE INDEX IF NOT EXISTS idx_fault_feeder_ts ON fact_fault_events (feeder_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_maint_tr ON fact_maintenance (transformer_id);
