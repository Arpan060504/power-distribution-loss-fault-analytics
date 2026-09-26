# Analytical & Electrical Engineering Methodology

This document outlines the theoretical, mathematical, and algorithmic foundations implemented in the **Power Distribution Loss & Fault Analytics System**.

---

## 1. Network Topology & Single-Line Electrical Model

The electrical distribution model simulates a typical dual-substation industrial and municipal distribution network operating at **33 kV sub-transmission** and **11 kV medium-voltage distribution**.

```text
Incoming 33 kV Utility Grid Supply
  ├── Main Substation 1: SUB_NORTH (20 MVA, 33/11 kV)
  │     ├── Transformer TR_01 (10 MVA, Dyn11, %Z=6.5%)
  │     │     ├── FDR_01: Industrial Process (Automotive Machining, ACSR Dog 3.2 km)
  │     │     ├── FDR_02: Induction Motors (Heavy Pumping, XLPE 185 mm² 2.5 km)
  │     │     └── FDR_03: Residential Staff Township (ACSR Rabbit 4.0 km)
  │     └── Transformer TR_02 (10 MVA, Dyn11, %Z=6.5%)
  │           ├── FDR_04: Commercial Tech Park (XLPE 240 mm² 1.8 km)
  │           ├── FDR_05: Municipal Water & Lighting (ACSR Dog 5.2 km)
  │           └── FDR_06: Suburban Periphery Mixed (ACSR Rabbit 6.8 km)
  └── Main Substation 2: SUB_SOUTH (30 MVA, 33/11 kV)
        ├── Transformer TR_03 (12.5 MVA, Dyn11, %Z=7.0%)
        │     ├── FDR_07: Heavy Metallurgy & Arc Furnace (Copper 300 mm² 2.2 km)
        │     └── FDR_08: Petrochemical Continuous Plant (XLPE 185 mm² 3.0 km)
        ├── Transformer TR_04 (12.5 MVA, Dyn11, %Z=7.0%)
        │     ├── FDR_09: Harbor Cold Storage (ACSR Dog 3.6 km)
        │     ├── FDR_10: Auxiliary Utility (XLPE 150 mm² 1.6 km)
        │     └── FDR_11: Regional Hospital Critical (Dual XLPE 240 mm² 2.1 km)
        └── Transformer TR_05 (5.0 MVA, Dyn11, %Z=5.75%)
              └── FDR_12: Rural Agricultural Irrigation (ACSR Weasel 8.5 km)
```

---

## 2. Governing Electrical Formulas

### 2.1 Three-Phase Balanced & Unbalanced Relationships

1. **Average Phase Voltage ($V_{avg}$):**
   $$V_{avg} = \frac{V_r + V_y + V_b}{3}$$
   Where $V_r, V_y, V_b$ represent phase-to-phase voltages (Nominal $V_{LL} = 11,000\text{ V}$).

2. **Average Phase Current ($I_{avg}$):**
   $$I_{avg} = \frac{I_r + I_y + I_b}{3}$$

3. **Voltage Deviation Percentage ($\Delta V_{\%}$):**
   $$\Delta V_{\%} = \frac{V_{avg} - V_{nominal}}{V_{nominal}} \times 100$$
   *Regulatory Limits (IEEE Std 1159):* Normal operating band is $\pm 5\%$. Sags exceeding $-10\%$ trigger undervoltage relay operations (IEEE 27).

4. **Phase Current Imbalance (IEEE Std 141 / NEMA MG 1):**
   $$I_{imbalance} = \frac{\max\left(|I_r - I_{avg}|, |I_y - I_{avg}|, |I_b - I_{avg}|\right)}{I_{avg}} \times 100$$
   *Impact:* An unbalance $>5\%$ generates negative sequence magnetic fluxes in connected 3-phase induction motors, causing disproportionate rotor heating and torque pulsations.

---

### 2.2 Power & Energy Derivations

1. **Apparent Power ($S$ in kVA):**
   $$S = \sqrt{3} \times V_{avg} \times I_{avg} \times 10^{-3}$$

2. **Active Power ($P$ in kW):**
   $$P = S \times PF$$

3. **Reactive Power ($Q$ in kVAR):**
   $$Q = \sqrt{S^2 - P^2} = P \times \tan(\arccos(PF))$$

4. **Power Factor ($PF$):**
   $$PF = \frac{P}{S} = \cos(\phi)$$
   *Commercial Thresholds:* Utilities levy reactive power penalties when $PF < 0.85$. Optimal operational target is $\ge 0.95$.

5. **Energy Consumption ($E$ in kWh per 30-minute interval $\Delta t = 0.5\text{ h}$):**
   $$E = P \times 0.5$$

---

### 2.3 Feeder Technical Conductor Losses ($I^2R$)

Conductor losses are calculated per phase to capture the exact thermal dissipation increase caused by phase unbalance:
$$P_{loss} = \left(I_r^2 + I_y^2 + I_b^2\right) \times R_{feeder} \times 10^{-3} \quad (\text{kW})$$

Because $\sum I_i^2 \ge 3 I_{avg}^2$ by Cauchy-Schwarz inequality, any phase imbalance strictly increases total $I^2R$ copper losses.

**Total Input Power & Loss Percentage:**
$$P_{input} = P + P_{loss}$$
$$\text{Feeder Loss \%} = \frac{P_{loss}}{P_{input}} \times 100$$

> **Empirical Validation:** Conductor loss scales strictly with the square of current ($P_{loss} \propto I^2$). Quadratic polynomial regression yields $R^2 \approx 0.99$.

---

### 2.4 Transformer Utilization & Losses

1. **Transformer Loading Percentage:**
   $$\text{Loading \%} = \frac{\sum_{f \in TR} S_f}{S_{rated\_TR}} \times 100$$

2. **Transformer Copper and Iron Loss Model:**
   $$P_{loss\_TR} = P_0 + \left(\frac{\text{Loading \%}}{100}\right)^2 \times P_k$$
   Where $P_0$ is the no-load core loss (iron loss) and $P_k$ is the full-load copper loss at rated temperature.

---

### 2.5 Thermal Heat Dissipation Model

Conductor and equipment operating temperature rises as a function of Joule dissipation and ambient weather:
$$T_{equip} = T_{amb} + \Delta T_{rated} \times \left(\frac{I_{avg}}{I_{rated}}\right)^{1.8} + \mathcal{N}(0, \sigma^2)$$

Where:
* $T_{amb}$ is ambient temperature ($22^\circ\text{C}$ to $44^\circ\text{C}$)
* $\Delta T_{rated} = 28^\circ\text{C}$ rated temperature rise above ambient
* The exponent $1.8$ models mixed convective and radiative cooling according to IEEE Std 738.

---

## 3. Data Quality Engine Methodology

The Data Quality Engine executes automated validation across six primary failure modes:

| Validation Rule | Physical Criterion | Root-Cause Context |
| :--- | :--- | :--- |
| **Duplicate Records** | Primary Key $(feeder, timestamp)$ | Network retries / SCADA polling duplicates |
| **Missing Telemetry** | Null check on $V, I, P, PF$ | GPRS packet loss / RTU power reset |
| **Voltage Boundaries** | $8,000 \le V_{avg} \le 14,500$ V | PT open-circuit / lightning surge glitch |
| **Current Boundaries** | $0 \le I_{avg} \le 2,500$ A | CT saturation / reverse polarity |
| **Power Factor Bounds** | $0.50 \le PF \le 1.00$ | Inverted wiring transducer polarity |
| **Physical Law Consistency** | $P \le S + \epsilon$ ($P \le \sqrt{3}VI$) | Uncalibrated active/apparent transducers |

A composite **Data Quality Score %** is computed as:
$$\text{DQ Score \%} = \left(\frac{\text{Total Records} - \text{Defective Rows}}{\text{Total Records}}\right) \times 100$$

---

## 4. Anomaly Detection & Machine Learning Methodology

### 4.1 Method 1: Statistical Engine (Z-Score & IQR)
Feeder-normalized Z-scores isolate anomalies while accounting for feeder-specific baselines:
$$Z_{x} = \frac{x - \mu_{feeder}}{\sigma_{feeder}}$$

An observation is flagged if $|Z_x| > 3.0$ on any key parameter ($I, V, P_{loss\%}, T_{equip}, I_{imb}$).
**Causal Attribution:** Each flagged point receives an explicit explanation string (e.g. *"Current Spike (Z=3.8); Thermal Hotspot (Z=3.1)"*).

### 4.2 Method 2: Multivariate Isolation Forest
Isolation Forest partitions observations in a multidimensional feature space ($V, I, PF, I_{imb}, T_{equip}, P_{loss\%}$):
* Isolates anomalous points near the root of shallow isolation trees ($n_{trees} = 100$, contamination $= 0.015$).
* Identifies complex multivariate correlations that single-parameter Z-scores miss (e.g., normal current combined with unusually high temperature and poor PF).

### 4.3 Consensus Framework
Observations are categorized into four confidence tiers:
1. **Dual-Method Confirmed:** Both Statistical and ML flag the point (High Confidence Operational Anomaly).
2. **Statistical Outlier Only:** Extreme single-variable excursion.
3. **ML Multivariate Outlier Only:** Subtle multi-variable correlation anomaly.
4. **Normal Operation.**

---

## 5. Transparent Fault Severity Scoring

Unlike black-box risk scores, the **Fault Severity Score ($0 - 100$)** is computed using an explainable, weighted formula:
$$\text{Severity} = 35 \times \left(\frac{I_{peak}}{2 \cdot I_{rated}}\right) + 25 \times \left(\frac{\Delta V_{sag\%}}{20}\right) + 20 \times \left(\frac{\text{Duration (min)}}{120}\right) + 20$$

* Overcurrent weight ($35\%$): Reflects magnetic forces ($F \propto I^2$) and thermal damage to line conductors.
* Voltage sag weight ($25\%$): Reflects power quality disruption to sensitive downstream loads.
* Duration weight ($20\%$): Reflects cumulative outage time.
* Base severity ($20\%$): Baseline acknowledgment of an uncommanded protective trip.
