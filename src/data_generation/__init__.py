"""
Data generation module
"""
from src.data_generation.network_model import (
    get_dim_substation, get_dim_transformer, get_dim_feeder,
    get_dim_load, get_dim_fault, generate_dim_calendar
)
from src.data_generation.generator import generate_time_series_data
