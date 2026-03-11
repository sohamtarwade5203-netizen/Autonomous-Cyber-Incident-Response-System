"""
Behavior-Assisted Incident Correlation (UEBA-Inspired)

This module correlates multiple alerts into security incidents using
behavioral analytics. While inspired by UEBA principles, this is a
lightweight implementation focused on attack-type grouping and
multi-layer confidence scoring.

Real UEBA would include: user profiling, entity behavior baselines,
peer group analysis, and temporal pattern learning.
"""

import pandas as pd
import os

# ---------------------------------------------------
# STEP 1: Locate project root
# ---------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------
# STEP 2: Load anomaly detection output
# ---------------------------------------------------
data_path = os.path.join(BASE_DIR, "output", "alerts_with_anomalies.csv")
alerts = pd.read_csv(data_path)

print("Loaded alerts:", alerts.shape)
print(alerts.head())

# ---------------------------------------------------
# STEP 3: Decide which alerts to correlate (ML + fallback)
# ---------------------------------------------------
if alerts["is_anomaly"].sum() < 10:
    print("Low anomaly count detected. Applying severity-based fallback.")
    anomalies = alerts[alerts["severity"] == "HIGH"]
else:
    anomalies = alerts[alerts["is_anomaly"] == 1]

print("Anomalous alerts:", anomalies.shape)

# ---------------------------------------------------
# STEP 4: UEBA correlation (group into incidents)
# ---------------------------------------------------
incident_summary = (
    anomalies
    .groupby("attack_type")
    .agg(
        alert_count=("attack_type", "count"),
        anomaly_hits=("is_anomaly", "sum"),
        high_severity_hits=("severity", lambda x: (x == "HIGH").sum()),
        burst_hits=("burst_score", "sum")  # uses time-based burst detection
    )
    .reset_index()
)

# ---------------------------------------------------
# STEP 5: Behavioral risk scoring
# ---------------------------------------------------
def risk_score(count):
    if count > 1000:
        return "CRITICAL"
    elif count > 500:
        return "HIGH"
    elif count > 100:
        return "MEDIUM"
    else:
        return "LOW"

incident_summary["behavior_risk"] = incident_summary["alert_count"].apply(risk_score)

# ---------------------------------------------------
# STEP 6: MULTI-LAYER ANOMALY CONFIDENCE (⭐ FEATURE 1)
# ---------------------------------------------------
def compute_multi_layer_confidence(row):
    score = 0

    # Layer 1: Statistical anomaly (PyOD)
    if row["anomaly_hits"] > 0:
        score += 40

    # Layer 2: Behavioral anomaly (UEBA scale)
    if row["behavior_risk"] == "CRITICAL":
        score += 40
    elif row["behavior_risk"] == "HIGH":
        score += 25

    # Layer 3: Rule-based + temporal (severity + burst)
    if row["high_severity_hits"] > 0 or row["burst_hits"] > 0:
        score += 20

    return min(score, 100)

incident_summary["anomaly_confidence"] = incident_summary.apply(
    compute_multi_layer_confidence, axis=1
)

# ---------------------------------------------------
# STEP 7: CONFIDENCE BANDING (⭐ FEATURE 3)
# ---------------------------------------------------
def confidence_band(score):
    if score >= 80:
        return "HIGH"
    elif score >= 50:
        return "MEDIUM"
    else:
        return "LOW"

incident_summary["confidence_band"] = incident_summary["anomaly_confidence"].apply(confidence_band)

# ---------------------------------------------------
# STEP 8: Display correlated incidents
# ---------------------------------------------------
print("\nCorrelated Incidents (Final):")
print(incident_summary)

# ---------------------------------------------------
# STEP 9: Save output
# ---------------------------------------------------
output_dir = os.path.join(BASE_DIR, "output")
os.makedirs(output_dir, exist_ok=True)

incident_path = os.path.join(output_dir, "correlated_incidents.csv")
incident_summary.to_csv(incident_path, index=False)

print("\nUEBA incidents saved at:")
print(incident_path)
