"""
Configuration and Electrical Engineering Constants
Power Distribution Loss & Fault Analytics System
"""

import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
DATABASE_DIR = BASE_DIR / "database"
DB_PATH = DATABASE_DIR / "power_distribution.db"

# Electrical System Global Constants
NOMINAL_VOLTAGE_LL = 11000.0  # 11 kV Line-to-Line (Volts)
NOMINAL_VOLTAGE_LN = NOMINAL_VOLTAGE_LL / (3 ** 0.5)  # ~6350.85 Volts Line-to-Neutral
GRID_FREQUENCY_HZ = 50.0      # 50 Hz standard (Indian/European distribution grid)
INTERVAL_MINUTES = 30         # 30-minute SCADA / AMI recording intervals
INTERVAL_HOURS = INTERVAL_MINUTES / 60.0  # 0.5 Hours

# Grid Standard Tolerances (per IEEE Std 1159 / CEA / IEC 60038)
VOLTAGE_NORMAL_BAND_PCT = 5.0     # +/- 5% nominal
VOLTAGE_UNDERVOLTAGE_PCT = -5.0   # < -5%
VOLTAGE_OVERVOLTAGE_PCT = 5.0     # > +5%
VOLTAGE_CRITICAL_LOW_PCT = -10.0  # < -10%

# Power Factor Thresholds (Regulatory & Efficiency Tariffs)
PF_EXCELLENT = 0.95
PF_ACCEPTABLE = 0.90
PF_POOR = 0.80
# PF < 0.80 is deemed CRITICAL (incurs maximum commercial penalty and high conductor heating)

# Current Imbalance Thresholds (IEEE Std 141 / NEMA MG 1)
CURRENT_IMBALANCE_NORMAL_PCT = 5.0    # <= 5% acceptable
CURRENT_IMBALANCE_WARNING_PCT = 10.0  # 5-10% warning
# > 10% is CRITICAL (induces severe neutral current, negative sequence heating in transformers/motors)

# Transformer Loading Thresholds
TR_LOADING_NORMAL_PCT = 70.0
TR_LOADING_HIGH_PCT = 85.0
TR_LOADING_OVERLOAD_PCT = 100.0

# Substation Metadata
SUBSTATIONS = [
    {
        "substation_id": "SUB_NORTH",
        "substation_name": "North Metro 33/11 kV Distribution Substation",
        "region": "Industrial Corridor - North",
        "incoming_voltage_kv": 33.0,
        "bus_configuration": "Double Bus with Bus Coupler",
        "total_capacity_mva": 20.0,
        "commissioned_year": 2018,
        "latitude": 28.7041,
        "longitude": 77.1025
    },
    {
        "substation_id": "SUB_SOUTH",
        "substation_name": "South Heavy Process 33/11 kV Distribution Substation",
        "region": "Industrial & Harbor Zone - South",
        "incoming_voltage_kv": 33.0,
        "bus_configuration": "Main and Transfer Bus",
        "total_capacity_mva": 30.0,
        "commissioned_year": 2015,
        "latitude": 28.5355,
        "longitude": 77.2410
    }
]

# Transformers Metadata
TRANSFORMERS = [
    {
        "transformer_id": "TR_01",
        "substation_id": "SUB_NORTH",
        "transformer_name": "TR-1 (North Area Primary)",
        "rated_mva": 10.0,
        "primary_voltage_kv": 33.0,
        "secondary_voltage_kv": 11.0,
        "vector_group": "Dyn11",
        "impedance_pct": 6.50,
        "no_load_loss_kw": 8.5,
        "full_load_loss_kw": 62.0,
        "cooling_type": "ONAN",
        "rated_secondary_current_a": 524.9
    },
    {
        "transformer_id": "TR_02",
        "substation_id": "SUB_NORTH",
        "transformer_name": "TR-2 (North Area Commercial/Urban)",
        "rated_mva": 10.0,
        "primary_voltage_kv": 33.0,
        "secondary_voltage_kv": 11.0,
        "vector_group": "Dyn11",
        "impedance_pct": 6.50,
        "no_load_loss_kw": 8.5,
        "full_load_loss_kw": 62.0,
        "cooling_type": "ONAN",
        "rated_secondary_current_a": 524.9
    },
    {
        "transformer_id": "TR_03",
        "substation_id": "SUB_SOUTH",
        "transformer_name": "TR-3 (South Heavy Industrial)",
        "rated_mva": 12.5,
        "primary_voltage_kv": 33.0,
        "secondary_voltage_kv": 11.0,
        "vector_group": "Dyn11",
        "impedance_pct": 7.00,
        "no_load_loss_kw": 11.2,
        "full_load_loss_kw": 78.0,
        "cooling_type": "ONAF",
        "rated_secondary_current_a": 656.1
    },
    {
        "transformer_id": "TR_04",
        "substation_id": "SUB_SOUTH",
        "transformer_name": "TR-4 (South Continuous Process)",
        "rated_mva": 12.5,
        "primary_voltage_kv": 33.0,
        "secondary_voltage_kv": 11.0,
        "vector_group": "Dyn11",
        "impedance_pct": 7.00,
        "no_load_loss_kw": 11.2,
        "full_load_loss_kw": 78.0,
        "cooling_type": "ONAF",
        "rated_secondary_current_a": 656.1
    },
    {
        "transformer_id": "TR_05",
        "substation_id": "SUB_SOUTH",
        "transformer_name": "TR-5 (South Auxiliary & Rural)",
        "rated_mva": 5.0,
        "primary_voltage_kv": 33.0,
        "secondary_voltage_kv": 11.0,
        "vector_group": "Dyn11",
        "impedance_pct": 5.75,
        "no_load_loss_kw": 5.0,
        "full_load_loss_kw": 36.0,
        "cooling_type": "ONAN",
        "rated_secondary_current_a": 262.4
    }
]

# Feeders Metadata with Real Electrical Conductor Properties
# R per km and X per km derived from standard ACSR/XLPE electrical cable schedules
FEEDERS = [
    {
        "feeder_id": "FDR_01",
        "feeder_code": "F-IND-01",
        "transformer_id": "TR_01",
        "substation_id": "SUB_NORTH",
        "feeder_name": "Automotive Assembly & Machining Feeder",
        "load_type_id": "LOAD_IND_PROC",
        "load_category": "Industrial Process",
        "length_km": 3.2,
        "conductor_type": "ACSR Dog (100 mm²)",
        "resistance_ohm_per_km": 0.2792,
        "reactance_ohm_per_km": 0.3150,
        "total_resistance_ohm": 0.8934,
        "rated_current_a": 250.0,
        "nominal_voltage_v": 11000.0,
        "baseline_current_a": 150.0,
        "base_pf": 0.86,
        "phase_imbalance_base": 3.2
    },
    {
        "feeder_id": "FDR_02",
        "feeder_code": "F-MOT-02",
        "transformer_id": "TR_01",
        "substation_id": "SUB_NORTH",
        "feeder_name": "Heavy Pumping Station & Induction Drives",
        "load_type_id": "LOAD_IND_MOT",
        "load_category": "Induction Motors",
        "length_km": 2.5,
        "conductor_type": "XLPE 185 mm² Underground Cable",
        "resistance_ohm_per_km": 0.1600,
        "reactance_ohm_per_km": 0.1100,
        "total_resistance_ohm": 0.4000,
        "rated_current_a": 300.0,
        "nominal_voltage_v": 11000.0,
        "baseline_current_a": 195.0,
        "base_pf": 0.76,  # Typical motor low lagging PF!
        "phase_imbalance_base": 2.8
    },
    {
        "feeder_id": "FDR_03",
        "feeder_code": "F-RES-03",
        "transformer_id": "TR_01",
        "substation_id": "SUB_NORTH",
        "feeder_name": "Residential Staff Township Feeder",
        "load_type_id": "LOAD_RES",
        "load_category": "Residential",
        "length_km": 4.0,
        "conductor_type": "ACSR Rabbit (50 mm²)",
        "resistance_ohm_per_km": 0.5449,
        "reactance_ohm_per_km": 0.3350,
        "total_resistance_ohm": 2.1796,
        "rated_current_a": 150.0,
        "nominal_voltage_v": 11000.0,
        "baseline_current_a": 85.0,
        "base_pf": 0.94,  # High domestic PF
        "phase_imbalance_base": 6.8  # Unbalanced single-phase loads cause higher current imbalance!
    },
    {
        "feeder_id": "FDR_04",
        "feeder_code": "F-COM-04",
        "transformer_id": "TR_02",
        "substation_id": "SUB_NORTH",
        "feeder_name": "IT Tech Park & Commercial Complex Feeder",
        "load_type_id": "LOAD_COMM",
        "load_category": "Commercial & IT",
        "length_km": 1.8,
        "conductor_type": "XLPE 240 mm² Cable",
        "resistance_ohm_per_km": 0.1250,
        "reactance_ohm_per_km": 0.1050,
        "total_resistance_ohm": 0.2250,
        "rated_current_a": 350.0,
        "nominal_voltage_v": 11000.0,
        "baseline_current_a": 220.0,
        "base_pf": 0.90,
        "phase_imbalance_base": 4.1
    },
    {
        "feeder_id": "FDR_05",
        "feeder_code": "F-MUN-05",
        "transformer_id": "TR_02",
        "substation_id": "SUB_NORTH",
        "feeder_name": "Water Treatment & Expressway Lighting Feeder",
        "load_type_id": "LOAD_LIGHT",
        "load_category": "Lighting & Municipal",
        "length_km": 5.2,
        "conductor_type": "ACSR Dog (100 mm²)",
        "resistance_ohm_per_km": 0.2792,
        "reactance_ohm_per_km": 0.3150,
        "total_resistance_ohm": 1.4518,
        "rated_current_a": 200.0,
        "nominal_voltage_v": 11000.0,
        "baseline_current_a": 105.0,
        "base_pf": 0.88,
        "phase_imbalance_base": 5.5
    },
    {
        "feeder_id": "FDR_06",
        "feeder_code": "F-SUB-06",
        "transformer_id": "TR_02",
        "substation_id": "SUB_NORTH",
        "feeder_name": "Suburban Periphery Mixed Feeder",
        "load_type_id": "LOAD_RES",
        "load_category": "Residential Mixed",
        "length_km": 6.8,
        "conductor_type": "ACSR Rabbit (50 mm²)",
        "resistance_ohm_per_km": 0.5449,
        "reactance_ohm_per_km": 0.3350,
        "total_resistance_ohm": 3.7053,
        "rated_current_a": 140.0,
        "nominal_voltage_v": 11000.0,
        "baseline_current_a": 78.0,
        "base_pf": 0.91,
        "phase_imbalance_base": 7.2  # High line impedance + single phase unbalance
    },
    {
        "feeder_id": "FDR_07",
        "feeder_code": "F-MET-07",
        "transformer_id": "TR_03",
        "substation_id": "SUB_SOUTH",
        "feeder_name": "Steel Rolling Mill & Arc Furnace Feeder",
        "load_type_id": "LOAD_IND_PROC",
        "load_category": "Heavy Industrial",
        "length_km": 2.2,
        "conductor_type": "Copper 300 mm² Busway / Cable",
        "resistance_ohm_per_km": 0.0818,
        "reactance_ohm_per_km": 0.0950,
        "total_resistance_ohm": 0.1800,
        "rated_current_a": 480.0,
        "nominal_voltage_v": 11000.0,
        "baseline_current_a": 340.0,
        "base_pf": 0.81,
        "phase_imbalance_base": 9.5  # Arc furnace single-phase taps create chronic imbalance!
    },
    {
        "feeder_id": "FDR_08",
        "feeder_code": "F-CHM-08",
        "transformer_id": "TR_03",
        "substation_id": "SUB_SOUTH",
        "feeder_name": "Petrochemical Continuous Plant Feeder",
        "load_type_id": "LOAD_IND_PROC",
        "load_category": "Continuous Chemical",
        "length_km": 3.0,
        "conductor_type": "XLPE 185 mm² Cable",
        "resistance_ohm_per_km": 0.1600,
        "reactance_ohm_per_km": 0.1100,
        "total_resistance_ohm": 0.4800,
        "rated_current_a": 320.0,
        "nominal_voltage_v": 11000.0,
        "baseline_current_a": 260.0,  # High continuous base load (>80% loading)
        "base_pf": 0.87,
        "phase_imbalance_base": 2.4
    },
    {
        "feeder_id": "FDR_09",
        "feeder_code": "F-REF-09",
        "transformer_id": "TR_04",
        "substation_id": "SUB_SOUTH",
        "feeder_name": "Harbor Cold Storage & Cryogenics Feeder",
        "load_type_id": "LOAD_IND_MOT",
        "load_category": "Refrigeration & Compressors",
        "length_km": 3.6,
        "conductor_type": "ACSR Dog (100 mm²)",
        "resistance_ohm_per_km": 0.2792,
        "reactance_ohm_per_km": 0.3150,
        "total_resistance_ohm": 1.0051,
        "rated_current_a": 240.0,
        "nominal_voltage_v": 11000.0,
        "baseline_current_a": 165.0,
        "base_pf": 0.77,  # Compressor motor lagging PF
        "phase_imbalance_base": 3.5
    },
    {
        "feeder_id": "FDR_10",
        "feeder_code": "F-AUX-10",
        "transformer_id": "TR_04",
        "substation_id": "SUB_SOUTH",
        "feeder_name": "Industrial Park Utility & Cooling Tower Feeder",
        "load_type_id": "LOAD_AUX",
        "load_category": "Auxiliary Utilities",
        "length_km": 1.6,
        "conductor_type": "XLPE 150 mm² Cable",
        "resistance_ohm_per_km": 0.2060,
        "reactance_ohm_per_km": 0.1150,
        "total_resistance_ohm": 0.3296,
        "rated_current_a": 220.0,
        "nominal_voltage_v": 11000.0,
        "baseline_current_a": 130.0,
        "base_pf": 0.85,
        "phase_imbalance_base": 3.0
    },
    {
        "feeder_id": "FDR_11",
        "feeder_code": "F-HSP-11",
        "transformer_id": "TR_04",
        "substation_id": "SUB_SOUTH",
        "feeder_name": "Metro Regional Hospital & Trauma Feeder",
        "load_type_id": "LOAD_COMM",
        "load_category": "Institutional Critical",
        "length_km": 2.1,
        "conductor_type": "Dual XLPE 240 mm² Cable",
        "resistance_ohm_per_km": 0.0625,  # Parallel run reduces line resistance
        "reactance_ohm_per_km": 0.0525,
        "total_resistance_ohm": 0.1312,
        "rated_current_a": 280.0,
        "nominal_voltage_v": 11000.0,
        "baseline_current_a": 170.0,
        "base_pf": 0.95,  # Automatic Power Factor Correction (APFC) bank installed!
        "phase_imbalance_base": 2.1
    },
    {
        "feeder_id": "FDR_12",
        "feeder_code": "F-AGR-12",
        "transformer_id": "TR_05",
        "substation_id": "SUB_SOUTH",
        "feeder_name": "Rural Agricultural & Lift Irrigation Feeder",
        "load_type_id": "LOAD_AGRI",
        "load_category": "Agricultural Irrigation",
        "length_km": 8.5,  # Long overhead radial line
        "conductor_type": "ACSR Weasel (30 mm²)",
        "resistance_ohm_per_km": 0.9100,
        "reactance_ohm_per_km": 0.3550,
        "total_resistance_ohm": 7.7350,  # Highest resistance feeder in grid!
        "rated_current_a": 120.0,
        "nominal_voltage_v": 11000.0,
        "baseline_current_a": 72.0,
        "base_pf": 0.79,  # Uncompensated induction irrigation pumps
        "phase_imbalance_base": 8.0  # High line impedance, seasonal pump surges
    }
]

# Load Type Master
LOAD_TYPES = [
    {
        "load_type_id": "LOAD_IND_PROC",
        "load_category": "Industrial Process",
        "typical_pf_min": 0.82,
        "typical_pf_max": 0.89,
        "harmonic_profile": "THD-I 8-12% (VFDs, Thyristors)",
        "sensitivity_level": "High",
        "description": "Continuous assembly lines, machining, and material handling systems"
    },
    {
        "load_type_id": "LOAD_IND_MOT",
        "load_category": "Induction Motors",
        "typical_pf_min": 0.72,
        "typical_pf_max": 0.82,
        "harmonic_profile": "THD-I 5-8% (Direct-on-line motors)",
        "sensitivity_level": "Medium",
        "description": "Large 3-phase induction motors, blowers, cooling pumps, and compressors"
    },
    {
        "load_type_id": "LOAD_RES",
        "load_category": "Residential",
        "typical_pf_min": 0.91,
        "typical_pf_max": 0.96,
        "harmonic_profile": "THD-I 12-18% (SMPS, LED lighting, Electronics)",
        "sensitivity_level": "Low",
        "description": "Township residential quarters, domestic appliances, air conditioners"
    },
    {
        "load_type_id": "LOAD_COMM",
        "load_category": "Commercial & Institutional",
        "typical_pf_min": 0.88,
        "typical_pf_max": 0.96,
        "harmonic_profile": "THD-I 10-15% (Data servers, HVAC chillers)",
        "sensitivity_level": "Very High",
        "description": "IT data center, hospital critical infrastructure, office buildings"
    },
    {
        "load_type_id": "LOAD_LIGHT",
        "load_category": "Lighting & Municipal",
        "typical_pf_min": 0.85,
        "typical_pf_max": 0.92,
        "harmonic_profile": "THD-I 15-22% (Discharge lamps, electronic drivers)",
        "sensitivity_level": "Low",
        "description": "High-mast highway illumination, street lighting, municipal aeration"
    },
    {
        "load_type_id": "LOAD_AUX",
        "load_category": "Auxiliary Utilities",
        "typical_pf_min": 0.83,
        "typical_pf_max": 0.89,
        "harmonic_profile": "THD-I 6-10%",
        "sensitivity_level": "Medium",
        "description": "Cooling towers, air compressors, auxiliary water pumps, substation station supply"
    },
    {
        "load_type_id": "LOAD_AGRI",
        "load_category": "Agricultural Irrigation",
        "typical_pf_min": 0.74,
        "typical_pf_max": 0.82,
        "harmonic_profile": "THD-I 6-9% (Borewell pumps)",
        "sensitivity_level": "Low",
        "description": "Rural tube-wells, lift irrigation pumps, grain processing mills"
    }
]

# Fault Types Master (Standard Distribution Faults)
FAULT_TYPES = [
    {
        "fault_type_id": "FLT_OVERCURRENT",
        "fault_name": "Feeder Overcurrent",
        "category": "Thermal/Load",
        "default_severity": "High",
        "standard_action": "Check line loading, trip breaker 50/51, inspect load redistribution",
        "ieee_code": "50/51"
    },
    {
        "fault_type_id": "FLT_UNDERVOLT",
        "fault_name": "Voltage Sag / Undervoltage",
        "category": "Power Quality",
        "default_severity": "Medium",
        "standard_action": "Inspect tap changer (OLTC), check reactive power deficit, capacitor bank status",
        "ieee_code": "27"
    },
    {
        "fault_type_id": "FLT_OVERVOLT",
        "fault_name": "Voltage Swell / Overvoltage",
        "category": "Power Quality",
        "default_severity": "Medium",
        "standard_action": "Inspect grid incoming voltage, switch off surplus capacitor banks, check OLTC step",
        "ieee_code": "59"
    },
    {
        "fault_type_id": "FLT_IMBALANCE",
        "fault_name": "Severe Phase Current Imbalance",
        "category": "Unbalance",
        "default_severity": "High",
        "standard_action": "Audit single-phase branch connections, rotate single-phase taps, rebalance phases",
        "ieee_code": "46"
    },
    {
        "fault_type_id": "FLT_TR_OVERLOAD",
        "fault_name": "Transformer Thermal Overload",
        "category": "Asset Health",
        "default_severity": "Critical",
        "standard_action": "Engage ONAF forced cooling, shed non-critical feeders, review MVA load duration curve",
        "ieee_code": "49"
    },
    {
        "fault_type_id": "FLT_EQUIP_OVERHEAT",
        "fault_name": "Equipment / Cable Termination Hotspot",
        "category": "Thermal",
        "default_severity": "High",
        "standard_action": "Perform thermography inspection, torque busbar bolted joints, inspect cable lugs",
        "ieee_code": "49T"
    },
    {
        "fault_type_id": "FLT_EARTH_LEAKAGE",
        "fault_name": "Transient Earth Fault / High Resistance Fault",
        "category": "Insulation",
        "default_severity": "Critical",
        "standard_action": "Line patrol for vegetation contact, test insulator surge arresters, megger cable insulation",
        "ieee_code": "50N/51N"
    }
]
