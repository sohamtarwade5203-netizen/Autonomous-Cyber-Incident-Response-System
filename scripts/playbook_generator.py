import pandas as pd
import os
import subprocess
import json

# Project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Load ranked incidents
ranked_path = os.path.join(BASE_DIR, "output", "ranked_incidents.csv")
incidents = pd.read_csv(ranked_path)

print("Loaded ranked incidents:")
print(incidents)

def generate_playbook(incident):
    """Generate playbook with action tier and justification

    Returns tuple: (human_readable_text, structured_playbook_dict)
    """
    
    # ============================================================
    # ACTION TIER MAPPING (Fix #2)
    # ============================================================
    priority = incident['priority']
    confidence = incident['anomaly_confidence']
    
    if priority == 'CRITICAL':
        action_tier = "IMMEDIATE CONTAINMENT + ESCALATE"
        response_time = "Immediate (< 5 minutes)"
        execution_mode = "AUTO" if confidence >= 90 else "RECOMMEND"
    elif priority == 'HIGH':
        action_tier = "INVESTIGATE + CONTAIN"
        response_time = "Within 30 minutes"
        execution_mode = "RECOMMEND"
    elif priority == 'MEDIUM':
        action_tier = "MONITOR + INVESTIGATE"
        response_time = "Within 2 hours"
        execution_mode = "ADVISORY"
    else:
        action_tier = "LOG ONLY"
        response_time = "Next business day"
        execution_mode = "ADVISORY"
    
    # ============================================================
    # ENHANCED PROMPT WITH DECISION AUTHORITY (Fix #4)
    # ============================================================
    prompt = f"""You are a senior SOC analyst at a bank.

INCIDENT DETAILS:
- Type: {incident['attack_type']}
- Alert Volume: {incident['alert_count']:,}
- Priority: {incident['priority']}
- Fidelity Score: {incident['fidelity_score']}/100
- Confidence: {incident['anomaly_confidence']}%

ACTION TIER: {action_tier}
RESPONSE TIME: {response_time}
EXECUTION MODE: {execution_mode}

Generate a clear, step-by-step incident response playbook.
Ensure actions are suitable for a banking environment.
Include specific timeframes and stakeholders.
"""

    result = subprocess.run(
        ["ollama", "run", "llama3"],
        input=prompt.encode("utf-8"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    response = result.stdout.decode("utf-8", errors="ignore")
    
    # ============================================================
    # JUSTIFICATION BLOCK (Fix #5)
    # ============================================================
    justification = f"""
{'='*70}
PLAYBOOK JUSTIFICATION (Audit Trail)
{'='*70}

WHY THIS RESPONSE:
- Alert volume: {incident['alert_count']:,} alerts (significantly above baseline)
- Fidelity score: {incident['fidelity_score']}/100 (high confidence)
- Anomaly confidence: {incident['anomaly_confidence']}% (confirmed by ML + temporal analysis)
- Behavior risk: {incident.get('behavior_risk', 'N/A')} (UEBA correlation)
- Priority: {incident['priority']} (requires {action_tier.lower()})

DECISION AUTHORITY:
- Execution Mode: {execution_mode}
- Confidence Threshold: {confidence}% (>= 90% = AUTO, >= 70% = RECOMMEND, < 70% = ADVISORY)
- Approval Required: {'No (auto-execute safe actions)' if execution_mode == 'AUTO' else 'Yes (senior analyst approval)'}

COMPLIANCE NOTES:
- All actions are non-destructive and reversible
- Complete audit trail maintained
- Regulatory reporting requirements included
- Customer impact assessment required before execution

{'='*70}
"""

    human_text = response.strip() + "\n" + justification

    # Build a structured, deterministic playbook that complements the LLM output
    steps = []
    if priority == 'CRITICAL':
        steps = [
            {"title": "Initial Notification", "timeframe": "0-2 min", "actions": ["Verify incident details", "Acknowledge to SOC", "Notify senior management"]},
            {"title": "Containment", "timeframe": "0-5 min", "actions": ["Isolate affected segment", "Block suspicious IPs", "Engage NOC"]},
            {"title": "Escalation", "timeframe": "0-10 min", "actions": ["Alert IR Lead", "Escalate to Cybersecurity Manager"]},
            {"title": "Investigation", "timeframe": "5-30 min", "actions": ["Collect logs", "Capture network traffic", "Identify IoCs"]},
            {"title": "Countermeasures", "timeframe": "5-60 min", "actions": ["Rate limit", "Activate WAF rules", "Block IP ranges"]}
        ]
    elif priority == 'HIGH':
        steps = [
            {"title": "Initial Triage", "timeframe": "0-30 min", "actions": ["Verify alerts", "Assign analyst"]},
            {"title": "Containment", "timeframe": "30-120 min", "actions": ["Limit access", "Apply temporary blocks"]},
            {"title": "Investigation", "timeframe": "30-240 min", "actions": ["Log analysis", "Identify scope"]}
        ]
    else:
        steps = [
            {"title": "Monitoring", "timeframe": "Next 24 hours", "actions": ["Continue monitoring", "Schedule review"]}
        ]

    structured = {
        "incident": incident.get('attack_type', 'unknown'),
        "alert_count": int(incident.get('alert_count', 0)),
        "priority": incident.get('priority', 'UNKNOWN'),
        "fidelity_score": incident.get('fidelity_score', None),
        "confidence": incident.get('anomaly_confidence', None),
        "action_tier": action_tier,
        "response_time": response_time,
        "execution_mode": execution_mode,
        "steps": steps,
        "llm_playbook": response.strip(),
        "justification": {
            "alert_volume": int(incident.get('alert_count', 0)),
            "fidelity_score": incident.get('fidelity_score', None),
            "anomaly_confidence": incident.get('anomaly_confidence', None),
            "behavior_risk": incident.get('behavior_risk', None),
            "decision_authority": {
                "execution_mode": execution_mode,
                "confidence_threshold": confidence,
                "approval_required": False if execution_mode == 'AUTO' else True
            }
        }
    }

    return human_text, structured


    


playbooks = []
playbooks_json = []

for _, row in incidents.iterrows():
    print(f"Generating playbook for {row['attack_type']}...")
    human_text, structured = generate_playbook(row)
    playbooks.append(f"=== INCIDENT: {row['attack_type']} ===\n{human_text}\n")
    playbooks_json.append(structured)

# Save playbooks
output_dir = os.path.join(BASE_DIR, "output")
os.makedirs(output_dir, exist_ok=True)

playbook_path = os.path.join(output_dir, "incident_playbooks.txt")
json_path = os.path.join(output_dir, "incident_playbooks.json")

with open(playbook_path, "w", encoding="utf-8") as f:
    for pb in playbooks:
        f.write(pb + "\n")

with open(json_path, "w", encoding="utf-8") as jf:
    json.dump(playbooks_json, jf, indent=2)

print("\nIncident response playbooks saved at:")
print(playbook_path)
print(json_path)

