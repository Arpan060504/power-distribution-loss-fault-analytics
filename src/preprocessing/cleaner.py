"""
Data Preprocessing, Cleaning, and Relational Export Pipeline
Power Distribution Loss & Fault Analytics System
"""

import os
import sqlite3
import pandas as pd
from typing import Dict, Any, Tuple
from src.utils.config import (
    RAW_DATA_DIR, PROCESSED_DATA_DIR, DATABASE_DIR, DB_PATH
)
from src.data_generation.network_model import (
    get_dim_substation, get_dim_transformer, get_dim_feeder,
    get_dim_load, get_dim_fault, generate_dim_calendar
)
from src.data_generation.generator import generate_time_series_data
from src.data_validation.validator import DataQualityEngine
from src.feature_engineering.features import compute_engineering_features
from src.anomaly_detection.detector import AnomalyDetectionEngine, FaultPredictiveModel


class DistributionAnalyticsPipeline:
    """
    End-to-End Orchestrator:
    Raw Generation -> Data Quality Audit -> Cleaning -> Feature Engineering -> Anomaly Detection -> Database Load
    """
    
    def __init__(self, db_path: str = str(DB_PATH)):
        self.db_path = db_path
        self.dq_engine = DataQualityEngine()
        self.anomaly_engine = AnomalyDetectionEngine()
        self.predictive_model = FaultPredictiveModel()
        
    def run_full_pipeline(self, days: int = 182, seed: int = 42) -> Dict[str, Any]:
        """
        Executes the entire end-to-end data pipeline.
        Saves files into data/raw, data/processed, and database/power_distribution.db.
        """
        print("=== STEP 1: GENERATING NETWORK TOPOLOGY & CALENDAR ===")
        dim_sub = get_dim_substation()
        dim_tr = get_dim_transformer()
        dim_fdr = get_dim_feeder()
        dim_load = get_dim_load()
        dim_flt = get_dim_fault()
        dim_cal = generate_dim_calendar(start_date="2026-03-01", days=days)
        
        print(f"Substations: {len(dim_sub)}, Transformers: {len(dim_tr)}, Feeders: {len(dim_fdr)}, Calendar Days: {len(dim_cal)}")
        
        print("\n=== STEP 2: GENERATING 6-MONTH RAW TIME-SERIES WITH INJECTED DEFECTS ===")
        df_raw_meas, df_faults, df_maint = generate_time_series_data(
            start_date="2026-03-01", days=days, seed=seed, inject_defects=True
        )
        
        # Save raw data
        raw_meas_path = RAW_DATA_DIR / "raw_electrical_measurements.csv"
        df_raw_meas.to_csv(raw_meas_path, index=False)
        print(f"Saved raw data to {raw_meas_path} ({len(df_raw_meas):,} rows)")
        
        print("\n=== STEP 3: EXECUTING DATA QUALITY ENGINE AUDIT ===")
        dq_report = self.dq_engine.run_audit(df_raw_meas)
        self.dq_engine.print_report(dq_report)
        
        print("\n=== STEP 4: CLEANING DATASET & RE-DERIVING CONSISTENT PHYSICS ===")
        df_clean, _ = self.dq_engine.clean_dataset(df_raw_meas)
        print(f"Cleaned dataset: {len(df_clean):,} records (100% verified physics)")
        
        print("\n=== STEP 5: COMPUTING ENGINEERING FEATURES & POWER QUALITY METRICS ===")
        df_features = compute_engineering_features(df_clean)
        
        print("\n=== STEP 6: EXECUTING DUAL ANOMALY DETECTION (Z-SCORE & ISOLATION FOREST) ===")
        df_analyzed = self.anomaly_engine.detect_anomalies(df_features)
        
        print("\n=== STEP 7: EVALUATING PREDICTIVE FAULT RISK MODEL ===")
        ml_eval = self.predictive_model.train_and_evaluate(df_analyzed)
        print(f"Random Forest Fault Prediction F1-Score: {ml_eval['random_forest']['f1_score']:.4f} (ROC-AUC: {ml_eval['random_forest']['roc_auc']:.4f})")
        print("Top 3 Leading Operational Predictors:", list(ml_eval['random_forest']['feature_importances'].items())[:3])
        
        print("\n=== STEP 8: EXPORTING PROCESSED DATASETS FOR POWER BI & SQL ===")
        df_analyzed.to_csv(PROCESSED_DATA_DIR / "fact_electrical_measurements.csv", index=False)
        df_faults.to_csv(PROCESSED_DATA_DIR / "fact_fault_events.csv", index=False)
        df_maint.to_csv(PROCESSED_DATA_DIR / "fact_maintenance.csv", index=False)
        dim_sub.to_csv(PROCESSED_DATA_DIR / "dim_substation.csv", index=False)
        dim_tr.to_csv(PROCESSED_DATA_DIR / "dim_transformer.csv", index=False)
        dim_fdr.to_csv(PROCESSED_DATA_DIR / "dim_feeder.csv", index=False)
        dim_load.to_csv(PROCESSED_DATA_DIR / "dim_load.csv", index=False)
        dim_flt.to_csv(PROCESSED_DATA_DIR / "dim_fault.csv", index=False)
        dim_cal.to_csv(PROCESSED_DATA_DIR / "dim_calendar.csv", index=False)
        print("Exported all processed fact and dimension CSV files to data/processed/")
        
        print("\n=== STEP 9: LOADING RELATIONAL DATABASE (SQLITE) ===")
        self._load_sqlite(dim_sub, dim_tr, dim_fdr, dim_load, dim_flt, dim_cal, df_analyzed, df_faults, df_maint)
        
        return {
            "dq_report": dq_report,
            "ml_eval": ml_eval,
            "total_measurements": len(df_analyzed),
            "total_faults": len(df_faults),
            "total_maintenance": len(df_maint)
        }
        
    def _load_sqlite(
        self, dim_sub, dim_tr, dim_fdr, dim_load, dim_flt, dim_cal,
        df_meas, df_faults, df_maint
    ):
        """
        Creates SQLite database with proper relational schema and indexes.
        """
        os.makedirs(DATABASE_DIR, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        
        # Write tables
        dim_sub.to_sql("dim_substation", conn, if_exists="replace", index=False)
        dim_tr.to_sql("dim_transformer", conn, if_exists="replace", index=False)
        dim_fdr.to_sql("dim_feeder", conn, if_exists="replace", index=False)
        dim_load.to_sql("dim_load", conn, if_exists="replace", index=False)
        dim_flt.to_sql("dim_fault", conn, if_exists="replace", index=False)
        dim_cal.to_sql("dim_calendar", conn, if_exists="replace", index=False)
        
        df_meas.to_sql("fact_electrical_measurements", conn, if_exists="replace", index=False)
        df_faults.to_sql("fact_fault_events", conn, if_exists="replace", index=False)
        df_maint.to_sql("fact_maintenance", conn, if_exists="replace", index=False)
        
        cursor = conn.cursor()
        # Create performance indexes for analytical queries
        print("Creating relational database indexes...")
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_meas_feeder ON fact_electrical_measurements (feeder_id);",
            "CREATE INDEX IF NOT EXISTS idx_meas_time ON fact_electrical_measurements (timestamp);",
            "CREATE INDEX IF NOT EXISTS idx_meas_date ON fact_electrical_measurements (date_key);",
            "CREATE INDEX IF NOT EXISTS idx_meas_transformer ON fact_electrical_measurements (transformer_id);",
            "CREATE INDEX IF NOT EXISTS idx_fault_feeder ON fact_fault_events (feeder_id);",
            "CREATE INDEX IF NOT EXISTS idx_fault_time ON fact_fault_events (timestamp);",
            "CREATE INDEX IF NOT EXISTS idx_maint_feeder ON fact_maintenance (feeder_id);"
        ]
        for idx_sql in indexes:
            cursor.execute(idx_sql)
            
        conn.commit()
        conn.close()
        print(f"Successfully loaded relational database at {self.db_path}!")


if __name__ == "__main__":
    pipeline = DistributionAnalyticsPipeline()
    pipeline.run_full_pipeline(days=182, seed=42)
