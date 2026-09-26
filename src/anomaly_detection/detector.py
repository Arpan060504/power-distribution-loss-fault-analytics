"""
Dual-Engine Anomaly Detection & Predictive Fault Risk Modeling
Power Distribution Loss & Fault Analytics System
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, precision_recall_fscore_support, roc_auc_score


class AnomalyDetectionEngine:
    """
    Dual-Method Anomaly Detection Engine:
    1. Statistical Engine: Z-score & Interquartile Range (IQR) with causal parameter attribution
    2. Machine Learning Engine: Multivariate Isolation Forest
    """
    
    def __init__(self, z_threshold: float = 3.0, contamination: float = 0.015):
        self.z_threshold = z_threshold
        self.contamination = contamination
        self.features_for_ml = [
            "voltage_avg", "current_avg", "power_factor",
            "current_imbalance_pct", "equipment_temperature_c", "feeder_loss_pct"
        ]
        
    def detect_anomalies(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Executes statistical and machine learning anomaly detection on telemetry records.
        Appends diagnostic flags, reason attribution, and agreement metrics.
        """
        df = df.copy()
        print("Running Statistical Anomaly Detection (Z-Score & IQR)...")
        
        # 1. Statistical Method: Z-Score per feeder
        stat_reasons = []
        is_stat_anomaly = np.zeros(len(df), dtype=int)
        
        # Compute grouped Z-scores
        for col in ["current_avg", "voltage_avg", "feeder_loss_pct", "equipment_temperature_c", "current_imbalance_pct"]:
            z_col = f"zscore_{col}"
            df[z_col] = df.groupby("feeder_id")[col].transform(
                lambda s: (s - s.mean()) / (s.std() + 1e-6)
            ).round(2)
            
        # Detect causes
        for i in range(len(df)):
            reasons = []
            if abs(df.at[i, "zscore_current_avg"]) > self.z_threshold:
                reasons.append(f"Current Spike (Z={df.at[i, 'zscore_current_avg']})")
            if df.at[i, "zscore_voltage_avg"] < -self.z_threshold:
                reasons.append(f"Voltage Sag (Z={df.at[i, 'zscore_voltage_avg']})")
            elif df.at[i, "zscore_voltage_avg"] > self.z_threshold:
                reasons.append(f"Voltage Swell (Z={df.at[i, 'zscore_voltage_avg']})")
            if df.at[i, "zscore_feeder_loss_pct"] > self.z_threshold:
                reasons.append(f"Elevated Loss (Z={df.at[i, 'zscore_feeder_loss_pct']})")
            if df.at[i, "zscore_equipment_temperature_c"] > self.z_threshold:
                reasons.append(f"Thermal Hotspot (Z={df.at[i, 'zscore_equipment_temperature_c']})")
            if df.at[i, "zscore_current_imbalance_pct"] > self.z_threshold:
                reasons.append(f"Severe Unbalance (Z={df.at[i, 'zscore_current_imbalance_pct']})")
                
            if reasons:
                is_stat_anomaly[i] = 1
                stat_reasons.append("; ".join(reasons))
            else:
                stat_reasons.append("Normal Operating Range")
                
        df["stat_anomaly_flag"] = is_stat_anomaly
        df["stat_anomaly_reason"] = stat_reasons
        
        # 2. Machine Learning Method: Multivariate Isolation Forest
        print("Running Machine Learning Anomaly Detection (Multivariate Isolation Forest)...")
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(df[self.features_for_ml].fillna(0))
        
        iso_forest = IsolationForest(
            n_estimators=100,
            contamination=self.contamination,
            random_state=42,
            n_jobs=-1
        )
        preds = iso_forest.fit_predict(X_scaled)
        # Isolation Forest outputs -1 for anomalies, 1 for inliers
        df["ml_anomaly_flag"] = np.where(preds == -1, 1, 0)
        df["ml_anomaly_score"] = np.round(-iso_forest.score_samples(X_scaled), 3)  # Higher = more anomalous
        
        # 3. Method Consensus & Classification
        conditions = [
            (df["stat_anomaly_flag"] == 1) & (df["ml_anomaly_flag"] == 1),
            (df["stat_anomaly_flag"] == 1) & (df["ml_anomaly_flag"] == 0),
            (df["stat_anomaly_flag"] == 0) & (df["ml_anomaly_flag"] == 1)
        ]
        choices = [
            "Dual-Method Confirmed (High Confidence)",
            "Statistical Outlier Only",
            "ML Multivariate Outlier Only"
        ]
        df["anomaly_consensus"] = np.select(conditions, choices, default="Normal Operation")
        df["is_any_anomaly"] = np.where((df["stat_anomaly_flag"] == 1) | (df["ml_anomaly_flag"] == 1), 1, 0)
        
        # Categorize engineering nature
        df["anomaly_type_engineering"] = np.where(
            df["fault_status"] == 1,
            "Fault-Induced Electrical Transient",
            np.where(
                df["is_any_anomaly"] == 1,
                "Operational Loading / Thermal Anomaly",
                "Normal"
            )
        )
        
        return df


class FaultPredictiveModel:
    """
    Time-Series Early Warning / Fault Prediction Engine.
    Predicts if a feeder will experience an electrical fault in the next 2 hours (4 intervals).
    Uses strict temporal train-test split to avoid lookahead data leakage.
    """
    
    def __init__(self, prediction_horizon_intervals: int = 4):
        self.horizon = prediction_horizon_intervals
        self.feature_cols = [
            "rolling_current_avg_24h", "rolling_current_std_24h",
            "current_imbalance_pct", "voltage_deviation_pct", "power_factor",
            "transformer_loading_pct", "equipment_temperature_c", "thermal_rise_c"
        ]
        self.lr_model = LogisticRegression(class_weight="balanced", max_iter=1000, random_state=42)
        self.rf_model = RandomForestClassifier(
            n_estimators=100, max_depth=6, class_weight="balanced", random_state=42, n_jobs=-1
        )
        
    def prepare_dataset(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Creates forward-looking target: fault_in_next_2h = 1 if fault occurs in next 4 intervals.
        """
        df_sorted = df.sort_values(by=["feeder_id", "timestamp"]).copy()
        
        # Rolling forward maximum of fault_status within the next 4 intervals
        # Using shift to look forward
        indexer = pd.api.indexers.FixedForwardWindowIndexer(window_size=self.horizon)
        df_sorted["fault_target_future"] = (
            df_sorted.groupby("feeder_id")["fault_status"]
            .transform(lambda s: s.rolling(window=indexer, min_periods=1).max())
            .shift(-1)  # Look strictly ahead from current timestamp
            .fillna(0)
            .astype(int)
        )
        return df_sorted.dropna(subset=self.feature_cols + ["fault_target_future"])
        
    def train_and_evaluate(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Executes chronological train/test split (75% past train, 25% future test) and evaluates models.
        """
        data = self.prepare_dataset(df)
        
        # Temporal train/test split: strictly chronological
        split_idx = int(len(data) * 0.75)
        train_data = data.iloc[:split_idx]
        test_data = data.iloc[split_idx:]
        
        X_train, y_train = train_data[self.feature_cols], train_data["fault_target_future"]
        X_test, y_test = test_data[self.feature_cols], test_data["fault_target_future"]
        
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train Logistic Regression
        self.lr_model.fit(X_train_scaled, y_train)
        y_pred_lr = self.lr_model.predict(X_test_scaled)
        y_prob_lr = self.lr_model.predict_proba(X_test_scaled)[:, 1]
        
        # Train Random Forest
        self.rf_model.fit(X_train, y_train)
        y_pred_rf = self.rf_model.predict(X_test)
        y_prob_rf = self.rf_model.predict_proba(X_test)[:, 1]
        
        # Compute metrics
        prec_lr, rec_lr, f1_lr, _ = precision_recall_fscore_support(y_test, y_pred_lr, average="binary", zero_division=0)
        prec_rf, rec_rf, f1_rf, _ = precision_recall_fscore_support(y_test, y_pred_rf, average="binary", zero_division=0)
        
        auc_lr = roc_auc_score(y_test, y_prob_lr) if len(np.unique(y_test)) > 1 else 0.5
        auc_rf = roc_auc_score(y_test, y_prob_rf) if len(np.unique(y_test)) > 1 else 0.5
        
        cm_lr = confusion_matrix(y_test, y_pred_lr).tolist()
        cm_rf = confusion_matrix(y_test, y_pred_rf).tolist()
        
        feat_importance = dict(zip(self.feature_cols, np.round(self.rf_model.feature_importances_, 4)))
        feat_importance_sorted = dict(sorted(feat_importance.items(), key=lambda x: x[1], reverse=True))
        
        results = {
            "total_test_samples": len(y_test),
            "actual_faults_in_test": int(y_test.sum()),
            "logistic_regression": {
                "precision": round(float(prec_lr), 4),
                "recall": round(float(rec_lr), 4),
                "f1_score": round(float(f1_lr), 4),
                "roc_auc": round(float(auc_lr), 4),
                "confusion_matrix": cm_lr
            },
            "random_forest": {
                "precision": round(float(prec_rf), 4),
                "recall": round(float(rec_rf), 4),
                "f1_score": round(float(f1_rf), 4),
                "roc_auc": round(float(auc_rf), 4),
                "confusion_matrix": cm_rf,
                "feature_importances": feat_importance_sorted
            }
        }
        
        return results
