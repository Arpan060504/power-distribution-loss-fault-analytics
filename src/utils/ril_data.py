"""
Reliance Industries Limited (RIL) Substation 600-30 Field Telemetry Data & Analytical Engine
Real Industrial Telemetry Ingested from Refinery & Petrochemical Distribution Complex
Substation 600-30 (6.6 kV Medium Voltage Switchboard: Bus A & Bus B)
Satellite Substations 600-31 & 600-32 (415 V Low Voltage Motor Control Centers)
"""

import math
import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
RAW_DATA_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DATA_DIR = BASE_DIR / "data" / "processed"
DB_PATH = BASE_DIR / "database" / "power_distribution.db"

# Technical Conductor Resistances at 75°C (Ω/km) for Industrial XLPE Cables
R_PER_KM_150_XLPE = 0.2060  # 150 mm² Aluminum XLPE (or 0.160 for Cu)
R_PER_KM_240_XLPE = 0.1250  # 240 mm² Aluminum XLPE (or 0.098 for Cu)

# Raw Field Data from RIL Internship
RIL_RAW_FEEDERS = [
    # =========================================================================
    # SUBSTATION 600-30: BUS BAR B (6.6 kV Nominal)
    # =========================================================================
    {
        "substation": "Substation 600-30",
        "voltage_level_kv": 6.6,
        "bus_bar": "Bus B",
        "feeder_id": "FDR_600_30_B1",
        "feeder_tag": "Feeder B1",
        "description": "BUS PT FOR BUS B",
        "service": "Bus Potential Transformer / Metering",
        "length_m": 10.0,
        "cable_spec": "Control Cable",
        "area_sqmm": 150.0,
        "voltage_v": 6630.0,
        "ir_a": 40.0,
        "iy_a": 40.0,
        "ib_a": 40.0,
        "power_factor": 0.950,
        "status": "ACTIVE"
    },
    {
        "substation": "Substation 600-30",
        "voltage_level_kv": 6.6,
        "bus_bar": "Bus B",
        "feeder_id": "FDR_600_30_B2",
        "feeder_tag": "Feeder B2",
        "description": "2MVA TR 600-03B AT SUBSTATION 600-30",
        "service": "Step-down Transformer Auxiliary Feeder",
        "length_m": 48.0,
        "cable_spec": "XLPE",
        "area_sqmm": 150.0,
        "voltage_v": 6700.0,
        "ir_a": 50.0,
        "iy_a": 50.0,
        "ib_a": 50.0,
        "power_factor": 0.960,
        "status": "ACTIVE"
    },
    {
        "substation": "Substation 600-30",
        "voltage_level_kv": 6.6,
        "bus_bar": "Bus B",
        "feeder_id": "FDR_600_30_B3",
        "feeder_tag": "Feeder B3",
        "description": "INCOMER 16MVA FROM TR-600-01B",
        "service": "Main Grid Transformer 16 MVA Incomer",
        "length_m": 50.0,
        "cable_spec": "Bus Duct / Heavy XLPE",
        "area_sqmm": 400.0,
        "voltage_v": 6750.0,
        "ir_a": 190.0,
        "iy_a": 190.0,
        "ib_a": 185.0,
        "power_factor": 0.965,
        "status": "ACTIVE_INCOMER"
    },
    {
        "substation": "Substation 600-30",
        "voltage_level_kv": 6.6,
        "bus_bar": "Bus B",
        "feeder_id": "FDR_600_30_B4",
        "feeder_tag": "Feeder B4",
        "description": "TO 2MVA TR 600-05B AT SUBSTATION 600-31",
        "service": "Step-down TR Feeder to S/S 600-31 (LPG/Naphtha)",
        "length_m": 416.0,
        "cable_spec": "XLPE",
        "area_sqmm": 150.0,
        "voltage_v": 6620.0,
        "ir_a": 11.0,
        "iy_a": 11.0,
        "ib_a": 12.0,
        "power_factor": 0.940,
        "status": "ACTIVE"
    },
    {
        "substation": "Substation 600-30",
        "voltage_level_kv": 6.6,
        "bus_bar": "Bus B",
        "feeder_id": "FDR_600_30_B5",
        "feeder_tag": "Feeder B5",
        "description": "TO 2MVA TR 600-06B AT SUBSTATION 600-32",
        "service": "Step-down TR Feeder to S/S 600-32 (ATF/HSD)",
        "length_m": 450.0,
        "cable_spec": "XLPE",
        "area_sqmm": 150.0,
        "voltage_v": 6600.0,
        "ir_a": 5.0,
        "iy_a": 5.0,
        "ib_a": 5.0,
        "power_factor": 0.920,
        "status": "ACTIVE"
    },
    {
        "substation": "Substation 600-30",
        "voltage_level_kv": 6.6,
        "bus_bar": "Bus B",
        "feeder_id": "FDR_600_30_B6",
        "feeder_tag": "Feeder B6",
        "description": "TO 2MVA TR AT SUBSTATION 600-33 ET-RS 652-01B",
        "service": "Transformer Feeder S/S 600-33",
        "length_m": 600.0,
        "cable_spec": "3C XLPE",
        "area_sqmm": 150.0,
        "voltage_v": 6600.0,
        "ir_a": 20.0,
        "iy_a": 20.0,
        "ib_a": 20.0,
        "power_factor": 0.950,
        "status": "ACTIVE"
    },
    {
        "substation": "Substation 600-30",
        "voltage_level_kv": 6.6,
        "bus_bar": "Bus B",
        "feeder_id": "FDR_600_30_B7",
        "feeder_tag": "Feeder B7",
        "description": "SW BD 600-10B",
        "service": "Switchboard Distribution Feeder",
        "length_m": 800.0,
        "cable_spec": "4C XLPE",
        "area_sqmm": 240.0,
        "voltage_v": 6610.0,
        "ir_a": 42.0,
        "iy_a": 37.0,
        "ib_a": 37.0,
        "power_factor": 0.930,
        "status": "ACTIVE"
    },
    {
        "substation": "Substation 600-30",
        "voltage_level_kv": 6.6,
        "bus_bar": "Bus B",
        "feeder_id": "FDR_600_30_B8",
        "feeder_tag": "Feeder B8",
        "description": "6.6/0.433KV TRANSFORMER ET RS 600-09 AT S/S 600-35",
        "service": "Step-down Distribution Transformer",
        "length_m": 650.0,
        "cable_spec": "XLPE",
        "area_sqmm": 240.0,
        "voltage_v": 6620.0,
        "ir_a": 11.4,
        "iy_a": 9.8,
        "ib_a": 10.5,
        "power_factor": 0.940,
        "status": "ACTIVE"
    },
    {
        "substation": "Substation 600-30",
        "voltage_level_kv": 6.6,
        "bus_bar": "Bus B",
        "feeder_id": "FDR_600_30_B9",
        "feeder_tag": "Feeder B9",
        "description": "ES JIZ 300-02B AT SUBSTATION 600-38",
        "service": "Industrial Process Supply",
        "length_m": 800.0,
        "cable_spec": "4C XLPE",
        "area_sqmm": 150.0,
        "voltage_v": 6620.0,
        "ir_a": 3.0,
        "iy_a": 3.0,
        "ib_a": 3.0,
        "power_factor": 0.900,
        "status": "ACTIVE"
    },
    {
        "substation": "Substation 600-30",
        "voltage_level_kv": 6.6,
        "bus_bar": "Bus B",
        "feeder_id": "FDR_600_30_B10",
        "feeder_tag": "Feeder B10",
        "description": "MP RS65/M08 3B OX SHIP LOADING PUMP",
        "service": "Marine Terminal OX Ship Loading Pump Motor",
        "length_m": 500.0,
        "cable_spec": "XLPE",
        "area_sqmm": 150.0,
        "voltage_v": 6600.0,
        "ir_a": 0.0,
        "iy_a": 0.0,
        "ib_a": 0.0,
        "power_factor": 0.880,
        "status": "OFF_STANDBY"
    },
    {
        "substation": "Substation 600-30",
        "voltage_level_kv": 6.6,
        "bus_bar": "Bus B",
        "feeder_id": "FDR_600_30_B11",
        "feeder_tag": "Feeder B11",
        "description": "GAIL INCOMER -2 HT 201 BUS 2A",
        "service": "GAIL Gas Grid Redundant Incomer 2",
        "length_m": 520.0,
        "cable_spec": "XLPE",
        "area_sqmm": 150.0,
        "voltage_v": 6600.0,
        "ir_a": 0.0,
        "iy_a": 0.0,
        "ib_a": 0.0,
        "power_factor": 0.940,
        "status": "OFF_STANDBY"
    },
    {
        "substation": "Substation 600-30",
        "voltage_level_kv": 6.6,
        "bus_bar": "Bus B",
        "feeder_id": "FDR_600_30_B12",
        "feeder_tag": "Feeder B12",
        "description": "BACKUP FEEDER B12",
        "service": "Substation Switchboard Spare",
        "length_m": 0.0,
        "cable_spec": "None",
        "area_sqmm": 150.0,
        "voltage_v": 6600.0,
        "ir_a": 0.0,
        "iy_a": 0.0,
        "ib_a": 0.0,
        "power_factor": 1.000,
        "status": "OFF_SPARE"
    },
    {
        "substation": "Substation 600-30",
        "voltage_level_kv": 6.6,
        "bus_bar": "Bus B",
        "feeder_id": "FDR_600_30_B13",
        "feeder_tag": "Feeder B13",
        "description": "1800-SB-001B CEIL CAIRN INDIA I/C-2",
        "service": "Upstream Crude Transfer Incomer 2",
        "length_m": 900.0,
        "cable_spec": "XLPE",
        "area_sqmm": 150.0,
        "voltage_v": 6600.0,
        "ir_a": 9.6,
        "iy_a": 9.6,
        "ib_a": 9.6,
        "power_factor": 0.970,
        "status": "ACTIVE"
    },
    {
        "substation": "Substation 600-30",
        "voltage_level_kv": 6.6,
        "bus_bar": "Bus B",
        "feeder_id": "FDR_600_30_B14",
        "feeder_tag": "Feeder B14",
        "description": "MP RW621-M701B RTF VR/VGU MOTOR",
        "service": "Refinery Tank Farm Vapor Recovery Motor",
        "length_m": 800.0,
        "cable_spec": "XLPE",
        "area_sqmm": 150.0,
        "voltage_v": 6600.0,
        "ir_a": 24.1,
        "iy_a": 24.1,
        "ib_a": 24.1,
        "power_factor": 0.965,
        "status": "ACTIVE"
    },
    {
        "substation": "Substation 600-30",
        "voltage_level_kv": 6.6,
        "bus_bar": "Bus B",
        "feeder_id": "FDR_600_30_B15",
        "feeder_tag": "Feeder B15",
        "description": "MP RW621-M701D RTF VR/VGU MOTOR",
        "service": "Refinery Tank Farm Standby Motor D",
        "length_m": 800.0,
        "cable_spec": "XLPE",
        "area_sqmm": 150.0,
        "voltage_v": 6600.0,
        "ir_a": 0.0,
        "iy_a": 0.0,
        "ib_a": 0.0,
        "power_factor": 0.960,
        "status": "OFF_STANDBY"
    },
    {
        "substation": "Substation 600-30",
        "voltage_level_kv": 6.6,
        "bus_bar": "Bus B",
        "feeder_id": "FDR_600_30_B16",
        "feeder_tag": "Feeder B16",
        "description": "BACKUP FEEDER B16",
        "service": "Substation Switchboard Spare",
        "length_m": 0.0,
        "cable_spec": "None",
        "area_sqmm": 150.0,
        "voltage_v": 6600.0,
        "ir_a": 0.0,
        "iy_a": 0.0,
        "ib_a": 0.0,
        "power_factor": 1.000,
        "status": "OFF_SPARE"
    },
    {
        "substation": "Substation 600-30",
        "voltage_level_kv": 6.6,
        "bus_bar": "Bus B",
        "feeder_id": "FDR_600_30_B17",
        "feeder_tag": "Feeder B17",
        "description": "IOC BUILDING",
        "service": "Institutional Administrative Complex",
        "length_m": 600.0,
        "cable_spec": "XLPE",
        "area_sqmm": 150.0,
        "voltage_v": 6600.0,
        "ir_a": 7.8,
        "iy_a": 7.8,
        "ib_a": 7.8,
        "power_factor": 0.950,
        "status": "ACTIVE"
    },

    # =========================================================================
    # SUBSTATION 600-30: BUS BAR A (6.6 kV Nominal)
    # =========================================================================
    {
        "substation": "Substation 600-30",
        "voltage_level_kv": 6.6,
        "bus_bar": "Bus A",
        "feeder_id": "FDR_600_30_A1",
        "feeder_tag": "Feeder A1",
        "description": "ES JIZ 300 02A S/S 600-38 I/C -1",
        "service": "Industrial Process Supply Incomer 1",
        "length_m": 554.0,
        "cable_spec": "XLPE",
        "area_sqmm": 150.0,
        "voltage_v": 6650.0,
        "ir_a": 116.0,
        "iy_a": 111.0,
        "ib_a": 115.0,
        "power_factor": 0.940,
        "status": "ACTIVE"
    },
    {
        "substation": "Substation 600-30",
        "voltage_level_kv": 6.6,
        "bus_bar": "Bus A",
        "feeder_id": "FDR_600_30_A2",
        "feeder_tag": "Feeder A2",
        "description": "TO 2MVA TR 600-03A AT S/S 600-30",
        "service": "Step-down TR Feeder 600-03A",
        "length_m": 48.0,
        "cable_spec": "XLPE",
        "area_sqmm": 150.0,
        "voltage_v": 6660.0,
        "ir_a": 28.0,
        "iy_a": 28.0,
        "ib_a": 28.0,
        "power_factor": 0.980,
        "status": "ACTIVE"
    },
    {
        "substation": "Substation 600-30",
        "voltage_level_kv": 6.6,
        "bus_bar": "Bus A",
        "feeder_id": "FDR_600_30_A3",
        "feeder_tag": "Feeder A3",
        "description": "TO 2MVA TR 600-05A AT S/S 600-31",
        "service": "Step-down TR Feeder to S/S 600-31 Bus A",
        "length_m": 510.0,
        "cable_spec": "XLPE",
        "area_sqmm": 150.0,
        "voltage_v": 6640.0,
        "ir_a": 10.0,
        "iy_a": 10.0,
        "ib_a": 10.0,
        "power_factor": 0.930,
        "status": "ACTIVE"
    },
    {
        "substation": "Substation 600-30",
        "voltage_level_kv": 6.6,
        "bus_bar": "Bus A",
        "feeder_id": "FDR_600_30_A4",
        "feeder_tag": "Feeder A4",
        "description": "TO 2MVA TR 600-06A AT S/S 600-32",
        "service": "Step-down TR Feeder to S/S 600-32 Bus A",
        "length_m": 500.0,
        "cable_spec": "XLPE",
        "area_sqmm": 150.0,
        "voltage_v": 6700.0,
        "ir_a": 28.0,
        "iy_a": 28.0,
        "ib_a": 28.0,
        "power_factor": 0.970,
        "status": "ACTIVE"
    },
    {
        "substation": "Substation 600-30",
        "voltage_level_kv": 6.6,
        "bus_bar": "Bus A",
        "feeder_id": "FDR_600_30_A5",
        "feeder_tag": "Feeder A5",
        "description": "ETRS652 -01A 2MVA TR S/S 600-33",
        "service": "Step-down TR Feeder to S/S 600-33",
        "length_m": 1011.0,
        "cable_spec": "XLPE",
        "area_sqmm": 150.0,
        "voltage_v": 6700.0,
        "ir_a": 25.0,
        "iy_a": 25.0,
        "ib_a": 25.0,
        "power_factor": 0.960,
        "status": "ACTIVE"
    },
    {
        "substation": "Substation 600-30",
        "voltage_level_kv": 6.6,
        "bus_bar": "Bus A",
        "feeder_id": "FDR_600_30_A6",
        "feeder_tag": "Feeder A6",
        "description": "BUS PT FOR BUS A",
        "service": "Bus Potential Transformer / Metering",
        "length_m": 10.0,
        "cable_spec": "Control Cable",
        "area_sqmm": 150.0,
        "voltage_v": 6650.0,
        "ir_a": 0.0,
        "iy_a": 0.0,
        "ib_a": 0.0,
        "power_factor": 1.000,
        "status": "METERING_PT"
    },
    {
        "substation": "Substation 600-30",
        "voltage_level_kv": 6.6,
        "bus_bar": "Bus A",
        "feeder_id": "FDR_600_30_A7",
        "feeder_tag": "Feeder A7",
        "description": "TO SW BD RS 600-10A AT S/S 600-34",
        "service": "Switchboard Distribution Feeder",
        "length_m": 1500.0,
        "cable_spec": "XLPE",
        "area_sqmm": 150.0,
        "voltage_v": 6620.0,
        "ir_a": 70.0,
        "iy_a": 72.0,
        "ib_a": 71.3,
        "power_factor": 0.930,
        "status": "ACTIVE"
    },
    {
        "substation": "Substation 600-30",
        "voltage_level_kv": 6.6,
        "bus_bar": "Bus A",
        "feeder_id": "FDR_600_30_A8",
        "feeder_tag": "Feeder A8",
        "description": "MAIN INCOMER BUS A",
        "service": "Primary Substation Incomer Bus A",
        "length_m": 50.0,
        "cable_spec": "Heavy Bus Duct",
        "area_sqmm": 400.0,
        "voltage_v": 6780.0,
        "ir_a": 390.0,
        "iy_a": 390.0,
        "ib_a": 390.0,
        "power_factor": 0.820,
        "status": "ACTIVE_INCOMER"
    },
    {
        "substation": "Substation 600-30",
        "voltage_level_kv": 6.6,
        "bus_bar": "Bus A",
        "feeder_id": "FDR_600_30_A9",
        "feeder_tag": "Feeder A9",
        "description": "MP RS65/MO83A OX SHIP LOADING PUMP",
        "service": "Marine Terminal OX Ship Loading Pump A",
        "length_m": 300.0,
        "cable_spec": "XLPE",
        "area_sqmm": 150.0,
        "voltage_v": 6620.0,
        "ir_a": 0.0,
        "iy_a": 0.0,
        "ib_a": 0.0,
        "power_factor": 0.880,
        "status": "OFF_STANDBY"
    },
    {
        "substation": "Substation 600-30",
        "voltage_level_kv": 6.6,
        "bus_bar": "Bus A",
        "feeder_id": "FDR_600_30_A10",
        "feeder_tag": "Feeder A10",
        "description": "GAIL INCOMER 1 HT 201 BUS 1AX",
        "service": "GAIL Gas Pipeline Incomer 1",
        "length_m": 520.0,
        "cable_spec": "XLPE",
        "area_sqmm": 150.0,
        "voltage_v": 6650.0,
        "ir_a": 96.0,
        "iy_a": 96.0,
        "ib_a": 96.0,
        "power_factor": 0.940,
        "status": "ACTIVE"
    },
    {
        "substation": "Substation 600-30",
        "voltage_level_kv": 6.6,
        "bus_bar": "Bus A",
        "feeder_id": "FDR_600_30_A11",
        "feeder_tag": "Feeder A11",
        "description": "O/G TO NEW TRANSFORMER AT 1J PUMP HOUSE",
        "service": "Cooling Water 1J Pump House Transformer",
        "length_m": 800.0,
        "cable_spec": "XLPE",
        "area_sqmm": 150.0,
        "voltage_v": 6670.0,
        "ir_a": 40.0,
        "iy_a": 40.0,
        "ib_a": 40.0,
        "power_factor": 0.860,
        "status": "ACTIVE"
    },
    {
        "substation": "Substation 600-30",
        "voltage_level_kv": 6.6,
        "bus_bar": "Bus A",
        "feeder_id": "FDR_600_30_A12",
        "feeder_tag": "Feeder A12",
        "description": "1800-SB 001A CEIL CAIRN INDIA",
        "service": "Upstream Crude Transfer Incomer 1",
        "length_m": 2100.0,
        "cable_spec": "XLPE",
        "area_sqmm": 150.0,
        "voltage_v": 6620.0,
        "ir_a": 8.0,
        "iy_a": 8.0,
        "ib_a": 8.0,
        "power_factor": 0.980,
        "status": "ACTIVE"
    },
    {
        "substation": "Substation 600-30",
        "voltage_level_kv": 6.6,
        "bus_bar": "Bus A",
        "feeder_id": "FDR_600_30_A13",
        "feeder_tag": "Feeder A13",
        "description": "MP - RW 621 M701C RTF MOTOR",
        "service": "Refinery Tank Farm Vapor Recovery Motor C",
        "length_m": 1000.0,
        "cable_spec": "XLPE",
        "area_sqmm": 150.0,
        "voltage_v": 6720.0,
        "ir_a": 26.0,
        "iy_a": 26.0,
        "ib_a": 26.0,
        "power_factor": 0.970,
        "status": "ACTIVE"
    },
    {
        "substation": "Substation 600-30",
        "voltage_level_kv": 6.6,
        "bus_bar": "Bus A",
        "feeder_id": "FDR_600_30_A14",
        "feeder_tag": "Feeder A14",
        "description": "MP - RW 621 M701A RTF MOTOR",
        "service": "Refinery Tank Farm Vapor Recovery Motor A",
        "length_m": 1000.0,
        "cable_spec": "XLPE",
        "area_sqmm": 150.0,
        "voltage_v": 6700.0,
        "ir_a": 27.0,
        "iy_a": 27.0,
        "ib_a": 27.0,
        "power_factor": 0.972,
        "status": "ACTIVE"
    },
    {
        "substation": "Substation 600-30",
        "voltage_level_kv": 6.6,
        "bus_bar": "Bus A",
        "feeder_id": "FDR_600_30_A15",
        "feeder_tag": "Feeder A15",
        "description": "ES JG 141-803 LC-1 STAFF HOUSING (SEC-2)",
        "service": "Township Staff Housing Sector 2",
        "length_m": 2000.0,
        "cable_spec": "XLPE",
        "area_sqmm": 150.0,
        "voltage_v": 6700.0,
        "ir_a": 8.0,
        "iy_a": 8.0,
        "ib_a": 8.0,
        "power_factor": 0.950,
        "status": "ACTIVE"
    },
    {
        "substation": "Substation 600-30",
        "voltage_level_kv": 6.6,
        "bus_bar": "Bus A",
        "feeder_id": "FDR_600_30_A16",
        "feeder_tag": "Feeder A16",
        "description": "ES JG 141-803 LC-1 STAFF HOUSING (SEC-1)",
        "service": "Township Staff Housing Sector 1 (Long Run)",
        "length_m": 3600.0,
        "cable_spec": "XLPE",
        "area_sqmm": 150.0,
        "voltage_v": 6610.0,
        "ir_a": 17.0,
        "iy_a": 16.0,
        "ib_a": 16.0,
        "power_factor": 0.940,
        "status": "ACTIVE"
    },

    # =========================================================================
    # SUBSTATION 600-31: 415 V MOTOR CONTROL CENTER (BUS A & BUS B)
    # =========================================================================
    {
        "substation": "Substation 600-31",
        "voltage_level_kv": 0.415,
        "bus_bar": "Bus A",
        "feeder_id": "FDR_600_31_1A",
        "feeder_tag": "Feeder 1A",
        "description": "INCOMER 1 FROM ET RS600-05A",
        "service": "MCC Main Incomer 1 Supply",
        "length_m": 15.0,
        "cable_spec": "Bus Duct",
        "area_sqmm": 300.0,
        "voltage_v": 419.0,
        "ir_a": 460.0,
        "iy_a": 460.0,
        "ib_a": 460.0,
        "power_factor": 0.870,
        "status": "ACTIVE_INCOMER"
    },
    {
        "substation": "Substation 600-31",
        "voltage_level_kv": 0.415,
        "bus_bar": "Bus A",
        "feeder_id": "FDR_600_31_3FA",
        "feeder_tag": "Feeder 3FA",
        "description": "TO 415V MCC SUBSTATION 600-31 EC-RS600-06",
        "service": "Sub-distribution MCC Bus Tie",
        "length_m": 80.0,
        "cable_spec": "XLPE",
        "area_sqmm": 150.0,
        "voltage_v": 416.0,
        "ir_a": 107.0,
        "iy_a": 107.0,
        "ib_a": 107.0,
        "power_factor": 0.870,
        "status": "ACTIVE"
    },
    {
        "substation": "Substation 600-31",
        "voltage_level_kv": 0.415,
        "bus_bar": "Bus A",
        "feeder_id": "FDR_600_31_9FA",
        "feeder_tag": "Feeder 9FA",
        "description": "NAPHTHA RAIL LOADING MP RS652-P007B",
        "service": "Naphtha Rail Tanker Loading Pump Motor",
        "length_m": 550.0,
        "cable_spec": "XLPE",
        "area_sqmm": 150.0,
        "voltage_v": 415.0,
        "ir_a": 215.0,
        "iy_a": 218.0,
        "ib_a": 215.0,
        "power_factor": 0.955,
        "status": "ACTIVE"
    },
    {
        "substation": "Substation 600-31",
        "voltage_level_kv": 0.415,
        "bus_bar": "Bus A",
        "feeder_id": "FDR_600_31_10FB",
        "feeder_tag": "Feeder 10FB",
        "description": "LPG RAIL LOADING PUMP MP RS652-P006C",
        "service": "Liquefied Petroleum Gas Loading Pump C",
        "length_m": 350.0,
        "cable_spec": "XLPE",
        "area_sqmm": 150.0,
        "voltage_v": 410.0,
        "ir_a": 148.0,
        "iy_a": 150.0,
        "ib_a": 150.0,
        "power_factor": 0.880,
        "status": "ACTIVE"
    },
    {
        "substation": "Substation 600-31",
        "voltage_level_kv": 0.415,
        "bus_bar": "Bus A",
        "feeder_id": "FDR_600_31_10FA",
        "feeder_tag": "Feeder 10FA",
        "description": "LPG RAIL LOADING PUMP MP RS652-P006B",
        "service": "Liquefied Petroleum Gas Loading Pump B",
        "length_m": 350.0,
        "cable_spec": "XLPE",
        "area_sqmm": 150.0,
        "voltage_v": 413.0,
        "ir_a": 145.0,
        "iy_a": 146.0,
        "ib_a": 145.7,
        "power_factor": 0.890,
        "status": "ACTIVE"
    },
    {
        "substation": "Substation 600-31",
        "voltage_level_kv": 0.415,
        "bus_bar": "Bus B",
        "feeder_id": "FDR_600_31_11FA",
        "feeder_tag": "Feeder 11FA",
        "description": "LPG RAIL LOADING PUMP",
        "service": "Liquefied Petroleum Gas Loading Pump A",
        "length_m": 350.0,
        "cable_spec": "XLPE",
        "area_sqmm": 150.0,
        "voltage_v": 417.0,
        "ir_a": 146.0,
        "iy_a": 145.0,
        "ib_a": 145.0,
        "power_factor": 0.930,
        "status": "ACTIVE"
    },
    {
        "substation": "Substation 600-31",
        "voltage_level_kv": 0.415,
        "bus_bar": "Bus B",
        "feeder_id": "FDR_600_31_11FB",
        "feeder_tag": "Feeder 11FB",
        "description": "NAPHTHA RAIL LOADING PUMP",
        "service": "Naphtha Rail Tanker Loading Pump Motor A",
        "length_m": 500.0,
        "cable_spec": "XLPE",
        "area_sqmm": 150.0,
        "voltage_v": 417.0,
        "ir_a": 195.0,
        "iy_a": 195.0,
        "ib_a": 195.0,
        "power_factor": 0.920,
        "status": "ACTIVE"
    },
    {
        "substation": "Substation 600-31",
        "voltage_level_kv": 0.415,
        "bus_bar": "Bus B",
        "feeder_id": "FDR_600_31_12FA",
        "feeder_tag": "Feeder 12FA",
        "description": "LPG RAIL LOADING PUMP",
        "service": "Liquefied Petroleum Gas Loading Pump D",
        "length_m": 400.0,
        "cable_spec": "XLPE",
        "area_sqmm": 150.0,
        "voltage_v": 416.0,
        "ir_a": 148.0,
        "iy_a": 147.0,
        "ib_a": 149.0,
        "power_factor": 0.940,
        "status": "ACTIVE"
    },
    {
        "substation": "Substation 600-31",
        "voltage_level_kv": 0.415,
        "bus_bar": "Bus B",
        "feeder_id": "FDR_600_31_8F",
        "feeder_tag": "Feeder 8F",
        "description": "INCOMER 2 FROM ET RS600-05A",
        "service": "MCC Main Incomer 2 Supply",
        "length_m": 15.0,
        "cable_spec": "Bus Duct",
        "area_sqmm": 300.0,
        "voltage_v": 418.0,
        "ir_a": 425.0,
        "iy_a": 425.0,
        "ib_a": 425.0,
        "power_factor": 0.910,
        "status": "ACTIVE_INCOMER"
    },
    {
        "substation": "Substation 600-31",
        "voltage_level_kv": 0.415,
        "bus_bar": "Bus B",
        "feeder_id": "FDR_600_31_6FB",
        "feeder_tag": "Feeder 6FB",
        "description": "415V MCC S/S 600-31 EC RS600-07",
        "service": "Sub-distribution MCC Bus Tie B",
        "length_m": 80.0,
        "cable_spec": "XLPE",
        "area_sqmm": 150.0,
        "voltage_v": 416.0,
        "ir_a": 104.0,
        "iy_a": 104.0,
        "ib_a": 104.0,
        "power_factor": 0.970,
        "status": "ACTIVE"
    },

    # =========================================================================
    # SUBSTATION 600-32: 415 V MOTOR CONTROL CENTER (BUS A & BUS B)
    # =========================================================================
    {
        "substation": "Substation 600-32",
        "voltage_level_kv": 0.415,
        "bus_bar": "Bus A",
        "feeder_id": "FDR_600_32_1",
        "feeder_tag": "Feeder 1",
        "description": "MAIN INCOMER BUS A",
        "service": "MCC Main Incomer 1 Supply",
        "length_m": 15.0,
        "cable_spec": "Bus Duct",
        "area_sqmm": 300.0,
        "voltage_v": 425.0,
        "ir_a": 280.0,
        "iy_a": 279.0,
        "ib_a": 279.0,
        "power_factor": 0.970,
        "status": "ACTIVE_INCOMER"
    },
    {
        "substation": "Substation 600-32",
        "voltage_level_kv": 0.415,
        "bus_bar": "Bus A",
        "feeder_id": "FDR_600_32_3FB",
        "feeder_tag": "Feeder 3FB",
        "description": "415V MCC SUBSTATION 600-32 EC RS 600-11",
        "service": "Sub-distribution MCC Bus Tie",
        "length_m": 60.0,
        "cable_spec": "XLPE",
        "area_sqmm": 150.0,
        "voltage_v": 420.0,
        "ir_a": 47.0,
        "iy_a": 47.0,
        "ib_a": 47.0,
        "power_factor": 0.960,
        "status": "ACTIVE"
    },
    {
        "substation": "Substation 600-32",
        "voltage_level_kv": 0.415,
        "bus_bar": "Bus A",
        "feeder_id": "FDR_600_32_4FA",
        "feeder_tag": "Feeder 4FA",
        "description": "HSD CHILLER MOTOR",
        "service": "High Speed Diesel Product Chilling Compressor",
        "length_m": 120.0,
        "cable_spec": "XLPE",
        "area_sqmm": 150.0,
        "voltage_v": 417.0,
        "ir_a": 22.0,
        "iy_a": 22.3,
        "ib_a": 22.3,
        "power_factor": 0.920,
        "status": "ACTIVE"
    },
    {
        "substation": "Substation 600-32",
        "voltage_level_kv": 0.415,
        "bus_bar": "Bus A",
        "feeder_id": "FDR_600_32_4FB",
        "feeder_tag": "Feeder 4FB",
        "description": "415V MCC SUBSTATION 600-32 EC RS 600-09",
        "service": "MCC Process Control Tie",
        "length_m": 80.0,
        "cable_spec": "XLPE",
        "area_sqmm": 150.0,
        "voltage_v": 417.0,
        "ir_a": 40.7,
        "iy_a": 40.0,
        "ib_a": 41.0,
        "power_factor": 0.932,
        "status": "ACTIVE"
    },
    {
        "substation": "Substation 600-32",
        "voltage_level_kv": 0.415,
        "bus_bar": "Bus A",
        "feeder_id": "FDR_600_32_11FB",
        "feeder_tag": "Feeder 11FB",
        "description": "ATF RAIL LOADING PUMP MP RS 652P005B",
        "service": "Aviation Turbine Fuel Rail Loading Pump B",
        "length_m": 450.0,
        "cable_spec": "XLPE",
        "area_sqmm": 150.0,
        "voltage_v": 416.0,
        "ir_a": 150.0,
        "iy_a": 150.6,
        "ib_a": 150.0,
        "power_factor": 0.910,
        "status": "ACTIVE"
    },
    {
        "substation": "Substation 600-32",
        "voltage_level_kv": 0.415,
        "bus_bar": "Bus A",
        "feeder_id": "FDR_600_32_12FA2",
        "feeder_tag": "Feeder 12FA2",
        "description": "SFD RAIL LOADING PUMP MP RS 652P002A",
        "service": "Super Fast Diesel Rail Loading Pump A",
        "length_m": 400.0,
        "cable_spec": "XLPE",
        "area_sqmm": 150.0,
        "voltage_v": 418.0,
        "ir_a": 143.0,
        "iy_a": 142.8,
        "ib_a": 143.0,
        "power_factor": 0.880,
        "status": "ACTIVE"
    },
    {
        "substation": "Substation 600-32",
        "voltage_level_kv": 0.415,
        "bus_bar": "Bus A",
        "feeder_id": "FDR_600_32_12FB2",
        "feeder_tag": "Feeder 12FB2",
        "description": "SFD RAIL LOADING PUMP MP RS 652P002C",
        "service": "Super Fast Diesel Rail Loading Pump C",
        "length_m": 400.0,
        "cable_spec": "XLPE",
        "area_sqmm": 150.0,
        "voltage_v": 418.0,
        "ir_a": 148.0,
        "iy_a": 148.0,
        "ib_a": 148.0,
        "power_factor": 0.904,
        "status": "ACTIVE"
    },
    {
        "substation": "Substation 600-32",
        "voltage_level_kv": 0.415,
        "bus_bar": "Bus A",
        "feeder_id": "FDR_600_32_12FA1",
        "feeder_tag": "Feeder 12FA1",
        "description": "ROAD LOADING OIL PUMP 1",
        "service": "Refinery Road Tanker Dispatch Pump 1",
        "length_m": 300.0,
        "cable_spec": "XLPE",
        "area_sqmm": 150.0,
        "voltage_v": 415.0,
        "ir_a": 160.0,
        "iy_a": 160.0,
        "ib_a": 160.0,
        "power_factor": 0.920,
        "status": "ACTIVE"
    },
    {
        "substation": "Substation 600-32",
        "voltage_level_kv": 0.415,
        "bus_bar": "Bus A",
        "feeder_id": "FDR_600_32_12FB1",
        "feeder_tag": "Feeder 12FB1",
        "description": "ROAD LOADING OIL PUMP 2",
        "service": "Refinery Road Tanker Dispatch Pump 2",
        "length_m": 300.0,
        "cable_spec": "XLPE",
        "area_sqmm": 150.0,
        "voltage_v": 415.0,
        "ir_a": 160.0,
        "iy_a": 160.0,
        "ib_a": 160.0,
        "power_factor": 0.920,
        "status": "ACTIVE"
    },
    {
        "substation": "Substation 600-32",
        "voltage_level_kv": 0.415,
        "bus_bar": "Bus B",
        "feeder_id": "FDR_600_32_11FA_B",
        "feeder_tag": "Feeder 11FA (Bus B)",
        "description": "FUEL OIL ROAD LOADING PUMP MOTOR 1",
        "service": "Heavy Fuel Oil Road Loading Pump 1",
        "length_m": 320.0,
        "cable_spec": "XLPE",
        "area_sqmm": 150.0,
        "voltage_v": 416.0,
        "ir_a": 163.0,
        "iy_a": 163.0,
        "ib_a": 163.0,
        "power_factor": 0.900,
        "status": "ACTIVE"
    },
    {
        "substation": "Substation 600-32",
        "voltage_level_kv": 0.415,
        "bus_bar": "Bus B",
        "feeder_id": "FDR_600_32_11FB_B",
        "feeder_tag": "Feeder 11FB (Bus B)",
        "description": "FUEL OIL ROAD LOADING PUMP MOTOR 2",
        "service": "Heavy Fuel Oil Road Loading Pump 2",
        "length_m": 320.0,
        "cable_spec": "XLPE",
        "area_sqmm": 150.0,
        "voltage_v": 416.0,
        "ir_a": 161.5,
        "iy_a": 161.5,
        "ib_a": 162.0,
        "power_factor": 0.910,
        "status": "ACTIVE"
    },
    {
        "substation": "Substation 600-32",
        "voltage_level_kv": 0.415,
        "bus_bar": "Bus B",
        "feeder_id": "FDR_600_32_13FA",
        "feeder_tag": "Feeder 13FA",
        "description": "HSD RAIL LOADING PUMP",
        "service": "High Speed Diesel Rail Loading Pump Motor",
        "length_m": 420.0,
        "cable_spec": "XLPE",
        "area_sqmm": 150.0,
        "voltage_v": 416.0,
        "ir_a": 133.9,
        "iy_a": 134.0,
        "ib_a": 133.0,
        "power_factor": 0.933,
        "status": "ACTIVE"
    },
    {
        "substation": "Substation 600-32",
        "voltage_level_kv": 0.415,
        "bus_bar": "Bus B",
        "feeder_id": "FDR_600_32_14FA",
        "feeder_tag": "Feeder 14FA",
        "description": "ATF RAIL LOADING PUMP MP RS 652 P005A",
        "service": "Aviation Turbine Fuel Rail Loading Pump A",
        "length_m": 450.0,
        "cable_spec": "XLPE",
        "area_sqmm": 150.0,
        "voltage_v": 418.0,
        "ir_a": 148.0,
        "iy_a": 148.0,
        "ib_a": 148.0,
        "power_factor": 0.887,
        "status": "ACTIVE"
    },
    {
        "substation": "Substation 600-32",
        "voltage_level_kv": 0.415,
        "bus_bar": "Bus B",
        "feeder_id": "FDR_600_32_14FB",
        "feeder_tag": "Feeder 14FB",
        "description": "ATF RAIL LOADING PUMP MP RS 652 P005C",
        "service": "Aviation Turbine Fuel Rail Loading Pump C",
        "length_m": 450.0,
        "cable_spec": "XLPE",
        "area_sqmm": 150.0,
        "voltage_v": 417.0,
        "ir_a": 149.0,
        "iy_a": 149.0,
        "ib_a": 149.0,
        "power_factor": 0.890,
        "status": "ACTIVE"
    },
    {
        "substation": "Substation 600-32",
        "voltage_level_kv": 0.415,
        "bus_bar": "Bus B",
        "feeder_id": "FDR_600_32_7FB",
        "feeder_tag": "Feeder 7FB",
        "description": "415V MCC SUBSTATION 600-32 EC RS 600-10",
        "service": "MCC Process Sub-distribution",
        "length_m": 90.0,
        "cable_spec": "XLPE",
        "area_sqmm": 150.0,
        "voltage_v": 418.0,
        "ir_a": 43.0,
        "iy_a": 43.0,
        "ib_a": 43.0,
        "power_factor": 0.980,
        "status": "ACTIVE"
    },
    {
        "substation": "Substation 600-32",
        "voltage_level_kv": 0.415,
        "bus_bar": "Bus B",
        "feeder_id": "FDR_600_32_BFB",
        "feeder_tag": "Feeder BFB",
        "description": "415V MCC SUBSTATION 600-32 EC RS 600-12",
        "service": "MCC Process Sub-distribution",
        "length_m": 90.0,
        "cable_spec": "XLPE",
        "area_sqmm": 150.0,
        "voltage_v": 418.0,
        "ir_a": 45.0,
        "iy_a": 45.0,
        "ib_a": 45.0,
        "power_factor": 0.990,
        "status": "ACTIVE"
    },
    {
        "substation": "Substation 600-32",
        "voltage_level_kv": 0.415,
        "bus_bar": "Bus B",
        "feeder_id": "FDR_600_32_2",
        "feeder_tag": "Feeder 2",
        "description": "MAIN INCOMER BUS B",
        "service": "MCC Main Incomer 2 Supply",
        "length_m": 15.0,
        "cable_spec": "Bus Duct",
        "area_sqmm": 300.0,
        "voltage_v": 424.0,
        "ir_a": 280.0,
        "iy_a": 279.0,
        "ib_a": 279.0,
        "power_factor": 0.920,
        "status": "ACTIVE_INCOMER"
    }
]


def process_ril_telemetry() -> pd.DataFrame:
    """
    Computes rigorous three-phase electrical physics on RIL field measurements:
    - Average current and IEEE 141 phase current imbalance %
    - Voltage deviation % from nominal (6.6 kV or 415 V)
    - Apparent Power S (kVA), Active Power P (kW), Reactive Power Q (kVAR)
    - Cable Conductor Resistance R (Ohms)
    - Conductor Copper Losses P_loss (kW) and Feeder Loss %
    """
    records = []
    
    for f in RIL_RAW_FEEDERS:
        ir, iy, ib = f["ir_a"], f["iy_a"], f["ib_a"]
        i_avg = round((ir + iy + ib) / 3.0, 2)
        
        # IEEE Std 141 Current Imbalance
        if i_avg > 0:
            max_dev = max(abs(ir - i_avg), abs(iy - i_avg), abs(ib - i_avg))
            i_imb_pct = round((max_dev / i_avg) * 100.0, 2)
        else:
            i_imb_pct = 0.0
            
        v_act = f["voltage_v"]
        v_nom = f["voltage_level_kv"] * 1000.0
        v_dev_pct = round(((v_act - v_nom) / v_nom) * 100.0, 2)
        
        # Conductor Resistance Calculation: R = R_per_km * (Length / 1000)
        # Select R per km based on cable cross section
        if f["area_sqmm"] >= 240.0:
            r_per_km = R_PER_KM_240_XLPE
        else:
            r_per_km = R_PER_KM_150_XLPE
            
        r_feeder = round(r_per_km * (f["length_m"] / 1000.0), 4)
        
        pf = f["power_factor"]
        
        # Power Calculations: S = sqrt(3) * V * I / 1000 (kVA)
        s_kva = round((3 ** 0.5) * v_act * i_avg / 1000.0, 2)
        p_kw = round(s_kva * pf, 2)
        q_kvar = round(math.sqrt(max(0.0, s_kva ** 2 - p_kw ** 2)), 2)
        
        # Conductor Joule Loss: P_loss = (Ir^2 + Iy^2 + Ib^2) * R * 10^-3 (kW)
        p_loss_kw = round((ir ** 2 + iy ** 2 + ib ** 2) * r_feeder / 1000.0, 4)
        p_input = p_kw + p_loss_kw
        loss_pct = round((p_loss_kw / p_input) * 100.0, 3) if p_input > 0 else 0.0
        
        # Power Factor Category
        if pf >= 0.95:
            pf_cat = "Excellent (>=0.95)"
        elif pf >= 0.90:
            pf_cat = "Acceptable (0.90-0.94)"
        elif pf >= 0.85:
            pf_cat = "Moderate (0.85-0.89)"
        else:
            pf_cat = "Critical / Penalty (<0.85)"
            
        records.append({
            "substation": f["substation"],
            "voltage_level_kv": f["voltage_level_kv"],
            "bus_bar": f["bus_bar"],
            "feeder_id": f["feeder_id"],
            "feeder_tag": f["feeder_tag"],
            "description": f["description"],
            "service": f["service"],
            "length_m": f["length_m"],
            "cable_spec": f["cable_spec"],
            "area_sqmm": f["area_sqmm"],
            "resistance_ohm": r_feeder,
            "voltage_v": v_act,
            "voltage_deviation_pct": v_dev_pct,
            "current_r_a": ir,
            "current_y_a": iy,
            "current_b_a": ib,
            "current_avg_a": i_avg,
            "current_imbalance_pct": i_imb_pct,
            "power_factor": pf,
            "pf_category": pf_cat,
            "apparent_power_kva": s_kva,
            "active_power_kw": p_kw,
            "reactive_power_kvar": q_kvar,
            "conductor_loss_kw": p_loss_kw,
            "feeder_loss_pct": loss_pct,
            "status": f["status"]
        })
        
    df = pd.DataFrame(records)
    
    # Export to CSV
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(PROCESSED_DATA_DIR / "ril_feeder_performance_analysis.csv", index=False)
    
    # Save to SQLite
    conn = sqlite3.connect(DB_PATH)
    df.to_sql("fact_ril_field_measurements", conn, if_exists="replace", index=False)
    conn.commit()
    conn.close()
    
    print(f"Ingested and analyzed {len(df)} authentic RIL field feeders into database and CSV!")
    return df


if __name__ == "__main__":
    df_ril = process_ril_telemetry()
    print("\n=== TOP 5 RIL FEEDERS BY CONDUCTOR LOSS (kW) ===")
    print(df_ril.sort_values(by="conductor_loss_kw", ascending=False)[[
        "feeder_tag", "description", "substation", "length_m", "current_avg_a", "conductor_loss_kw", "feeder_loss_pct"
    ]].head())
    
    print("\n=== TOP 5 RIL FEEDERS BY PHASE CURRENT IMBALANCE % ===")
    print(df_ril.sort_values(by="current_imbalance_pct", ascending=False)[[
        "feeder_tag", "description", "substation", "current_r_a", "current_y_a", "current_b_a", "current_imbalance_pct"
    ]].head())
