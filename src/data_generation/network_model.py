"""
Distribution Network Topology and Dimension Tables Generator
Power Distribution Loss & Fault Analytics System
"""

import pandas as pd
from datetime import datetime, timedelta
from src.utils.config import SUBSTATIONS, TRANSFORMERS, FEEDERS, LOAD_TYPES, FAULT_TYPES


def get_dim_substation() -> pd.DataFrame:
    """Returns the Substation dimension dataframe."""
    return pd.DataFrame(SUBSTATIONS)


def get_dim_transformer() -> pd.DataFrame:
    """Returns the Transformer dimension dataframe."""
    return pd.DataFrame(TRANSFORMERS)


def get_dim_feeder() -> pd.DataFrame:
    """Returns the Feeder dimension dataframe with real physical conductor properties."""
    return pd.DataFrame(FEEDERS)


def get_dim_load() -> pd.DataFrame:
    """Returns the Load Profile dimension dataframe."""
    return pd.DataFrame(LOAD_TYPES)


def get_dim_fault() -> pd.DataFrame:
    """Returns the Fault Types dimension dataframe."""
    return pd.DataFrame(FAULT_TYPES)


def generate_dim_calendar(start_date: str = "2026-03-01", days: int = 182) -> pd.DataFrame:
    """
    Generates a comprehensive Calendar dimension table covering the observation window.
    Includes quarter, day of week, weekend flags, seasonal definitions.
    """
    start = pd.to_datetime(start_date)
    date_list = [start + timedelta(days=x) for x in range(days)]
    
    calendar_records = []
    for d in date_list:
        month = d.month
        # Typical meteorological seasons for temperate/subtropical grid
        if month in [3, 4, 5]:
            season = "Pre-Monsoon / Summer"
        elif month in [6, 7, 8]:
            season = "Monsoon / High Humidity"
        elif month in [9, 10, 11]:
            season = "Post-Monsoon / Autumn"
        else:
            season = "Winter"
            
        calendar_records.append({
            "date_key": int(d.strftime("%Y%m%d")),
            "full_date": d.strftime("%Y-%m-%d"),
            "year": d.year,
            "quarter": f"Q{d.quarter}",
            "month": d.month,
            "month_name": d.strftime("%B"),
            "day": d.day,
            "day_of_week": d.dayofweek + 1,  # 1 = Monday, 7 = Sunday
            "day_name": d.strftime("%A"),
            "is_weekend": 1 if d.dayofweek >= 5 else 0,
            "season": season
        })
        
    return pd.DataFrame(calendar_records)
