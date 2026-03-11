"""
FastAPI Main Application

LOCAL REST API for real-time alert ingestion and incident management.
Runs on localhost only - fully offline operation.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from datetime import datetime
import subprocess
import uuid
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.models import (
    AlertIngest, BatchAlertIngest, AlertResponse,
    IncidentSummary, IncidentDetail, PlaybookResponse,
    HealthResponse, DecisionExplanation
)
from agents.incident_agent import IncidentResponseAgent
from agents.decision_engine import decision_engine
from agents.state import incident_context

# Initialize FastAPI app
app = FastAPI(
    title="Cyber Incident Response AI",
    description="Autonomous incident response system with agentic AI - Fully Offline",
    version="2.0.0-agentic",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Initialize agent (lazy loading)
_agent = None

def get_agent() -> IncidentResponseAgent:
    """Get or create agent instance"""
    global _agent
    if _agent is None:
        _agent = IncidentResponseAgent(ollama_model="llama3")
    return _agent


# ============================================================================
# HEALTH CHECK ENDPOINT
# ============================================================================

@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """
    Check system health and readiness.
    
    Verifies:
    - API is running
    - Ollama is available
    - Agent is ready
    """
    # Check Ollama availability
    ollama_available = False
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            timeout=5
        )
        ollama_available = result.returncode == 0
    except:
        pass
    
    return HealthResponse(
        status="healthy" if ollama_available else "degraded",
        timestamp=datetime.now().isoformat(),
        ollama_available=ollama_available,
        agent_ready=True,
        version="2.0.0-agentic"
    )


# ============================================================================
# ALERT INGESTION ENDPOINTS
# ============================================================================

@app.post("/alerts/ingest", response_model=AlertResponse, tags=["Alerts"])
async def ingest_alert(alert: AlertIngest, background_tasks: BackgroundTasks):
    """
    Ingest a single security alert for real-time processing.
    
    The alert will be processed by the agentic workflow in the background.
    """
    alert_id = str(uuid.uuid4())
    
    # Add background task to process alert
    background_tasks.add_task(process_alert_async, alert_id, alert.dict())
    
    return AlertResponse(
        status="accepted",
        message=f"Alert accepted for processing: {alert.attack_type}",
        alert_id=alert_id,
        processed_at=datetime.now().isoformat()
    )


@app.post("/alerts/batch", response_model=dict, tags=["Alerts"])
async def ingest_batch_alerts(batch: BatchAlertIngest, background_tasks: BackgroundTasks):
    """
    Ingest multiple alerts at once.
    
    Useful for bulk import or SIEM integration.
    """
    alert_ids = []
    
    for alert in batch.alerts:
        alert_id = str(uuid.uuid4())
        alert_ids.append(alert_id)
        background_tasks.add_task(process_alert_async, alert_id, alert.dict())
    
    return {
        "status": "accepted",
        "message": f"Batch of {len(batch.alerts)} alerts accepted",
        "alert_ids": alert_ids,
        "processed_at": datetime.now().isoformat()
    }


async def process_alert_async(alert_id: str, alert_data: dict):
    """
    Background task to process alert through agentic workflow.
    
    This simulates real-time incident response processing.
    """
    # Convert alert to incident format
    incident = {
        'attack_type': alert_data['attack_type'],
        'severity': alert_data['severity'],
        'alert_count': 1,  # Single alert
        'fidelity_score': 75,  # Simulated
        'anomaly_confidence': 70,  # Simulated
        'priority': 'HIGH' if alert_data['severity'] == 'HIGH' else 'MEDIUM',
        'behavior_risk': 'HIGH'
    }
    
    # Process through agent
    agent = get_agent()
    response = agent.process_incident(incident)
    
    # Store in context
    incident_context.add_incident(alert_id, {
        'incident_data': incident,
        'final_response': response
    })
    incident_context.mark_complete(alert_id)


# ============================================================================
# INCIDENT MANAGEMENT ENDPOINTS
# ============================================================================

@app.get("/incidents", response_model=List[IncidentSummary], tags=["Incidents"])
async def list_incidents():
    """
    List all processed incidents.
    
    Returns summary information for each incident.
    """
    incidents = incident_context.get_all_incidents()
    
    summaries = []
    for inc in incidents:
        response = inc.get('state', {}).get('final_response', {})
        summaries.append(IncidentSummary(
            incident_id=inc['incident_id'],
            attack_type=response.get('incident_id', 'UNKNOWN'),
            threat_level=response.get('threat_level', 'UNKNOWN'),
            confidence_score=response.get('confidence_score', 0),
            alert_count=inc.get('state', {}).get('incident_data', {}).get('alert_count', 0),
            status=inc.get('status', 'unknown'),
            created_at=inc.get('created_at', '')
        ))
    
    return summaries


@app.get("/incidents/{incident_id}", response_model=IncidentDetail, tags=["Incidents"])
async def get_incident(incident_id: str):
    """
    Get detailed information about a specific incident.
    """
    incident = incident_context.get_incident(incident_id)
    
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    state = incident.get('state', {})
    incident_data = state.get('incident_data', {})
    response = state.get('final_response', {})
    
    return IncidentDetail(
        incident_id=incident_id,
        attack_type=incident_data.get('attack_type', 'UNKNOWN'),
        threat_level=response.get('threat_level', 'UNKNOWN'),
        confidence_score=response.get('confidence_score', 0),
        alert_count=incident_data.get('alert_count', 0),
        fidelity_score=incident_data.get('fidelity_score', 0),
        priority=incident_data.get('priority', 'UNKNOWN'),
        behavior_risk=incident_data.get('behavior_risk', 'UNKNOWN'),
        anomaly_confidence=incident_data.get('anomaly_confidence', 0),
        recommended_actions=response.get('recommended_actions', []),
        auto_execute=response.get('auto_execute', False),
        agent_reasoning=response.get('agent_reasoning', []),
        created_at=incident.get('created_at', ''),
        status=incident.get('status', 'unknown')
    )


@app.get("/incidents/{incident_id}/playbook", response_model=PlaybookResponse, tags=["Incidents"])
async def get_incident_playbook(incident_id: str):
    """
    Get the AI-generated incident response playbook.
    """
    incident = incident_context.get_incident(incident_id)
    
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    response = incident.get('state', {}).get('final_response', {})
    
    return PlaybookResponse(
        incident_id=incident_id,
        playbook=response.get('playbook', 'No playbook generated'),
        validated=response.get('playbook_validated', False),
        generated_at=incident.get('created_at', ''),
        threat_level=response.get('threat_level', 'UNKNOWN'),
        confidence_score=response.get('confidence_score', 0)
    )


@app.get("/incidents/{incident_id}/decision", response_model=DecisionExplanation, tags=["Incidents"])
async def get_decision_explanation(incident_id: str):
    """
    Get detailed explanation of the autonomous decision made for this incident.
    """
    incident = incident_context.get_incident(incident_id)
    
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    # Get decision from history
    incident_data = incident.get('state', {}).get('incident_data', {})
    response = incident.get('state', {}).get('final_response', {})
    
    # Find matching decision in engine history
    attack_type = incident_data.get('attack_type', 'UNKNOWN')
    decisions = [d for d in decision_engine.decision_history if d['incident_id'] == attack_type]
    
    if not decisions:
        raise HTTPException(status_code=404, detail="Decision not found")
    
    decision = decisions[-1]  # Get most recent
    
    return DecisionExplanation(
        incident_id=incident_id,
        decision_type=decision['decision_type'],
        confidence_score=decision['confidence_score'],
        threat_level=decision['threat_level'],
        rationale=decision['rationale'],
        actions=decision['actions'],
        requires_approval=decision['requires_approval'],
        auto_execute=decision['auto_execute'],
        notification=decision.get('notification', '')
    )


# ============================================================================
# STATISTICS ENDPOINT
# ============================================================================

@app.get("/stats", tags=["System"])
async def get_statistics():
    """
    Get system statistics and metrics.
    """
    decision_stats = decision_engine.get_statistics()
    
    return {
        "total_incidents": len(incident_context.incidents),
        "completed_incidents": len(incident_context.processing_history),
        "decision_stats": decision_stats,
        "timestamp": datetime.now().isoformat()
    }


# ============================================================================
# ROOT ENDPOINT
# ============================================================================

@app.get("/", tags=["System"])
async def root():
    """
    API root endpoint with welcome message.
    """
    return {
        "message": "Cyber Incident Response AI - Agentic System",
        "version": "2.0.0-agentic",
        "status": "online",
        "mode": "fully_offline",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
