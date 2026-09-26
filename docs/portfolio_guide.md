# Portfolio & Interview Preparation Guide
## Power Distribution Loss & Fault Analytics System
### Grounded in Real Industrial Telemetry: Reliance Industries Limited (RIL) Substation 600-30

This guide prepares an **Electrical Engineering student transitioning into Data Analyst / Analytics Engineer roles** to showcase this project on resumes, LinkedIn, and during technical interviews.

---

## 1. Resume Bullet Points (Ready for Immediate Insertion)

Choose and adapt these 3 high-impact, quantified bullet points for your resume:

* **Engineered end-to-end electrical distribution analytics system** analyzing 104,000+ SCADA/AMI records across 2 substations and 12 feeders, benchmarked against **60 authentic field circuits from Reliance Industries Limited (RIL) Substation 600-30 (6.6 kV) and 415 V satellite MCCs (600-31/32)**.
* **Architected relational Star Schema & 25+ SQL analytical queries** (CTEs, Window Functions, DENSE_RANK, LAG) and built a Python Data Quality Engine that sanitized 1,000+ sensor dropouts, polarity reversals, and boundary violations to deliver a 98.96% clean fact table.
* **Proved conductor dissipation scales quadratically ($P_{loss} \propto I^2$, $R^2 \approx 0.99$)** and benchmarked dual-engine anomaly detection (Z-Score causal attribution vs. multivariate Isolation Forest), deploying an interactive Streamlit/Power BI dashboard with rule-based maintenance recommendations that identified up to 9.6% technical losses on 415 V product loading pumps.

---

## 2. LinkedIn Project Post

```markdown
🚀 Excited to share my latest end-to-end data analytics project: 
Power Distribution Loss & Fault Analytics System ⚡📊 (Featuring RIL Refinery Field Case Study)

Bridging Electrical Power Systems engineering with modern Data Analytics, I built a complete SCADA/AMI telemetry pipeline that models technical conductor losses, power quality non-compliance, and protection relay operations across 104,000+ time-series measurements.

Key Highlights of the Project:
🔹 Real Industrial Benchmark: Ingested and analyzed authentic field telemetry from my internship at Reliance Industries Limited (RIL) Substation 600-30 (6.6 kV Medium Voltage Switchboard: Bus A & B) and satellite 415 V Motor Control Centers (Substations 600-31 & 600-32).
🔹 Grounded Electrical Physics: Derived active/reactive powers, IEEE Std 141 phase current imbalances, and empirically verified Joule's First Law (Loss ∝ I², R² ≈ 0.99) across 150/240 mm² XLPE cables up to 3.6 km in length.
🔹 Data Quality Engine: Automated validation pipeline that audited telemetry dropouts, CT/PT saturation glitches, and transducer wiring polarity inversions, delivering a 98.96% clean fact table.
🔹 Relational Star Schema (SQL): Structured 6 dimension and 3 fact tables; authored 25+ production-grade analytical SQL queries utilizing DENSE_RANK, LAG/LEAD, rolling window frames, and composite risk scoring.
🔹 Dual-Engine Anomaly Detection: Benchmarked statistical Z-scores (with causal parameter attribution) against multivariate Isolation Forest, categorizing consensus confidence tiers.
🔹 Interactive Operations Dashboard: Deployed a Power BI-style dark operations center in Streamlit & Plotly with rule-based explainable maintenance recommendations.

Check out the full repository and architecture here: [GitHub Link]

#DataAnalytics #ElectricalEngineering #RelianceIndustries #RIL #PowerSystems #SQL #Python #Streamlit #PowerBI #DataScience #DataQuality
```

---

## 3. 30-Second Elevator Pitch

> *"I built a portfolio-grade Power Distribution Loss & Fault Analytics System that bridges heavy electrical power systems engineering with modern data analytics. Based on operational architectures and real field data I collected during my internship at Reliance Industries Limited (RIL) Substation 600-30, the system ingests over 104,000 SCADA measurements. I developed an automated Data Quality Engine to sanitize transducer dropouts, structured an enterprise relational Star Schema with 25 advanced SQL queries, benchmarked statistical Z-scores against multivariate Isolation Forest, and deployed an interactive Streamlit operations dashboard that reveals why 415V product loading pumps suffer up to 9.6% conductor loss compared to 6.6 kV lines."*

---

## 4. 2-Minute In-Depth Interview Explanation

> *"In continuous industrial processing facilities like refineries and chemical plants, distribution electrical networks operate under severe reliability and thermal constraints. Unmonitored cable I²R dissipation and chronic power quality issues—such as phase current imbalance and low power factor—degrade equipment and cause unscheduled outages.
> 
> As an Electrical Engineer transitioning into Data Analytics, I wanted to anchor my work in authentic industrial reality. During my internship at Reliance Industries Limited (RIL), I collected field data from Substation 600-30, a 6.6 kV medium-voltage switchboard with dual busbars (Bus A & Bus B), as well as downstream 415 V Motor Control Centers at Substations 600-31 and 600-32. This data captured exact 150 and 240 mm² XLPE cable run lengths, phase currents, voltages, and motor loads for critical services like Naphtha and LPG rail loading pumps, RTF vapor recovery motors, and 3.6 km staff township lines.
> 
> Using these industrial parameters, I built an end-to-end analytics platform. First, I created a Python Data Quality Engine. Real field telemetry suffers from PT/CT open circuits, packet loss, and inverted transducer polarities. My engine audited over 104,000 records, caught over 1,000 defects, re-derived physical power consistency, and certified a 98.96% clean fact dataset.
> 
> Second, I designed a relational Star Schema in SQL with 6 dimensions and 3 fact tables, authoring 25 production-grade SQL queries. Using window functions like DENSE_RANK, LAG, and rolling moving averages, I built a composite risk matrix that ranks feeders based on conductor losses, phase asymmetry, and thermal stress.
> 
> Third, for loss analytics, I empirically verified that conductor losses scale with the square of current (R² ≈ 0.99). In our RIL field study, we found that 415 V product loading pumps running 195 to 218 Amps over 500+ meters experienced technical loss rates between 8% and 9.6%—illustrating the core electrical principle of why voltage must be stepped up to 6.6 kV for longer industrial runs.
> 
> Finally, I deployed an interactive Streamlit operations dashboard featuring Power BI dark corporate styling, dual-engine anomaly detection (Z-scores vs Isolation Forest), and rule-based maintenance recommendations. This project proves that I can combine deep electrical domain knowledge with modern data engineering, SQL, and machine learning to deliver actionable business value."*

---

## 5. Top 10 Technical Interview Questions & Exemplary Answers

### Q1: Why did you compute feeder losses using $(I_r^2 + I_y^2 + I_b^2) \times R$ instead of $3 \times I_{avg}^2 \times R$?
**Answer:** In an ideal, perfectly balanced three-phase system, both formulas yield the exact same value. However, real distribution feeders exhibit phase current unbalance due to single-phase service drops or cyclic arc furnace operations. Mathematically, by the Cauchy-Schwarz inequality, $\sum I_i^2 \ge 3 I_{avg}^2$. Evaluating each phase individually accounts for the additional Joule dissipation in the heavily loaded phase and circulating neutral currents, which is a critical domain detail often overlooked in generic data projects.

---

### Q2: What was the purpose of building a separate Data Quality Engine rather than just calling `df.dropna()`?
**Answer:** In industrial SCADA environments, data corruption is rarely just a null value. It includes impossible physical states: potential transformer open circuits causing $0\text{ V}$ readings while current is flowing, current transformer saturation, reversed transducer wiring causing negative power factors, and math violations where active power $P > S$. A simple `dropna()` misses these insidious errors. My Data Quality Engine audited primary key duplicates, boundary violations ($V \in [8\text{kV}, 14.5\text{kV}]$, $PF \in [0.5, 1.0]$), and physics consistency ($P \le \sqrt{3}VI$), reporting a transparent audit scorecard before certifying data for downstream SQL ingestion.

---

### Q3: How did you design your database schema, and why did you choose a Star Schema?
**Answer:** I structured the database as a dimensional Star Schema consisting of 6 dimension tables (`dim_substation`, `dim_transformer`, `dim_feeder`, `dim_load`, `dim_fault`, `dim_calendar`) and 3 fact tables (`fact_electrical_measurements`, `fact_fault_events`, `fact_maintenance`). A Star Schema was chosen because it decouples slowly changing asset metadata (e.g. conductor resistance, transformer impedance) from high-velocity telemetry facts. It optimizes analytical SQL queries, avoids redundant storage across 104,000+ rows, and enables seamless one-click import into business intelligence tools like Microsoft Power BI.

---

### Q4: Explain the difference between your statistical anomaly detection and your machine learning Isolation Forest.
**Answer:** The statistical engine uses feeder-normalized Z-scores ($|Z| > 3.0$) and IQR thresholds on individual parameters. Its key advantage is **explainability**: when an observation is flagged, the engine explicitly generates a causal attribution string (e.g., *"Current Spike Z=3.4; Thermal Hotspot Z=3.1"*). However, it struggles with subtle multi-parameter interactions. The multivariate **Isolation Forest** evaluates all dimensions simultaneously ($V, I, PF, I_{imb}, T, P_{loss}$) and flags observations that sit in sparse multi-dimensional regions—such as a normal current paired with an abnormally high temperature rise and low PF. I built a consensus tiering system to isolate high-confidence events confirmed by both engines.

---

### Q5: In your predictive fault modeling, why did you use a temporal train/test split instead of standard K-fold cross-validation?
**Answer:** Standard randomized train/test splits or K-fold cross-validation cause **lookahead data leakage** in time-series telemetry. If the model trains on future data points to predict a past fault, evaluation metrics become artificially inflated and unrepresentative of real-world deployment. I enforced a strict chronological split: the first 75% of the timeline served as the training corpus, and the subsequent 25% served as the unseen forward evaluation set.

---

### Q6: Why was the F1-score for forward fault prediction relatively low, and why didn't you try to artificially inflate it?
**Answer:** Electrical distribution faults are rare, transient events—representing less than 0.2% of total operational intervals. In genuine utility operations, predicting an exact 2-hour fault window from SCADA telemetry alone has inherently high false-positive rates because many physical faults (such as tree branch contacts or lightning surges) are external and stochastic. Following professional analytical ethics, rather than artificially oversampling synthetic data to report a misleading 99% accuracy, I documented the true precision/recall trade-off and emphasized that continuous condition monitoring and threshold anomaly detection offer far more operational value to field crews than noisy binary classification.

---

### Q7: What are the economic and engineering consequences of a feeder operating with a power factor below 0.85?
**Answer:** When power factor drops below 0.85, two major issues arise:
1. **Engineering:** The ratio of reactive magnetizing current to active current increases ($S = P / PF$). This inflated apparent current forces higher $I^2R$ copper dissipation in cables and consumes transformer MVA capacity without delivering productive work.
2. **Commercial:** Electrical utility distribution tariffs enforce strict reactive energy surcharges ($kVARh$ penalty tariffs) for industrial consumers operating below 0.85. In my dashboard, I tracked cumulative penalty hours by feeder to quantify the return on investment (ROI) for installing automatic switched capacitor banks (APFC).

---

### Q8: How did you prove that conductor losses scale with the square of current?
**Answer:** I extracted telemetry for specific feeders, binned current into discrete 25 Ampere intervals, and fitted a second-order polynomial regression model ($P_{loss} = a \cdot I^2 + b$). The regression yielded an $R^2$ coefficient of determination of over $0.99$, empirically validating Joule's First Law. This proves that high-demand peak intervals are disproportionately responsible for network losses: doubling the current quadruples line losses.

---

### Q9: Can you explain one of the complex SQL queries you wrote using window functions?
**Answer:** In Query 2, I implemented `DENSE_RANK() OVER (PARTITION BY load_category ORDER BY avg_loss_pct DESC)` and `DENSE_RANK() OVER (ORDER BY avg_loss_pct DESC)`. This query partitioned feeders into their industrial, commercial, and residential categories and computed both within-category efficiency ranks and global grid-wide loss ranks. In Query 5, I used the `LAG()` window function over calendar months to compute month-over-month percentage growth in delivered energy and technical conductor dissipation, enabling utilities to detect seasonal thermal degradation.

---

### Q10: How does your recommendation engine work?
**Answer:** The recommendation engine is an explainable, rule-based expert system. Rather than recommending expensive capital equipment automatically, it evaluates specific telemetry thresholds:
* If average $PF < 0.82$, it recommends targeted local capacitor banks (APFC) with expected payback periods.
* If average phase current unbalance exceeds $6.5\%$, it recommends low-cost single-phase service drop rebalancing.
* If a transformer exceeds $95\%$ peak loading, it triggers a bus-tie reconfiguration alert to transfer load to an adjacent under-utilized unit.
Every recommendation outputs an operational trigger, an actionable field intervention, expected electrical/financial benefits, and an estimated payback horizon.
