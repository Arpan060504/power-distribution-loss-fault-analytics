"""
Automated Jupyter Notebooks Generator
Creates all 6 analytical notebooks for the Power Distribution Analytics System
"""

import nbformat as nbf
from pathlib import Path

NOTEBOOKS_DIR = Path(__file__).resolve().parent.parent.parent / "notebooks"
NOTEBOOKS_DIR.mkdir(parents=True, exist_ok=True)


def create_nb_01():
    """01_data_quality.ipynb"""
    nb = nbf.v4.new_notebook()
    nb.cells = [
        nbf.v4.new_markdown_cell("""# 01. Data Quality Engine & Telemetry Validation

## Electrical Engineering Context
In electrical utility distribution systems, Supervisory Control and Data Acquisition (SCADA) systems and Advanced Metering Infrastructure (AMI) record thousands of telemetry data points every hour. However, real-world utility data is notoriously vulnerable to:
* **Potential Transformer (PT) / Current Transformer (CT) transducer saturation or open-circuit glitches**
* **Communication packet drops over cellular/GPRS/RF mesh networks**
* **Transducer polarity wiring reversal (leading to negative power factor readings)**
* **Uncalibrated sensors reporting active power $P > S$**

This notebook executes an automated **Data Quality Engine** that audits 100,000+ raw measurements against fundamental electrical boundaries and physical laws.
"""),
        nbf.v4.new_code_cell("""import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Set paths
BASE_DIR = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from src.data_validation.validator import DataQualityEngine
from src.utils.config import RAW_DATA_DIR, PROCESSED_DATA_DIR

print(f"Base Directory: {BASE_DIR}")
"""),
        nbf.v4.new_markdown_cell("""## 1. Ingesting Raw Distribution Telemetry
We load the raw measurements dataset containing 6 months of 30-minute interval SCADA readings across 12 distribution feeders.
"""),
        nbf.v4.new_code_cell("""raw_csv_path = RAW_DATA_DIR / "raw_electrical_measurements.csv"
df_raw = pd.read_csv(raw_csv_path)
print(f"Ingested Raw Records: {len(df_raw):,}")
df_raw.head()
"""),
        nbf.v4.new_markdown_cell("""## 2. Executing Data Quality Audit
We evaluate physical boundary checks:
* **Voltage Validity:** $8,000\\text{ V} \\le V_{avg} \\le 14,500\\text{ V}$ (11 kV nominal line-to-line)
* **Current Non-Negativity:** $I_{avg} \\ge 0\\text{ A}$
* **Power Factor Bounds:** $0.50 \\le PF \\le 1.00$
* **Physics Law:** $P \\le S$ ($P = \\sqrt{3} V I PF / 1000$)
* **Primary Key Uniqueness:** (feeder_id, timestamp)
"""),
        nbf.v4.new_code_cell("""dq_engine = DataQualityEngine()
audit_report = dq_engine.run_audit(df_raw)
report_text = dq_engine.print_report(audit_report)
"""),
        nbf.v4.new_markdown_cell("""## 3. Visualizing Telemetry Defect Distributions
We visualize the defect composition and data quality score.
"""),
        nbf.v4.new_code_cell("""defect_categories = {
    "Duplicates": audit_report["duplicate_records"],
    "Missing Telemetry": audit_report["missing_record_rows"],
    "Voltage Out-of-Bounds": audit_report["voltage_anomalies"],
    "Current Out-of-Bounds": audit_report["current_anomalies"],
    "Invalid PF (<0.5 or >1)": audit_report["invalid_pf_records"],
    "Physics Inconsistent (P>S)": audit_report["inconsistent_power_records"]
}

plt.figure(figsize=(10, 4.5))
bars = plt.barh(list(defect_categories.keys()), list(defect_categories.values()), color="#e53e3e")
plt.xlabel("Flagged Defective Records Count", fontsize=11, fontweight="bold")
plt.title(f"SCADA Telemetry Defect Breakdown (Overall Quality: {audit_report['overall_data_quality_pct']}%)", fontsize=12, fontweight="bold")
for bar in bars:
    w = bar.get_width()
    plt.text(w + 5, bar.get_y() + bar.get_height()/2, f"{int(w):,}", va="center", fontsize=10)
plt.xlim(0, max(defect_categories.values()) * 1.2)
plt.tight_layout()
plt.show()
"""),
        nbf.v4.new_markdown_cell("""## 4. Dataset Cleaning & Physics Re-Derivation
We remove corrupted records, re-derive electrical powers $(S, P, Q)$ using physical equations, and verify 100% clean output.
"""),
        nbf.v4.new_code_cell("""df_clean, _ = dq_engine.clean_dataset(df_raw)
print(f"Verified Pristine Output Records: {len(df_clean):,}")
print("Checking for remaining nulls:")
print(df_clean.isnull().sum()[df_clean.isnull().sum() > 0])
""")
    ]
    with open(NOTEBOOKS_DIR / "01_data_quality.ipynb", "w", encoding="utf-8") as f:
        nbf.write(nb, f)
    print("Generated 01_data_quality.ipynb")


def create_nb_02():
    """02_eda.ipynb"""
    nb = nbf.v4.new_notebook()
    nb.cells = [
        nbf.v4.new_markdown_cell("""# 02. Exploratory Data Analysis & System Load Dynamics

## Electrical Engineering Context
Distribution networks exhibit pronounced diurnal, seasonal, and load-dependent behavioral profiles. In this notebook, we explore:
* **Diurnal load cycles:** Industrial 3-shift operations vs residential dual-peaks (morning/evening) vs commercial business hours.
* **Ambient temperature correlation:** Summer cooling loads inflating active power demand.
* **Electrical correlation matrix:** Relationships between $V, I, P, Q, S, PF, T_{amb}, T_{equip}$.
* **Transformer coincident demand:** Aggregated loading across substations.
"""),
        nbf.v4.new_code_cell("""import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

BASE_DIR = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from src.utils.config import PROCESSED_DATA_DIR

df_meas = pd.read_csv(PROCESSED_DATA_DIR / "fact_electrical_measurements.csv")
dim_fdr = pd.read_csv(PROCESSED_DATA_DIR / "dim_feeder.csv")
df_meas["timestamp"] = pd.to_datetime(df_meas["timestamp"])
print(f"Loaded {len(df_meas):,} clean records.")
"""),
        nbf.v4.new_markdown_cell("""## 1. Diurnal Load Profiles by Load Category
We analyze hourly active power curves to observe shift work, commercial peaks, and domestic evening surges.
"""),
        nbf.v4.new_code_cell("""df_meas["hour"] = df_meas["timestamp"].dt.hour
df_merged = df_meas.merge(dim_fdr[["feeder_id", "load_category"]], on="feeder_id")

diurnal = df_merged.groupby(["load_category", "hour"])["active_power_kw"].mean().reset_index()

plt.figure(figsize=(12, 5.5))
for cat, grp in diurnal.groupby("load_category"):
    plt.plot(grp["hour"], grp["active_power_kw"], marker="o", label=cat, linewidth=2)
plt.title("Diurnal Active Power Profile by Industrial / Municipal Load Category", fontsize=13, fontweight="bold")
plt.xlabel("Hour of Day (00:00 - 23:00)", fontsize=11)
plt.ylabel("Mean Active Demand (kW)", fontsize=11)
plt.xticks(range(0, 24, 2))
plt.grid(True, linestyle="--", alpha=0.6)
plt.legend(bbox_to_anchor=(1.02, 1), loc="upper left")
plt.tight_layout()
plt.show()
"""),
        nbf.v4.new_markdown_cell("""## 2. Electrical Quantities Correlation Heatmap
We examine cross-correlations across voltages, currents, active/reactive powers, power factor, and temperatures.
"""),
        nbf.v4.new_code_cell("""corr_cols = [
    "voltage_avg", "current_avg", "active_power_kw", "reactive_power_kvar",
    "apparent_power_kva", "power_factor", "feeder_loss_kw", "feeder_loss_pct",
    "ambient_temperature_c", "equipment_temperature_c"
]
corr_matrix = df_meas[corr_cols].corr()

plt.figure(figsize=(10, 7.5))
sns.heatmap(corr_matrix, annot=True, fmt=".2f", cmap="coolwarm", cbar=True, square=True)
plt.title("Correlation Matrix of Electrical & Thermal Quantities", fontsize=13, fontweight="bold")
plt.tight_layout()
plt.show()
"""),
        nbf.v4.new_markdown_cell("""## 3. Transformer Loading Distribution
We evaluate how transformer loading percentages vary across the fleet.
"""),
        nbf.v4.new_code_cell("""plt.figure(figsize=(10, 4.5))
sns.boxplot(data=df_meas, x="transformer_id", y="transformer_loading_pct", palette="Set2")
plt.axhline(100.0, color="red", linestyle="--", label="100% Rated Capacity")
plt.axhline(80.0, color="orange", linestyle=":", label="80% Alert Threshold")
plt.title("Transformer Loading % Distribution Across 6 Months", fontsize=12, fontweight="bold")
plt.xlabel("Transformer ID")
plt.ylabel("Loading (% MVA)")
plt.legend()
plt.tight_layout()
plt.show()
""")
    ]
    with open(NOTEBOOKS_DIR / "02_eda.ipynb", "w", encoding="utf-8") as f:
        nbf.write(nb, f)
    print("Generated 02_eda.ipynb")


def create_nb_03():
    """03_power_quality.ipynb"""
    nb = nbf.v4.new_notebook()
    nb.cells = [
        nbf.v4.new_markdown_cell("""# 03. Power Quality Compliance: Voltage Regulation & IEEE Std 141 Phase Imbalance

## Electrical Engineering Context
Power Quality directly impacts equipment lifespan, motor torque stability, and technical efficiency. In this notebook, we evaluate:
1. **Voltage Regulation (IEEE Std 1159 / IEC 60038):**
   $$\\text{Voltage Deviation \\%} = \\frac{V_{actual} - V_{nominal}}{V_{nominal}} \\times 100$$
   Nominal limits are $\\pm 5\\%$. Sags $<-10\\%$ risk motor stalls and contactor dropouts.
2. **Current Imbalance (IEEE Std 141 / NEMA MG 1):**
   $$I_{imbalance} = \\frac{\\max(|I_r - I_{avg}|, |I_y - I_{avg}|, |I_b - I_{avg}|)}{I_{avg}} \\times 100$$
   An imbalance of $5\\%$ induces a $25\\%$ increase in motor winding temperature rise!
3. **Power Factor & Reactive Energy Penalties:**
   Operational compliance below $0.85$ triggers regulatory financial penalties.
"""),
        nbf.v4.new_code_cell("""import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

BASE_DIR = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from src.utils.config import PROCESSED_DATA_DIR

df_meas = pd.read_csv(PROCESSED_DATA_DIR / "fact_electrical_measurements.csv")
dim_fdr = pd.read_csv(PROCESSED_DATA_DIR / "dim_feeder.csv")
"""),
        nbf.v4.new_markdown_cell("""## 1. Voltage Deviation vs Regulatory Standard Bands
We categorize intervals into Normal $(\\pm 5\\%)$, Overvoltage $(>+5\\%)$, Undervoltage $(-5\\% \\text{ to } -10\\%)$, and Critical Sags $(<-10\\%)$.
"""),
        nbf.v4.new_code_cell("""v_band_counts = df_meas["voltage_quality_band"].value_counts()
print("Voltage Quality Compliance Summary:")
print(v_band_counts)

plt.figure(figsize=(8, 4.5))
sns.countplot(data=df_meas, y="voltage_quality_band", palette="coolwarm", order=v_band_counts.index)
plt.title("Distribution of IEEE 1159 Voltage Deviation Bands", fontsize=12, fontweight="bold")
plt.xlabel("Telemetry Measurement Count")
plt.tight_layout()
plt.show()
"""),
        nbf.v4.new_markdown_cell("""## 2. Phase Current Imbalance Across Feeders (IEEE Std 141)
We identify feeders with chronic unbalance exceeding the $5\\%$ warning and $10\\%$ critical limits.
"""),
        nbf.v4.new_code_cell("""plt.figure(figsize=(12, 5))
sns.boxplot(data=df_meas, x="feeder_id", y="current_imbalance_pct", palette="magma")
plt.axhline(5.0, color="orange", linestyle="--", label="IEEE 141 5% Warning Threshold")
plt.axhline(10.0, color="red", linestyle="-", label="10% Critical Imbalance Limit")
plt.title("Phase Current Imbalance Distribution by Feeder", fontsize=12, fontweight="bold")
plt.xlabel("Feeder ID")
plt.ylabel("Current Imbalance %")
plt.legend()
plt.tight_layout()
plt.show()
"""),
        nbf.v4.new_markdown_cell("""## 3. Power Factor Tariff Penalty Exposure
We calculate the cumulative hours each feeder operated below $0.85$ power factor.
"""),
        nbf.v4.new_code_cell("""pf_pen = df_meas.groupby("feeder_id")["pf_penalty_incurred"].agg(
    intervals="sum",
    penalty_hours=lambda s: s.sum() * 0.5,
    pct_time=lambda s: (s.sum() / len(s)) * 100.0
).reset_index().sort_values(by="penalty_hours", ascending=False)

print("Top Feeders by Commercial PF Penalty Exposure:")
print(pf_pen.head(6))
""")
    ]
    with open(NOTEBOOKS_DIR / "03_power_quality.ipynb", "w", encoding="utf-8") as f:
        nbf.write(nb, f)
    print("Generated 03_power_quality.ipynb")


def create_nb_04():
    """04_loss_analysis.ipynb"""
    nb = nbf.v4.new_notebook()
    nb.cells = [
        nbf.v4.new_markdown_cell("""# 04. Feeder Conductor Losses & Empirical Proof of Loss ∝ I²

## Electrical Engineering Context
In electrical distribution networks, technical losses consist primarily of:
1. **Conductor Copper / Joule Heating Losses:**
   $$P_{loss} = 3 \\cdot I_{avg}^2 \\cdot R_{feeder} = (I_r^2 + I_y^2 + I_b^2) \\cdot R_{feeder}$$
2. **Transformer Core (Iron) and Copper Losses:**
   $$P_{loss\\_TR} = P_0 + \\left(\\frac{S}{S_{rated}}\\right)^2 P_k$$

In this notebook, we empirically investigate whether the generated telemetry strictly adheres to the physical quadratic law $\\text{Loss} \\propto I^2$, rank feeders by total energy dissipation, and analyze the financial impact of line resistance.
"""),
        nbf.v4.new_code_cell("""import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

BASE_DIR = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from src.utils.config import PROCESSED_DATA_DIR

df_meas = pd.read_csv(PROCESSED_DATA_DIR / "fact_electrical_measurements.csv")
dim_fdr = pd.read_csv(PROCESSED_DATA_DIR / "dim_feeder.csv")
"""),
        nbf.v4.new_markdown_cell("""## 1. Feeder Conductor Loss Ranking
We aggregate cumulative energy delivery vs technical dissipation.
"""),
        nbf.v4.new_code_cell("""loss_summary = df_meas.groupby("feeder_id").agg({
    "energy_kwh": "sum",
    "feeder_loss_kw": lambda s: (s * 0.5).sum(),
    "feeder_loss_pct": "mean",
    "current_avg": "mean"
}).reset_index()

loss_summary["Delivered_MWh"] = (loss_summary["energy_kwh"] / 1000.0).round(2)
loss_summary["Loss_MWh"] = (loss_summary["feeder_loss_kw"] / 1000.0).round(2)
loss_summary["Avg_Loss_Pct"] = loss_summary["feeder_loss_pct"].round(2)

loss_summary = loss_summary.merge(dim_fdr[["feeder_id", "feeder_name", "length_km", "total_resistance_ohm"]], on="feeder_id")
loss_summary = loss_summary.sort_values(by="Avg_Loss_Pct", ascending=False)

print("Feeder Technical Loss Scorecard:")
print(loss_summary[["feeder_id", "feeder_name", "length_km", "total_resistance_ohm", "Delivered_MWh", "Loss_MWh", "Avg_Loss_Pct"]])
"""),
        nbf.v4.new_markdown_cell("""## 2. Empirical Verification of Physical Law: Loss ∝ I²
We fit a second-degree polynomial regression on Current vs Conductor Loss and evaluate the coefficient of determination $R^2$.
"""),
        nbf.v4.new_code_cell("""sample_fdr = df_meas[df_meas["feeder_id"] == "FDR_01"].sample(1500, random_state=42)
x = sample_fdr["current_avg"].values
y = sample_fdr["feeder_loss_kw"].values

# Fit quadratic model y = a * x^2 + b
poly_coeffs = np.polyfit(x ** 2, y, 1)
y_pred = poly_coeffs[0] * (x ** 2) + poly_coeffs[1]
slope, intercept, r_value, p_value, std_err = stats.linregress(x ** 2, y)

print(f"Quadratic Regression: P_loss = {poly_coeffs[0]:.6f} * I^2 + {poly_coeffs[1]:.4f}")
print(f"Coefficient of Determination R^2 = {r_value**2:.4f}")

plt.figure(figsize=(9, 5))
plt.scatter(x, y, alpha=0.3, color="#3182ce", label="Telemetry Data Points")
sort_idx = np.argsort(x)
plt.plot(x[sort_idx], y_pred[sort_idx], color="#e53e3e", linewidth=2.5, label=f"Physical Fit (R² = {r_value**2:.4f})")
plt.title("Empirical Verification of Joule's First Law: P_loss ∝ I² on Feeder FDR_01", fontsize=12, fontweight="bold")
plt.xlabel("Feeder Current I_avg (Amperes)", fontsize=11)
plt.ylabel("Feeder Technical Loss (kW)", fontsize=11)
plt.grid(True, linestyle="--", alpha=0.5)
plt.legend()
plt.tight_layout()
plt.show()
"""),
        nbf.v4.new_markdown_cell("""## 3. Conductor Resistance vs Percentage Energy Loss
We illustrate how conductor selection and line length dictate technical efficiency.
"""),
        nbf.v4.new_code_cell("""plt.figure(figsize=(9, 4.5))
sns.regplot(data=loss_summary, x="total_resistance_ohm", y="Avg_Loss_Pct", color="#805ad5", scatter_kws={"s": 80})
for _, row in loss_summary.iterrows():
    plt.text(row["total_resistance_ohm"] + 0.1, row["Avg_Loss_Pct"], row["feeder_id"], fontsize=9)
plt.title("Average Loss Percentage vs Total Feeder Conductor Resistance R (Ω)", fontsize=12, fontweight="bold")
plt.xlabel("Total Line Resistance (Ohms)")
plt.ylabel("Average Technical Loss %")
plt.grid(True, linestyle="--", alpha=0.5)
plt.tight_layout()
plt.show()
""")
    ]
    with open(NOTEBOOKS_DIR / "04_loss_analysis.ipynb", "w", encoding="utf-8") as f:
        nbf.write(nb, f)
    print("Generated 04_loss_analysis.ipynb")


def create_nb_05():
    """05_fault_analysis.ipynb"""
    nb = nbf.v4.new_notebook()
    nb.cells = [
        nbf.v4.new_markdown_cell("""# 05. Distribution Fault Epidemiology, Duration & Reliability Metrics

## Electrical Engineering Context
Distribution protection relays isolate abnormal conditions to prevent conductor burn-downs and transformer thermal degradation:
* **IEEE 50/51:** Instantaneous / Time-delay Overcurrent
* **IEEE 27:** Undervoltage / Bus Sag
* **IEEE 59:** Overvoltage / Ferranti Swell
* **IEEE 46:** Negative-sequence Current Imbalance
* **IEEE 49:** Thermal Overload

In this notebook, we analyze fault frequency, compute a transparent **Fault Severity Score**, evaluate outage downtime, and examine recurring feeder trip intervals.
"""),
        nbf.v4.new_code_cell("""import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

BASE_DIR = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from src.utils.config import PROCESSED_DATA_DIR
from src.fault_analysis.fault_engine import FaultAnalyticsEngine

df_faults = pd.read_csv(PROCESSED_DATA_DIR / "fact_fault_events.csv")
df_faults["timestamp"] = pd.to_datetime(df_faults["timestamp"])
print(f"Loaded {len(df_faults)} historical protection relay fault events.")
"""),
        nbf.v4.new_markdown_cell("""## 1. Reliability Indices & Fault Epidemiology Summary
We calculate MTBF, MTTR, and cumulative outage hours.
"""),
        nbf.v4.new_code_cell("""summary = FaultAnalyticsEngine.compute_summary(df_faults)
for k, v in summary.items():
    if not isinstance(v, dict):
        print(f"{k.replace('_', ' ').title()}: {v}")
"""),
        nbf.v4.new_markdown_cell("""## 2. Fault Severity Score Distribution
Our transparent rule-based score is computed as:
$$\\text{Severity} = 35 \\times \\left(\\frac{I_{peak}}{2 \\cdot I_{rated}}\\right) + 25 \\times \\left(\\frac{\\text{Sag \\%}}{20}\\right) + 20 \\times \\left(\\frac{\\text{Duration}}{120}\\right) + 20$$
"""),
        nbf.v4.new_code_cell("""plt.figure(figsize=(10, 4.5))
sns.histplot(data=df_faults, x="severity_score", hue="fault_type_id", multiple="stack", bins=20, palette="tab10")
plt.title("Distribution of Rule-Based Fault Severity Scores", fontsize=12, fontweight="bold")
plt.xlabel("Severity Score (0 - 100)")
plt.ylabel("Incident Count")
plt.tight_layout()
plt.show()
"""),
        nbf.v4.new_markdown_cell("""## 3. Feeder Fault Concentration (Pareto Principle)
We evaluate which feeders account for the disproportionate share of network trips.
"""),
        nbf.v4.new_code_cell("""fdr_counts = df_faults["feeder_id"].value_counts().reset_index()
fdr_counts.columns = ["Feeder ID", "Incidents"]

plt.figure(figsize=(11, 4.5))
bars = plt.bar(fdr_counts["Feeder ID"], fdr_counts["Incidents"], color="#dd6b20")
plt.title("Total Unscheduled Breaker Trips by Feeder (6-Month Period)", fontsize=12, fontweight="bold")
plt.xlabel("Feeder ID")
plt.ylabel("Number of Trips")
for bar in bars:
    h = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2, h + 0.3, str(int(h)), ha="center")
plt.tight_layout()
plt.show()
""")
    ]
    with open(NOTEBOOKS_DIR / "05_fault_analysis.ipynb", "w", encoding="utf-8") as f:
        nbf.write(nb, f)
    print("Generated 05_fault_analysis.ipynb")


def create_nb_06():
    """06_anomaly_detection.ipynb"""
    nb = nbf.v4.new_notebook()
    nb.cells = [
        nbf.v4.new_markdown_cell("""# 06. Dual-Engine Anomaly Detection & Predictive Fault Risk Modeling

## Electrical Engineering Context
Detecting early thermal degradation, partial discharge, or abnormal harmonic loading before an electrical trip occurs is a core objective of modern distribution asset management.
In this notebook, we implement and benchmark:
1. **Method 1 — Statistical Anomaly Engine:**
   Z-scores $(|Z| > 3.0)$ and IQR outlier bounds with explicit parameter attribution (e.g. Current Spike, Voltage Sag, Thermal Hotspot).
2. **Method 2 — Machine Learning Anomaly Engine:**
   Multivariate **Isolation Forest** operating across voltage, current, PF, imbalance, loss %, and equipment temperature.
3. **Consensus Analysis:**
   Comparing statistical vs ML agreement.
4. **Predictive Fault Risk Modeling (Section 13):**
   Evaluating whether operational indicators can forecast faults within a 2-hour forward horizon using temporal train-test splitting.
"""),
        nbf.v4.new_code_cell("""import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

BASE_DIR = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from src.utils.config import PROCESSED_DATA_DIR
from src.anomaly_detection.detector import FaultPredictiveModel

df_meas = pd.read_csv(PROCESSED_DATA_DIR / "fact_electrical_measurements.csv")
print(f"Loaded {len(df_meas):,} telemetry records.")
"""),
        nbf.v4.new_markdown_cell("""## 1. Anomaly Detection Engine Consensus Breakdown
We compare how many records were flagged by Statistical Z-Score only, Isolation Forest only, or Dual-Method confirmed.
"""),
        nbf.v4.new_code_cell("""consensus_summary = df_meas["anomaly_consensus"].value_counts()
print("Anomaly Consensus Summary:")
print(consensus_summary)

plt.figure(figsize=(9, 4.5))
df_meas["anomaly_consensus"].value_counts().plot(kind="barh", color=["#2d3748", "#dd6b20", "#3182ce", "#e53e3e"])
plt.title("Statistical vs Machine Learning Anomaly Consensus Tiers", fontsize=12, fontweight="bold")
plt.xlabel("Record Count")
plt.tight_layout()
plt.show()
"""),
        nbf.v4.new_markdown_cell("""## 2. Statistical Anomaly Causal Attribution
Why were statistical outliers flagged? We examine the engineering root-causes.
"""),
        nbf.v4.new_code_cell("""stat_reasons = df_meas[df_meas["stat_anomaly_flag"] == 1]["stat_anomaly_reason"].value_counts().head(10)
print("Top 10 Statistical Anomaly Drivers:")
print(stat_reasons)
"""),
        nbf.v4.new_markdown_cell("""## 3. Predictive Fault Risk Modeling (Temporal Train-Test Split)
We evaluate forward fault prediction over the next 2-hour window using Logistic Regression and Random Forest.
"""),
        nbf.v4.new_code_cell("""predictor = FaultPredictiveModel(prediction_horizon_intervals=4)
results = predictor.train_and_evaluate(df_meas)

print(f"Total Test Samples: {results['total_test_samples']:,}")
print(f"Actual Faults in Test Horizon: {results['actual_faults_in_test']}")
print("\\n--- RANDOM FOREST CLASSIFICATION PERFORMANCE ---")
print(f"Precision : {results['random_forest']['precision']:.4f}")
print(f"Recall    : {results['random_forest']['recall']:.4f}")
print(f"F1-Score  : {results['random_forest']['f1_score']:.4f}")
print(f"ROC-AUC   : {results['random_forest']['roc_auc']:.4f}")
print(f"Confusion Matrix: {results['random_forest']['confusion_matrix']}")

print("\\nLeading Operational Predictors of Imminent Fault Risk:")
for feat, imp in list(results['random_forest']['feature_importances'].items())[:5]:
    print(f"  * {feat:<28}: {imp:.4f}")
""")
    ]
    with open(NOTEBOOKS_DIR / "06_anomaly_detection.ipynb", "w", encoding="utf-8") as f:
        nbf.write(nb, f)
    print("Generated 06_anomaly_detection.ipynb")


if __name__ == "__main__":
    create_nb_01()
    create_nb_02()
    create_nb_03()
    create_nb_04()
    create_nb_05()
    create_nb_06()
    print("All 6 analytical Jupyter notebooks generated successfully!")
