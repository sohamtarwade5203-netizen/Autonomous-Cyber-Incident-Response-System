import pandas as pd
import os

# Project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Load UEBA-correlated incidents
incident_path = os.path.join(BASE_DIR, "output", "correlated_incidents.csv")
incidents = pd.read_csv(incident_path)

print("Loaded incidents:")
print(incidents)


# Map behavioral risk to numeric weight
risk_weight = {
    "CRITICAL": 40,
    "HIGH": 30,
    "MEDIUM": 20,
    "LOW": 10
}

# Compute fidelity score
def compute_fidelity(row):
    base = min(row["alert_count"] / 50, 40)  # alert volume impact
    behavior = risk_weight.get(row["behavior_risk"], 10)
    fidelity = base + behavior
    return min(int(fidelity), 100)

if incidents.empty:
    raise ValueError("No incidents found for fidelity ranking. Check UEBA correlation output.")

incidents["fidelity_score"] = incidents.apply(lambda row: compute_fidelity(row), axis=1)


# Assign priority based on fidelity
def priority(score):
    if score >= 80:
        return "CRITICAL"
    elif score >= 60:
        return "HIGH"
    elif score >= 40:
        return "MEDIUM"
    else:
        return "LOW"

incidents["priority"] = incidents["fidelity_score"].apply(priority)

print("\nFidelity-ranked incidents:")
print(incidents)

# Save ranked incidents
output_dir = os.path.join(BASE_DIR, "output")
os.makedirs(output_dir, exist_ok=True)

ranked_path = os.path.join(output_dir, "ranked_incidents.csv")
incidents.to_csv(ranked_path, index=False)

print("\nRanked incidents saved at:")
print(ranked_path)

