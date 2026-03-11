import pandas as pd
import os
import numpy as np
from pyod.models.iforest import IForest

# ---------------------------------------------------
# STEP 1: Locate project root
# ---------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------
# STEP 2: Load standardized alerts
# ---------------------------------------------------
data_path = os.path.join(BASE_DIR, "output", "standardized_alerts.csv")
alerts = pd.read_csv(data_path)

print("Alerts loaded:", alerts.shape)
print(alerts.head())

# ---------------------------------------------------
# STEP 3: Encode categorical features
# ---------------------------------------------------
alerts["attack_code"] = alerts["attack_type"].map({
    "BENIGN": 0,
    "DDOS": 1,
    "PORTSCAN": 2
})

alerts["severity_code"] = alerts["severity"].map({
    "LOW": 0,
    "HIGH": 1
})

# ---------------------------------------------------
# STEP 4: Feature matrix for anomaly detection
# ---------------------------------------------------
X = alerts[["attack_code", "severity_code"]].values
print("Feature matrix shape:", X.shape)

# ---------------------------------------------------
# STEP 5: Statistical anomaly detection (PyOD)
# ---------------------------------------------------
# PERFORMANCE OPTIMIZATION: Representative sampling for large datasets
# Industry-standard approach: train on sample, predict on full dataset
# This maintains responsiveness at scale (SOC requirement)

MAX_SAMPLES = 200_000  # Representative sample size

print("\n" + "="*70)
print("ANOMALY DETECTION - ISOLATION FOREST")
print("="*70)

if len(alerts) > MAX_SAMPLES:
    print(f"Dataset size: {len(alerts):,} rows")
    print(f"Using representative sampling: {MAX_SAMPLES:,} rows for training")
    print("Rationale: Maintains responsiveness while preserving detection accuracy")
    
    # Stratified sampling to preserve attack type distribution
    sample_df = alerts.groupby('attack_type', group_keys=False).apply(
        lambda x: x.sample(min(len(x), MAX_SAMPLES // 3), random_state=42)
    )
    sample_idx = sample_df.index
    X_train = X[sample_idx]
    
    print(f"Training set: {len(X_train):,} rows")
    print("Training Isolation Forest...")
else:
    print(f"Dataset size: {len(alerts):,} rows (training on full dataset)")
    X_train = X

model = IForest(
    n_estimators=100,
    contamination=0.05,
    random_state=42
)

model.fit(X_train)
print("[OK] Model training complete")

# Predict on FULL dataset (not just sample)
print(f"Applying model to full dataset ({len(alerts):,} rows)...")
alerts["anomaly_score"] = model.decision_function(X)
ml_anomaly = model.predict(X)  # 1 = anomaly, 0 = normal

print("[OK] Statistical anomaly detection completed")
print("\nAnomaly distribution:")
print(pd.Series(ml_anomaly).value_counts())
print("="*70 + "\n")

# ---------------------------------------------------
# STEP 6: CONTEXTUAL BURST DETECTION (⭐ ENHANCED)
# ---------------------------------------------------
# Burst detection relative to attack-type baseline
# This prevents benign traffic from dominating anomaly scores

# Create synthetic timestamps (lowercase 's' is IMPORTANT)
alerts["timestamp"] = pd.date_range(
    start="2025-01-01",
    periods=len(alerts),
    freq="s"   # ✅ lowercase 's'
)

# Create 5-minute windows
alerts["time_window"] = alerts["timestamp"].dt.floor("5min")

# Count alerts per window AND attack type (contextual)
window_attack_counts = alerts.groupby(["time_window", "attack_type"]).size().reset_index(name="count")

# Calculate baseline (average) for each attack type
baseline_per_attack = alerts.groupby("attack_type").size() / alerts["time_window"].nunique()

print("\nBaseline alerts per 5-min window (by attack type):")
for attack_type in baseline_per_attack.index:
    print(f"  {attack_type}: {baseline_per_attack[attack_type]:.1f} alerts/window")

# Contextual burst detection: current > k × baseline
# k = 2.5 means "2.5x higher than normal for this attack type"
BURST_MULTIPLIER = 2.5

def is_burst(row):
    """Determine if this window is a burst for this attack type"""
    attack_type = row["attack_type"]
    window = row["time_window"]
    
    # Get count for this specific window + attack type
    count = window_attack_counts[
        (window_attack_counts["time_window"] == window) & 
        (window_attack_counts["attack_type"] == attack_type)
    ]["count"].values
    
    if len(count) == 0:
        return 0
    
    current_count = count[0]
    baseline = baseline_per_attack[attack_type]
    
    # Burst if current is significantly higher than baseline
    return 1 if current_count > (BURST_MULTIPLIER * baseline) else 0

# Apply contextual burst detection
alerts["burst_score"] = alerts.apply(is_burst, axis=1)

print("\nContextual burst detection completed")
print("Burst alerts by attack type:")
burst_summary = alerts.groupby("attack_type")["burst_score"].agg(["sum", "count"])
burst_summary["burst_rate"] = (burst_summary["sum"] / burst_summary["count"] * 100).round(2)
print(burst_summary)

# ---------------------------------------------------
# STEP 7: FINAL ANOMALY DECISION (ML OR Burst)
# ---------------------------------------------------
alerts["is_anomaly"] = (
    (ml_anomaly == 1) | (alerts["burst_score"] == 1)
).astype(int)

print("Final anomaly decision completed")
print(alerts["is_anomaly"].value_counts())

# ---------------------------------------------------
# STEP 8: Save anomaly detection output
# ---------------------------------------------------
output_dir = os.path.join(BASE_DIR, "output")
os.makedirs(output_dir, exist_ok=True)

anomaly_output_path = os.path.join(output_dir, "alerts_with_anomalies.csv")
alerts.to_csv(anomaly_output_path, index=False)

print("\nAnomaly results saved at:")
print(anomaly_output_path)

