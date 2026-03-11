"""
Agent State Management for LangGraph

This module defines the state structure for the incident response agent.
All state is stored locally in memory - no external storage.
"""

from typing import TypedDict, List, Dict, Optional, Annotated
from datetime import datetime
import operator


class AgentState(TypedDict):
    """
    State schema for the incident response agent.
    
    This state is passed between agent nodes and tracks the entire
    incident analysis and response workflow.
    """
    # Input
    incident_data: Dict  # Raw incident data from UEBA correlation
    
    # Analysis results
    anomaly_analysis: Optional[str]  # Analysis from anomaly detection
    threat_level: Optional[str]  # CRITICAL, HIGH, MEDIUM, LOW
    confidence_score: Optional[int]  # 0-100
    
    # Decision making
    recommended_actions: Annotated[List[str], operator.add]  # List of recommended actions
    auto_execute: Optional[bool]  # Whether to auto-execute actions
    
    # Response generation
    playbook: Optional[str]  # Generated incident response playbook
    playbook_validated: Optional[bool]  # Whether playbook passed validation
    
    # Metadata
    agent_reasoning: Annotated[List[str], operator.add]  # Agent's reasoning steps
    timestamp: Optional[str]  # When processing started
    
    # Final output
    final_response: Optional[Dict]  # Complete response package


class IncidentContext:
    """
    Context manager for incident processing.
    Stores all incident-related data locally.
    """
    
    def __init__(self):
        self.incidents = {}  # In-memory storage
        self.processing_history = []
    
    def add_incident(self, incident_id: str, state: AgentState):
        """Store incident state locally"""
        self.incidents[incident_id] = {
            'state': state,
            'created_at': datetime.now().isoformat(),
            'status': 'processing'
        }
    
    def update_incident(self, incident_id: str, updates: Dict):
        """Update incident state"""
        if incident_id in self.incidents:
            self.incidents[incident_id]['state'].update(updates)
            self.incidents[incident_id]['updated_at'] = datetime.now().isoformat()
    
    def get_incident(self, incident_id: str) -> Optional[Dict]:
        """Retrieve incident state"""
        return self.incidents.get(incident_id)
    
    def mark_complete(self, incident_id: str):
        """Mark incident as complete"""
        if incident_id in self.incidents:
            self.incidents[incident_id]['status'] = 'complete'
            self.incidents[incident_id]['completed_at'] = datetime.now().isoformat()
            self.processing_history.append(incident_id)
    
    def get_all_incidents(self) -> List[Dict]:
        """Get all incidents (for API endpoints)"""
        return [
            {
                'incident_id': iid,
                **data
            }
            for iid, data in self.incidents.items()
        ]


# Global context instance (local to this process)
incident_context = IncidentContext()
