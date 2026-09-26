# Data Dictionary: Power Distribution Loss & Fault Analytics System

This data dictionary provides comprehensive metadata for all relational dimension and fact tables in the analytics system.

---

## 1. Dimension Tables

### 1.1 `dim_substation`
Contains physical and operational metadata for distribution substations.

| Column Name | Data Type | Key Type | Description | Valid Range / Example |
| :--- | :--- | :--- | :--- | :--- |
| `substation_id` | VARCHAR(20) | PK | Unique identifier for substation | `SUB_NORTH`, `SUB_SOUTH` |
| `substation_name` | VARCHAR(100) | | Full official designation | e.g. North Metro 33/11 kV Distribution Substation |
| `region` | VARCHAR(100) | | Geographic or grid zone | e.g. Industrial Corridor - North |
| `incoming_voltage_kv` | NUMERIC(5,2) | | Primary sub-transmission grid voltage | `33.00` kV |
| `bus_configuration` | VARCHAR(100) | | Busbar architecture | e.g. Double Bus with Bus Coupler |
| `total_capacity_mva` | NUMERIC(5,2) | | Total installed transformer MVA | `20.00` - `30.00` MVA |
| `commissioned_year` | INTEGER | | Year of energization | `2015` - `2018` |
| `latitude` | NUMERIC(9,6) | | Substation GIS latitude | `28.500000` to `28.800000` |
| `longitude` | NUMERIC(9,6) | | Substation GIS longitude | `77.100000` to `77.300000` |

---

### 1.2 `dim_transformer`
Contains nameplate and impedance specifications for step-down power transformers.

| Column Name | Data Type | Key Type | Description | Valid Range / Example |
| :--- | :--- | :--- | :--- | :--- |
| `transformer_id` | VARCHAR(20) | PK | Unique transformer identifier | `TR_01` to `TR_05` |
| `substation_id` | VARCHAR(20) | FK | Parent substation | References `dim_substation` |
| `transformer_name` | VARCHAR(100) | | Descriptive transformer designation | e.g. TR-1 (North Area Primary) |
| `rated_mva` | NUMERIC(5,2) | | Rated apparent power capacity | `5.00` to `12.50` MVA |
| `primary_voltage_kv` | NUMERIC(5,2) | | High voltage (HV) side nominal | `33.00` kV |
| `secondary_voltage_kv`| NUMERIC(5,2) | | Low voltage (LV) side nominal | `11.00` kV |
| `vector_group` | VARCHAR(20) | | Vector group and phase displacement | `Dyn11` |
| `impedance_pct` | NUMERIC(4,2) | | Percentage short-circuit impedance (%Z)| `5.75` to `7.00` % |
| `no_load_loss_kw` | NUMERIC(6,2) | | Continuous iron/core loss ($P_0$) | `5.00` to `11.20` kW |
| `full_load_loss_kw` | NUMERIC(6,2) | | Full-load copper loss ($P_k$) | `36.00` to `78.00` kW |
| `cooling_type` | VARCHAR(20) | | Cooling mechanism | `ONAN` (Natural), `ONAF` (Forced Air)|
| `rated_secondary_current_a` | NUMERIC(7,2) | | Rated secondary full load current | `262.40` to `656.10` A |

---

### 1.3 `dim_feeder`
Contains physical line parameters, conductor specifications, and load categorizations.

| Column Name | Data Type | Key Type | Description | Valid Range / Example |
| :--- | :--- | :--- | :--- | :--- |
| `feeder_id` | VARCHAR(20) | PK | Unique feeder identifier | `FDR_01` to `FDR_12` |
| `feeder_code` | VARCHAR(20) | | Standard engineering feeder code | e.g. `F-IND-01`, `F-AGR-12` |
| `transformer_id` | VARCHAR(20) | FK | Source step-down transformer | References `dim_transformer` |
| `substation_id` | VARCHAR(20) | FK | Source distribution substation | References `dim_substation` |
| `feeder_name` | VARCHAR(120) | | Feeder operational title | e.g. Automotive Machining Feeder |
| `load_type_id` | VARCHAR(30) | FK | Connected load characterization | References `dim_load` |
| `load_category` | VARCHAR(60) | | Categorical load sector | e.g. Industrial Process, Residential |
| `length_km` | NUMERIC(5,2) | | Circuit line route length | `1.50` to `8.50` km |
| `conductor_type` | VARCHAR(60) | | Cable / overhead conductor type | ACSR Dog, ACSR Weasel, XLPE Cable |
| `resistance_ohm_per_km` | NUMERIC(6,4) | | Conductor resistance per km | `0.0625` to `0.9100` $\Omega$/km |
| `reactance_ohm_per_km` | NUMERIC(6,4) | | Conductor inductive reactance per km | `0.0525` to `0.3550` $\Omega$/km |
| `total_resistance_ohm` | NUMERIC(6,4) | | Total circuit loop resistance | `0.1312` to `7.7350` $\Omega$ |
| `rated_current_a` | NUMERIC(7,2) | | Maximum continuous ampacity | `120.00` to `480.00` A |
| `nominal_voltage_v` | NUMERIC(7,2) | | Nominal circuit voltage | `11000.00` V |
| `baseline_current_a` | NUMERIC(7,2) | | Typical average operating current | `72.00` to `340.00` A |
| `base_pf` | NUMERIC(4,3) | | Design / typical operating power factor| `0.760` to `0.950` |
| `phase_imbalance_base`| NUMERIC(4,2) | | Baseline nominal unbalance % | `2.10` to `9.50` % |

---

### 1.4 `dim_load`
Characterizes industrial and municipal load types, harmonic distortions, and power factor envelopes.

| Column Name | Data Type | Key Type | Description | Valid Range / Example |
| :--- | :--- | :--- | :--- | :--- |
| `load_type_id` | VARCHAR(30) | PK | Load profile identifier | `LOAD_IND_PROC`, `LOAD_RES`, etc. |
| `load_category` | VARCHAR(60) | | Sector description | Industrial Process, Commercial, etc. |
| `typical_pf_min` | NUMERIC(4,3) | | Lower bound of normal PF envelope | `0.720` to `0.910` |
| `typical_pf_max` | NUMERIC(4,3) | | Upper bound of normal PF envelope | `0.820` to `0.960` |
| `harmonic_profile` | VARCHAR(100) | | Dominant current harmonic distortion | e.g. THD-I 8-12% (VFDs, Thyristors) |
| `sensitivity_level` | VARCHAR(30) | | Sag sensitivity classification | Low, Medium, High, Very High |
| `description` | TEXT | | Operational load details | Detailed narrative |

---

### 1.5 `dim_fault`
Standard IEEE and utility protection relay trip designations.

| Column Name | Data Type | Key Type | Description | Valid Range / Example |
| :--- | :--- | :--- | :--- | :--- |
| `fault_type_id` | VARCHAR(30) | PK | Fault classification code | `FLT_OVERCURRENT`, `FLT_UNDERVOLT` |
| `fault_name` | VARCHAR(100) | | Descriptive fault title | Feeder Overcurrent, Voltage Sag |
| `category` | VARCHAR(50) | | Disturbance classification | Thermal/Load, Power Quality, etc. |
| `default_severity`| VARCHAR(20) | | Standard engineering severity | Medium, High, Critical |
| `standard_action` | TEXT | | Standard operating procedure | Breaker reset, line patrol, etc. |
| `ieee_code` | VARCHAR(20) | | IEEE C37.2 protection device code | `50/51`, `27`, `59`, `46`, `49` |

---

### 1.6 `dim_calendar`
Time intelligence dimension table for date-based aggregations.

| Column Name | Data Type | Key Type | Description | Valid Range / Example |
| :--- | :--- | :--- | :--- | :--- |
| `date_key` | INTEGER | PK | Integer date key (YYYYMMDD) | `20260301` to `20260829` |
| `full_date` | DATE | | Standard date string | `2026-03-01` |
| `year` | INTEGER | | Calendar year | `2026` |
| `quarter` | VARCHAR(5) | | Calendar quarter | `Q1`, `Q2`, `Q3` |
| `month` | INTEGER | | Month number | `1` to `12` |
| `month_name` | VARCHAR(20) | | English month name | March, April, May, etc. |
| `day` | INTEGER | | Day of month | `1` to `31` |
| `day_of_week` | INTEGER | | Day of week (1=Mon, 7=Sun) | `1` to `7` |
| `day_name` | VARCHAR(15) | | English day name | Monday, Tuesday, etc. |
| `is_weekend` | INTEGER | | Weekend binary flag | `0` = Weekday, `1` = Weekend |
| `season` | VARCHAR(40) | | Meteorological season | Pre-Monsoon / Summer, Monsoon |

---

## 2. Fact Tables

### 2.1 `fact_electrical_measurements`
Central telemetry fact table containing 104,000+ verified 30-minute SCADA measurements.

| Column Name | Data Type | Key Type | Description | Units / Range |
| :--- | :--- | :--- | :--- | :--- |
| `measurement_id` | VARCHAR(30) | PK | Unique record identifier | `MEAS_0000001`+ |
| `timestamp` | TIMESTAMP | | Exact SCADA polling timestamp | 30-minute intervals |
| `date_key` | INTEGER | FK | Calendar link | References `dim_calendar` |
| `feeder_id` | VARCHAR(20) | FK | Monitored feeder link | References `dim_feeder` |
| `substation_id` | VARCHAR(20) | FK | Source substation | References `dim_substation` |
| `transformer_id` | VARCHAR(20) | FK | Source transformer | References `dim_transformer` |
| `load_type_id` | VARCHAR(30) | FK | Feeder load type | References `dim_load` |
| `voltage_r` | NUMERIC(8,2) | | Phase R Line-to-Line Voltage | Volts (V) [9,000 - 12,500] |
| `voltage_y` | NUMERIC(8,2) | | Phase Y Line-to-Line Voltage | Volts (V) [9,000 - 12,500] |
| `voltage_b` | NUMERIC(8,2) | | Phase B Line-to-Line Voltage | Volts (V) [9,000 - 12,500] |
| `voltage_avg` | NUMERIC(8,2) | | 3-Phase Average Voltage | Volts (V) |
| `voltage_deviation_pct`| NUMERIC(5,2) | | Deviation from 11,000 V nominal | Percentage (%) [-15% to +10%] |
| `current_r` | NUMERIC(7,2) | | Phase R Current | Amperes (A) [10 - 600] |
| `current_y` | NUMERIC(7,2) | | Phase Y Current | Amperes (A) [10 - 600] |
| `current_b` | NUMERIC(7,2) | | Phase B Current | Amperes (A) [10 - 600] |
| `current_avg` | NUMERIC(7,2) | | 3-Phase Average Current | Amperes (A) |
| `current_imbalance_pct`| NUMERIC(5,2) | | IEEE 141 current imbalance | Percentage (%) [0% to 25%] |
| `active_power_kw` | NUMERIC(9,2) | | Real Power ($P = S \times PF$) | Kilowatts (kW) |
| `reactive_power_kvar` | NUMERIC(9,2) | | Reactive Power ($Q = \sqrt{S^2-P^2}$) | kVAR |
| `apparent_power_kva` | NUMERIC(9,2) | | Apparent Power ($S = \sqrt{3}VI$) | kVA |
| `power_factor` | NUMERIC(4,3) | | Power factor ($\cos\phi$) | [0.65 to 0.99] |
| `pf_category` | VARCHAR(30) | | Categorical PF compliance tier | Excellent, Acceptable, Poor, Critical |
| `frequency_hz` | NUMERIC(4,2) | | Grid system frequency | Hertz (Hz) [49.70 - 50.30] |
| `feeder_loss_kw` | NUMERIC(8,2) | | Estimated Conductor Loss ($I^2R$) | Kilowatts (kW) |
| `feeder_loss_pct` | NUMERIC(5,2) | | Technical Loss Percentage | Percentage (%) [0.5% to 15.0%] |
| `energy_kwh` | NUMERIC(9,2) | | Delivered Energy ($P \times 0.5$) | Kilowatt-hours (kWh) |
| `ambient_temperature_c` | NUMERIC(4,1) | | Outdoor ambient temperature | Degrees Celsius (°C) [20 - 45] |
| `equipment_temperature_c`| NUMERIC(4,1) | | Conductor/terminal temperature | Degrees Celsius (°C) [25 - 95] |
| `fault_status` | INTEGER | | Binary flag for active fault | `0` = Normal, `1` = Active Fault |
| `fault_type_id` | VARCHAR(30) | FK | Type of active fault | References `dim_fault` |
| `transformer_loading_pct`| NUMERIC(5,2) | | Connected transformer stress | Percentage (%) [20% to 125%] |
| `stat_anomaly_flag` | INTEGER | | Flagged by Z-score / IQR | `0` = Inlier, `1` = Anomaly |
| `stat_anomaly_reason` | TEXT | | Explanatory reason string | e.g. Current Spike, Voltage Sag |
| `ml_anomaly_flag` | INTEGER | | Flagged by Isolation Forest | `0` = Inlier, `1` = Anomaly |
| `ml_anomaly_score` | NUMERIC(6,3) | | Continuous anomaly score | [-0.3 to 0.8] |
| `anomaly_consensus` | VARCHAR(60) | | Dual-Method consensus status | Dual-Confirmed, Stat Only, ML Only |

---

### 2.2 `fact_fault_events`
Historical log of protection relay breaker trips and transient disturbances.

| Column Name | Data Type | Key Type | Description | Units / Range |
| :--- | :--- | :--- | :--- | :--- |
| `event_id` | VARCHAR(30) | PK | Unique event identifier | `EVT_1001`+ |
| `timestamp` | TIMESTAMP | | Disturbance inception time | Datetime |
| `date_key` | INTEGER | FK | Calendar link | References `dim_calendar` |
| `feeder_id` | VARCHAR(20) | FK | Tripped feeder link | References `dim_feeder` |
| `transformer_id` | VARCHAR(20) | FK | Source transformer | References `dim_transformer` |
| `substation_id` | VARCHAR(20) | FK | Source substation | References `dim_substation` |
| `fault_type_id` | VARCHAR(30) | FK | Disturbance classification | References `dim_fault` |
| `severity_score` | NUMERIC(5,2) | | Rule-based severity index | Score [0 - 100] |
| `duration_minutes` | INTEGER | | Outage duration until restore | Minutes [30 - 240] |
| `peak_current_a` | NUMERIC(7,2) | | Maximum fault surge current | Amperes (A) |
| `voltage_sag_pct` | NUMERIC(5,2) | | Transient voltage drop depth | Percentage (%) |
| `affected_phase` | VARCHAR(30) | | Impacted electrical phase | R-Phase, Y-Phase, B-Phase, 3-Phase |
| `root_cause_category`| VARCHAR(80) | | Field investigation finding | e.g. Tree Contact, Motor Inrush |
| `maintenance_required`| INTEGER | | Corrective work order needed | `1` = Yes, `0` = No |
| `resolved_timestamp` | TIMESTAMP | | Time breaker reclosed | Datetime |
| `resolution_notes` | TEXT | | Field technician sign-off | Narrative |

---

### 2.3 `fact_maintenance`
Maintenance work orders, equipment overhaul logs, and operating expenditures.

| Column Name | Data Type | Key Type | Description | Units / Range |
| :--- | :--- | :--- | :--- | :--- |
| `maintenance_id` | VARCHAR(30) | PK | Work order identifier | `MNT_5001`+ |
| `maintenance_date` | DATE | | Execution date | YYYY-MM-DD |
| `timestamp` | TIMESTAMP | | Dispatch timestamp | Datetime |
| `feeder_id` | VARCHAR(30) | | Serviced feeder (or SUBSTATION) | Feeder ID |
| `transformer_id` | VARCHAR(20) | FK | Serviced transformer | References `dim_transformer` |
| `maintenance_type` | VARCHAR(50) | | PM vs Corrective | Corrective / Emergency, Preventive |
| `priority` | VARCHAR(20) | | Work order priority | Routine, Medium, High |
| `cost_usd` | NUMERIC(8,2) | | Remediation cost | USD ($250 - $3,500) |
| `downtime_hours` | NUMERIC(5,1) | | Outage duration for work | Hours (1.0 - 6.0) |
| `work_order_no` | VARCHAR(40) | | ERP / EAM Work Order Code | e.g. `WO-202604-5004` |
| `description` | TEXT | | Scope of work executed | Narrative |
| `technician_lead` | VARCHAR(80) | | Lead protection engineer | Name & Title |
