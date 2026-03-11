"""
Custom Tools for Incident Response Agent

All tools are LOCAL Python functions - no external API calls.
These tools are used by the LangGraph agent to perform specific tasks.
"""

from typing import Dict, List
import json


def analyze_incident_severity(incident: Dict) -> str:
    """
    Analyze incident severity based on fidelity score and confidence.
    
    Args:
        incident: Incident data with fidelity_score, confidence_band, etc.
    
    Returns:
        Detailed severity analysis as string
    """
    fidelity = incident.get('fidelity_score', 0)
    confidence = incident.get('anomaly_confidence', 0)
    priority = incident.get('priority', 'UNKNOWN')
    attack_type = incident.get('attack_type', 'UNKNOWN')
    alert_count = incident.get('alert_count', 0)
    
    analysis = f"""
INCIDENT SEVERITY ANALYSIS
==========================
Attack Type: {attack_type}
Alert Volume: {alert_count:,}
Fidelity Score: {fidelity}/100
Anomaly Confidence: {confidence}/100
Priority Level: {priority}

ASSESSMENT:
"""
    
    if fidelity >= 80 and confidence >= 80:
        analysis += "- HIGH SEVERITY: Immediate action required\n"
        analysis += "- Strong indicators of genuine security incident\n"
        analysis += "- Recommend automated containment measures\n"
    elif fidelity >= 60 or confidence >= 60:
        analysis += "- MEDIUM SEVERITY: Investigation required\n"
        analysis += "- Moderate confidence in threat assessment\n"
        analysis += "- Recommend manual review before action\n"
    else:
        analysis += "- LOW SEVERITY: Monitor and log\n"
        analysis += "- May be false positive or benign activity\n"
        analysis += "- Advisory-only response recommended\n"
    
    return analysis


def determine_threat_level(incident: Dict) -> str:
    """
    Determine threat level based on incident characteristics.
    
    Returns: CRITICAL, HIGH, MEDIUM, or LOW
    """
    fidelity = incident.get('fidelity_score', 0)
    confidence = incident.get('anomaly_confidence', 0)
    priority = incident.get('priority', 'LOW')
    
    # Multi-factor threat assessment
    if priority == 'CRITICAL' and fidelity >= 80:
        return 'CRITICAL'
    elif fidelity >= 70 or confidence >= 70:
        return 'HIGH'
    elif fidelity >= 50 or confidence >= 50:
        return 'MEDIUM'
    else:
        return 'LOW'


def calculate_confidence_score(incident: Dict) -> int:
    """
    Calculate overall confidence score for autonomous decision-making.
    
    Returns: Integer 0-100
    """
    fidelity = incident.get('fidelity_score', 0)
    anomaly_conf = incident.get('anomaly_confidence', 0)
    
    # Weighted average
    confidence = int((fidelity * 0.6) + (anomaly_conf * 0.4))
    
    return min(max(confidence, 0), 100)  # Clamp to 0-100


def generate_recommended_actions(incident: Dict, threat_level: str) -> List[str]:
    """
    Generate recommended actions based on threat level and incident type.
    
    All actions are LOCAL recommendations - no actual execution here.
    """
    attack_type = incident.get('attack_type', 'UNKNOWN')
    actions = []
    
    # Common actions for all incidents
    actions.append("Log incident details to SIEM")
    actions.append("Notify SOC team lead")
    
    # Attack-specific actions
    if attack_type == 'DDOS':
        actions.extend([
            "Activate DDoS mitigation measures",
            "Engage network team for traffic analysis",
            "Enable rate limiting on affected endpoints",
            "Monitor network bandwidth utilization",
            "Prepare communication for stakeholders"
        ])
    elif attack_type == 'PORTSCAN':
        actions.extend([
            "Isolate affected network segment",
            "Block source IP addresses at firewall",
            "Review firewall rules and ACLs",
            "Conduct vulnerability scan on targeted systems",
            "Check for signs of lateral movement"
        ])
    elif attack_type == 'BENIGN':
        actions.extend([
            "Verify alert is false positive",
            "Tune detection rules to reduce noise",
            "Document for future reference"
        ])
    
    # Threat-level specific actions
    if threat_level in ['CRITICAL', 'HIGH']:
        actions.insert(0, "IMMEDIATE: Escalate to senior SOC analyst")
        actions.append("Initiate incident response procedure")
        actions.append("Preserve evidence for forensic analysis")
    
    return actions


def validate_playbook_quality(playbook: str) -> Dict:
    """
    Validate generated playbook meets quality standards.
    
    Returns: Dict with validation results
    """
    validation = {
        'valid': True,
        'issues': [],
        'score': 100
    }
    
    # Check minimum length
    if len(playbook) < 200:
        validation['valid'] = False
        validation['issues'].append("Playbook too short - lacks detail")
        validation['score'] -= 30
    
    # Check for key sections
    required_sections = ['Step', 'Initial', 'Containment', 'Investigation']
    missing_sections = [s for s in required_sections if s.lower() not in playbook.lower()]
    
    if missing_sections:
        validation['issues'].append(f"Missing sections: {', '.join(missing_sections)}")
        validation['score'] -= 20 * len(missing_sections)
    
    # Check for banking-specific context
    banking_terms = ['bank', 'financial', 'customer', 'transaction', 'stakeholder']
    has_banking_context = any(term in playbook.lower() for term in banking_terms)
    
    if not has_banking_context:
        validation['issues'].append("Lacks banking-specific context")
        validation['score'] -= 15
    
    validation['score'] = max(validation['score'], 0)
    validation['valid'] = validation['score'] >= 60
    
    return validation


def format_agent_response(state: Dict) -> Dict:
    """
    Format final agent response for output.
    
    Returns: Structured response dictionary
    """
    return {
        'incident_id': state.get('incident_data', {}).get('attack_type', 'UNKNOWN'),
        'threat_level': state.get('threat_level', 'UNKNOWN'),
        'confidence_score': state.get('confidence_score', 0),
        'auto_execute': state.get('auto_execute', False),
        'recommended_actions': state.get('recommended_actions', []),
        'playbook': state.get('playbook', ''),
        'playbook_validated': state.get('playbook_validated', False),
        'agent_reasoning': state.get('agent_reasoning', []),
        'timestamp': state.get('timestamp', '')
    }


# Tool registry for LangGraph
AGENT_TOOLS = {
    'analyze_severity': analyze_incident_severity,
    'determine_threat': determine_threat_level,
    'calculate_confidence': calculate_confidence_score,
    'recommend_actions': generate_recommended_actions,
    'validate_playbook': validate_playbook_quality,
    'format_response': format_agent_response
}
