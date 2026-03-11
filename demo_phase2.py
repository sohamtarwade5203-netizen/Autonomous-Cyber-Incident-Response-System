"""
Demo Script for Phase 2 Agentic AI Features

This script demonstrates the new agentic capabilities:
1. LangGraph agent processing
2. Autonomous decision-making
3. Real-time alert simulation

Run this after starting the API server to see Phase 2 in action.
"""

import requests
import json
import time
from datetime import datetime

API_BASE = "http://localhost:8000"

def print_header(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")

def check_api_health():
    """Check if API is running"""
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✓ API is running")
            print(f"  - Ollama Available: {data['ollama_available']}")
            print(f"  - Agent Ready: {data['agent_ready']}")
            print(f"  - Version: {data['version']}")
            return True
        return False
    except:
        print("✗ API is not running")
        print("\nPlease start the API server first:")
        print("  python -m uvicorn api.main:app --host 127.0.0.1 --port 8000")
        return False

def demo_alert_ingestion():
    """Demo: Ingest a single alert"""
    print_header("DEMO 1: Real-Time Alert Ingestion")
    
    alert = {
        "source": "SIEM",
        "attack_type": "DDOS",
        "severity": "HIGH",
        "timestamp": datetime.now().isoformat(),
        "source_ip": "192.168.1.100",
        "destination_ip": "10.0.0.50"
    }
    
    print("Sending alert to API...")
    print(json.dumps(alert, indent=2))
    
    response = requests.post(f"{API_BASE}/alerts/ingest", json=alert)
    
    if response.status_code == 200:
        data = response.json()
        print("\n✓ Alert accepted!")
        print(f"  Alert ID: {data['alert_id']}")
        print(f"  Status: {data['status']}")
        print("\n  Agent is processing in background...")
        return data['alert_id']
    else:
        print(f"\n✗ Failed: {response.status_code}")
        return None

def demo_batch_ingestion():
    """Demo: Ingest multiple alerts"""
    print_header("DEMO 2: Batch Alert Ingestion")
    
    batch = {
        "alerts": [
            {
                "source": "SIEM",
                "attack_type": "PORTSCAN",
                "severity": "MEDIUM"
            },
            {
                "source": "EDR",
                "attack_type": "DDOS",
                "severity": "HIGH"
            },
            {
                "source": "SIEM",
                "attack_type": "BENIGN",
                "severity": "LOW"
            }
        ]
    }
    
    print(f"Sending batch of {len(batch['alerts'])} alerts...")
    
    response = requests.post(f"{API_BASE}/alerts/batch", json=batch)
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✓ Batch accepted!")
        print(f"  Total alerts: {len(data['alert_ids'])}")
        print(f"  Status: {data['status']}")
    else:
        print(f"\n✗ Failed: {response.status_code}")

def demo_incident_list():
    """Demo: List all incidents"""
    print_header("DEMO 3: List All Incidents")
    
    response = requests.get(f"{API_BASE}/incidents")
    
    if response.status_code == 200:
        incidents = response.json()
        print(f"Total incidents: {len(incidents)}\n")
        
        for inc in incidents:
            print(f"Incident: {inc['incident_id']}")
            print(f"  Attack Type: {inc['attack_type']}")
            print(f"  Threat Level: {inc['threat_level']}")
            print(f"  Confidence: {inc['confidence_score']}%")
            print(f"  Status: {inc['status']}")
            print()
    else:
        print(f"✗ Failed: {response.status_code}")

def demo_incident_detail(incident_id):
    """Demo: Get incident details"""
    print_header("DEMO 4: Incident Details with Agent Reasoning")
    
    response = requests.get(f"{API_BASE}/incidents/{incident_id}")
    
    if response.status_code == 200:
        inc = response.json()
        print(f"Incident ID: {inc['incident_id']}")
        print(f"Attack Type: {inc['attack_type']}")
        print(f"Threat Level: {inc['threat_level']}")
        print(f"Confidence Score: {inc['confidence_score']}%")
        print(f"Auto-Execute: {inc['auto_execute']}")
        print(f"\nRecommended Actions:")
        for i, action in enumerate(inc['recommended_actions'], 1):
            print(f"  {i}. {action}")
        
        if inc.get('agent_reasoning'):
            print(f"\nAgent Reasoning Trace:")
            for step in inc['agent_reasoning']:
                print(f"  {step}")
    else:
        print(f"✗ Failed: {response.status_code}")

def demo_playbook(incident_id):
    """Demo: Get AI-generated playbook"""
    print_header("DEMO 5: AI-Generated Incident Response Playbook")
    
    response = requests.get(f"{API_BASE}/incidents/{incident_id}/playbook")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Incident: {data['incident_id']}")
        print(f"Threat Level: {data['threat_level']}")
        print(f"Confidence: {data['confidence_score']}%")
        print(f"Validated: {data['validated']}")
        print(f"\nPlaybook:\n")
        print(data['playbook'])
    else:
        print(f"✗ Failed: {response.status_code}")

def demo_decision_explanation(incident_id):
    """Demo: Get decision explanation"""
    print_header("DEMO 6: Autonomous Decision Explanation")
    
    response = requests.get(f"{API_BASE}/incidents/{incident_id}/decision")
    
    if response.status_code == 200:
        dec = response.json()
        print(f"Decision Type: {dec['decision_type']}")
        print(f"Confidence Score: {dec['confidence_score']}%")
        print(f"Threat Level: {dec['threat_level']}")
        print(f"\nRationale:")
        print(f"  {dec['rationale']}")
        print(f"\nActions:")
        for i, action in enumerate(dec['actions'], 1):
            print(f"  {i}. {action}")
        print(f"\nRequires Approval: {dec['requires_approval']}")
        print(f"Auto-Execute: {dec['auto_execute']}")
        print(f"\nNotification: {dec['notification']}")
    else:
        print(f"✗ Failed: {response.status_code}")

def demo_statistics():
    """Demo: Get system statistics"""
    print_header("DEMO 7: System Statistics")
    
    response = requests.get(f"{API_BASE}/stats")
    
    if response.status_code == 200:
        stats = response.json()
        print(f"Total Incidents: {stats['total_incidents']}")
        print(f"Completed: {stats['completed_incidents']}")
        print(f"\nDecision Engine Stats:")
        for key, value in stats['decision_stats'].items():
            print(f"  {key}: {value}")
    else:
        print(f"✗ Failed: {response.status_code}")

def main():
    """Run all demos"""
    print_header("Phase 2 Agentic AI Demo")
    print("This demo showcases the new agentic capabilities:")
    print("  • LangGraph agent with multi-step reasoning")
    print("  • Autonomous decision-making")
    print("  • Real-time alert processing")
    print("  • AI-generated playbooks")
    print("\nAll processing is FULLY OFFLINE using local Ollama")
    
    # Check API health
    if not check_api_health():
        return
    
    # Demo 1: Ingest single alert
    alert_id = demo_alert_ingestion()
    
    if alert_id:
        # Wait for processing
        print("\nWaiting 5 seconds for agent processing...")
        time.sleep(5)
        
        # Demo 2: Batch ingestion
        demo_batch_ingestion()
        
        # Wait for batch processing
        print("\nWaiting 5 seconds for batch processing...")
        time.sleep(5)
        
        # Demo 3: List incidents
        demo_incident_list()
        
        # Demo 4: Incident details
        demo_incident_detail(alert_id)
        
        # Demo 5: Playbook
        demo_playbook(alert_id)
        
        # Demo 6: Decision explanation
        demo_decision_explanation(alert_id)
        
        # Demo 7: Statistics
        demo_statistics()
    
    print_header("Demo Complete!")
    print("Explore more endpoints at: http://localhost:8000/docs")

if __name__ == "__main__":
    main()
