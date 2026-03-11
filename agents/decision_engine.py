"""
Autonomous Decision Engine

Implements confidence-based decision-making for incident response.
All decisions are made locally using Python logic - no external calls.
"""

from typing import Dict, List, Tuple
from datetime import datetime


class DecisionEngine:
    """
    Autonomous decision engine for incident response.
    
    Makes decisions based on confidence scores and threat levels.
    Implements human-in-the-loop controls for uncertain cases.
    """
    
    # Decision thresholds
    AUTO_EXECUTE_THRESHOLD = 90  # Auto-execute actions if confidence >= 90%
    RECOMMEND_THRESHOLD = 70     # Recommend actions if confidence >= 70%
    ADVISORY_THRESHOLD = 50      # Advisory only if confidence < 50%
    
    def __init__(self):
        self.decision_history = []
        self.auto_executed_count = 0
        self.recommended_count = 0
        self.advisory_count = 0
    
    def make_decision(self, incident: Dict, confidence_score: int, threat_level: str) -> Dict:
        """
        Make autonomous decision based on confidence and threat level.
        
        Args:
            incident: Incident data
            confidence_score: Confidence score 0-100
            threat_level: CRITICAL, HIGH, MEDIUM, LOW
        
        Returns:
            Decision dictionary with action plan
        """
        decision = {
            'incident_id': incident.get('attack_type', 'UNKNOWN'),
            'confidence_score': confidence_score,
            'threat_level': threat_level,
            'timestamp': datetime.now().isoformat(),
            'decision_type': None,
            'actions': [],
            'rationale': '',
            'requires_approval': False,
            'auto_execute': False
        }
        
        # Decision logic based on confidence
        if confidence_score >= self.AUTO_EXECUTE_THRESHOLD:
            decision.update(self._auto_execute_decision(incident, threat_level))
            self.auto_executed_count += 1
        elif confidence_score >= self.RECOMMEND_THRESHOLD:
            decision.update(self._recommend_decision(incident, threat_level))
            self.recommended_count += 1
        else:
            decision.update(self._advisory_decision(incident, threat_level))
            self.advisory_count += 1
        
        # Log decision
        self.decision_history.append(decision)
        
        return decision
    
    def _auto_execute_decision(self, incident: Dict, threat_level: str) -> Dict:
        """
        High-confidence decision: Auto-execute safe actions.
        """
        attack_type = incident.get('attack_type', 'UNKNOWN')
        
        safe_actions = self._get_safe_actions(attack_type, threat_level)
        
        return {
            'decision_type': 'AUTO_EXECUTE',
            'actions': safe_actions,
            'rationale': (
                f"High confidence ({self.AUTO_EXECUTE_THRESHOLD}%+) allows automated execution. "
                f"Threat level: {threat_level}. Actions are pre-approved safe operations."
            ),
            'requires_approval': False,
            'auto_execute': True,
            'notification': 'SOC team will be notified of automated actions taken'
        }
    
    def _recommend_decision(self, incident: Dict, threat_level: str) -> Dict:
        """
        Medium-confidence decision: Recommend actions, require approval.
        """
        attack_type = incident.get('attack_type', 'UNKNOWN')
        
        recommended_actions = self._get_recommended_actions(attack_type, threat_level)
        
        return {
            'decision_type': 'RECOMMEND',
            'actions': recommended_actions,
            'rationale': (
                f"Medium confidence ({self.RECOMMEND_THRESHOLD}-{self.AUTO_EXECUTE_THRESHOLD}%) "
                f"requires human approval. Threat level: {threat_level}. "
                f"Review recommended actions and approve for execution."
            ),
            'requires_approval': True,
            'auto_execute': False,
            'notification': 'Senior SOC analyst approval required before execution'
        }
    
    def _advisory_decision(self, incident: Dict, threat_level: str) -> Dict:
        """
        Low-confidence decision: Advisory only, no automated actions.
        """
        return {
            'decision_type': 'ADVISORY',
            'actions': [
                'Log incident for manual review',
                'Monitor for additional indicators',
                'Correlate with other security events'
            ],
            'rationale': (
                f"Low confidence (<{self.RECOMMEND_THRESHOLD}%) indicates potential false positive. "
                f"Advisory-only response recommended. Manual investigation suggested."
            ),
            'requires_approval': False,
            'auto_execute': False,
            'notification': 'Incident logged for analyst review during next shift'
        }
    
    def _get_safe_actions(self, attack_type: str, threat_level: str) -> List[str]:
        """
        Get pre-approved safe actions that can be auto-executed.
        
        Safe actions are non-destructive and reversible.
        """
        safe_actions = [
            'Log incident to SIEM with HIGH priority',
            'Send automated notification to SOC team',
            'Create incident ticket in ITSM system',
            'Capture network traffic samples for analysis'
        ]
        
        if attack_type == 'DDOS':
            safe_actions.extend([
                'Enable DDoS mitigation at CDN layer',
                'Activate rate limiting on affected endpoints',
                'Notify network operations team'
            ])
        elif attack_type == 'PORTSCAN':
            safe_actions.extend([
                'Add source IPs to monitoring watchlist',
                'Increase logging verbosity on targeted systems',
                'Alert firewall team for review'
            ])
        
        if threat_level == 'CRITICAL':
            safe_actions.insert(0, 'IMMEDIATE: Escalate to senior SOC analyst')
        
        return safe_actions
    
    def _get_recommended_actions(self, attack_type: str, threat_level: str) -> List[str]:
        """
        Get recommended actions that require human approval.
        
        These actions may have business impact and need oversight.
        """
        actions = [
            'Review incident details and context',
            'Validate threat indicators',
            'Assess potential business impact'
        ]
        
        if attack_type == 'DDOS':
            actions.extend([
                'Consider blocking source IP ranges at perimeter',
                'Evaluate need for upstream ISP mitigation',
                'Prepare customer communication if service impacted'
            ])
        elif attack_type == 'PORTSCAN':
            actions.extend([
                'Isolate affected network segment if compromise suspected',
                'Conduct vulnerability assessment on targeted systems',
                'Review and update firewall rules'
            ])
        elif attack_type == 'BENIGN':
            actions.extend([
                'Tune detection rules to reduce false positives',
                'Update alert correlation logic'
            ])
        
        return actions
    
    def get_statistics(self) -> Dict:
        """
        Get decision engine statistics.
        """
        total = len(self.decision_history)
        
        return {
            'total_decisions': total,
            'auto_executed': self.auto_executed_count,
            'recommended': self.recommended_count,
            'advisory': self.advisory_count,
            'auto_execute_rate': f"{(self.auto_executed_count/total*100):.1f}%" if total > 0 else "0%"
        }
    
    def explain_decision(self, decision: Dict) -> str:
        """
        Generate human-readable explanation of decision.
        """
        explanation = f"""
DECISION EXPLANATION
====================
Incident: {decision['incident_id']}
Confidence Score: {decision['confidence_score']}/100
Threat Level: {decision['threat_level']}
Decision Type: {decision['decision_type']}

RATIONALE:
{decision['rationale']}

ACTIONS:
"""
        for i, action in enumerate(decision['actions'], 1):
            explanation += f"{i}. {action}\n"
        
        explanation += f"\nRequires Approval: {'YES' if decision['requires_approval'] else 'NO'}\n"
        explanation += f"Auto-Execute: {'YES' if decision['auto_execute'] else 'NO'}\n"
        explanation += f"\nNotification: {decision.get('notification', 'None')}\n"
        
        return explanation


# Global decision engine instance
decision_engine = DecisionEngine()
