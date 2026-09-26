"""
Generate 07_ril_substation_case_study.ipynb
"""

import nbformat as nbf
from pathlib import Path

NOTEBOOKS_DIR = Path(__file__).resolve().parent.parent.parent / "notebooks"
NOTEBOOKS_DIR.mkdir(parents=True, exist_ok=True)

nb = nbf.v4.new_notebook()
nb.cells = [
    nbf.v4.new_markdown_cell("""# 07. Industrial Case Study: Reliance Industries Limited (RIL) Substation 600-30 & Satellite MCCs

## 🏭 Real Industrial Telemetry Context
During an industrial internship at **Reliance Industries Limited (RIL)** at a major refinery and petrochemical complex, authentic operational telemetry was collected across:
1. **Substation 600-30 (6.6 kV Medium Voltage Switchboard):**
   * **Bus Bar A:** Incomer A8 (390 A, PF 0.82), GAIL gas pipeline incomer, refinery tank farm (RTF) vapor recovery motors (M701A/C), township staff housing (LC-1, lines up to 3.6 km), and step-down transformer feeders.
   * **Bus Bar B:** Incomer B3 (190 A from 16 MVA TR-600-01B, PF 0.965), Cairn India crude transfer lines, RTF motors, and feeders to satellite substations 600-31, 600-32, 600-33, 600-34, 600-35, and 600-38.
2. **Substation 600-31 (415 V Low Voltage Motor Control Center):**
   * Product dispatch: Naphtha rail loading pumps (MP RS652-P007B) and LPG rail loading pumps (MP RS652-P006B/C, 145-218 A).
3. **Substation 600-32 (415 V Low Voltage Motor Control Center):**
   * Refinery dispatch: Aviation Turbine Fuel (ATF) rail loading (MP RS 652 P005A/B/C), High Speed Diesel (HSD) rail loading, Super Fast Diesel (SFD) rail loading, and road oil dispatch pumps.

This notebook executes an in-depth **power engineering audit** on this authentic industrial dataset.
"""),
    nbf.v4.new_code_cell("""import sys
from pathlib import Path
import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

BASE_DIR = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from src.utils.ril_data import process_ril_telemetry, DB_PATH

df_ril = process_ril_telemetry()
print(f"Loaded {len(df_ril)} authentic RIL field feeders.")
df_ril.head(8)
"""),
    nbf.v4.new_markdown_cell("""## 1. Substation 600-30 (6.6 kV): Bus A vs Bus B Incomer & Load Balancing
We analyze the loading distribution between Bus A (Incomer A8, 390 A) and Bus B (Incomer B3, 190 A).
"""),
    nbf.v4.new_code_cell("""bus_summary = df_ril[df_ril[\"substation\"] == \"Substation 600-30\"].groupby(\"bus_bar\").agg(
    total_feeders=(\"feeder_id\", \"count\"),
    active_feeders=(\"status\", lambda s: (s != \"OFF_SPARE\") & (s != \"OFF_STANDBY\")),
    total_load_kw=(\"active_power_kw\", \"sum\"),
    total_loss_kw=(\"conductor_loss_kw\", \"sum\"),
    mean_pf=(\"power_factor\", \"mean\")
).reset_index()

print(\"=== SUBSTATION 600-30 (6.6 kV) BUS SUMMARY ===\")
print(bus_summary)
"""),
    nbf.v4.new_markdown_cell("""## 2. Low-Voltage (415 V) Product Loading Pumps: Conductor Loss Analysis
Why do 415 V product loading pumps (Naphtha, LPG, ATF) have significantly higher loss percentages than 6.6 kV lines?
**Engineering Principle:**
$$P_{loss} = 3 I^2 R$$
For equivalent power $P$, operating at $415\\text{ V}$ requires $\\approx 16\\times$ higher current than at $6.6\\text{ kV}$. Since Joule dissipation scales with $I^2$, conductor dissipation is up to $250\\times$ higher per unit active power!
"""),
    nbf.v4.new_code_cell("""top_loss_pumps = df_ril[df_ril[\"status\"] == \"ACTIVE\"].sort_values(by=\"feeder_loss_pct\", ascending=False).head(10)

plt.figure(figsize=(11, 5))
bars = plt.barh(top_loss_pumps[\"feeder_tag\"] + \" - \" + top_loss_pumps[\"description\"], top_loss_pumps[\"feeder_loss_pct\"], color=\"#e53e3e\")
plt.xlabel(\"Conductor Loss Percentage (%)\", fontsize=11, fontweight=\"bold\")
plt.title(\"Top 10 RIL Refinery Feeders by Conductor Loss % (Joule Dissipation)\", fontsize=12, fontweight=\"bold\")
for bar in bars:
    w = bar.get_width()
    plt.text(w + 0.1, bar.get_y() + bar.get_height()/2, f\"{w:.2f}%\", va=\"center\", fontsize=9)
plt.xlim(0, max(top_loss_pumps[\"feeder_loss_pct\"]) * 1.15)
plt.tight_layout()
plt.show()
"""),
    nbf.v4.new_markdown_cell("""## 3. Phase Current Imbalance Audit (IEEE Std 141)
We identify circuits with significant current unbalance between R, Y, and B phases.
"""),
    nbf.v4.new_code_cell("""unbalance_feeders = df_ril[df_ril[\"current_imbalance_pct\"] > 3.0].sort_values(by=\"current_imbalance_pct\", ascending=False)

print(\"RIL Feeders with Elevated Phase Current Imbalance (IEEE Std 141):\")
print(unbalance_feeders[[\"feeder_tag\", \"substation\", \"description\", \"current_r_a\", \"current_y_a\", \"current_b_a\", \"current_imbalance_pct\"]])

plt.figure(figsize=(10, 4.5))
sns.barplot(data=unbalance_feeders, x=\"feeder_tag\", y=\"current_imbalance_pct\", palette=\"YlOrRd_r\")
plt.axhline(5.0, color=\"orange\", linestyle=\"--\", label=\"IEEE 141 5% Warning Limit\")
plt.title(\"Phase Current Imbalance Across RIL Field Feeders\", fontsize=12, fontweight=\"bold\")
plt.ylabel(\"Current Imbalance (%)\")
plt.xlabel(\"Feeder Tag\")
plt.legend()
plt.tight_layout()
plt.show()
"""),
    nbf.v4.new_markdown_cell("""## 4. Cable Length vs Conductor Loss Correlation
We plot route length against conductor loss for $150\\text{ mm}^2$ and $240\\text{ mm}^2$ XLPE cables.
"""),
    nbf.v4.new_code_cell("""active_feeders = df_ril[(df_ril[\"status\"] == \"ACTIVE\") & (df_ril[\"length_m\"] > 0)]

plt.figure(figsize=(9, 5))
sns.scatterplot(
    data=active_feeders,
    x=\"length_m\",
    y=\"conductor_loss_kw\",
    hue=\"voltage_level_kv\",
    size=\"current_avg_a\",
    palette=\"Set1\",
    sizes=(40, 250)
)
plt.title(\"Cable Route Length vs Conductor Loss (kW) by Voltage Level\", fontsize=12, fontweight=\"bold\")
plt.xlabel(\"Cable Run Length (Meters)\")
plt.ylabel(\"Estimated Conductor Copper Loss (kW)\")
plt.grid(True, linestyle=\"--\", alpha=0.5)
plt.tight_layout()
plt.show()
""")
]

with open(NOTEBOOKS_DIR / "07_ril_substation_case_study.ipynb", "w", encoding="utf-8") as f:
    nbf.write(nb, f)
print("Generated 07_ril_substation_case_study.ipynb")
