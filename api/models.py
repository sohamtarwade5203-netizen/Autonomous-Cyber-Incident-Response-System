"""
Pydantic Models for API Request/Response Validation

All models are for LOCAL API validation - no external data transfer.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class NormalizedAlert(BaseModel):
    """
    Unified alert schema used across SIEM, EDR, firewall and batch pipelines.

    This represents the *normalized* view of any incoming alert so that:
    - Connectors (Elasticsearch/SIEM, file loaders, etc.) can map their native
      formats into this structure.
    - Downstream analytics (anomaly detection, UEBA, correlation) can assume a
      consistent set of core fields.
    """

    # Core routing / identity
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Alert timestamp in ISO 8601 format (UTC by default).",
    )
    # NOTE: external JSON can still use `source` thanks to the alias.
    source_system: str = Field(
        ...,
        alias="source",
        description="Source system for the alert (e.g. SIEM, EDR, FIREWALL).",
    )

    # Entity and network context
    user: Optional[str] = Field(
        default=None,
        description="User or account associated with the alert, if available.",
    )
    host: Optional[str] = Field(
        default=None,
        description="Hostname or endpoint identifier associated with the alert.",
    )
    source_ip: Optional[str] = Field(
        default=None,
        description="Source IP address for the event, if applicable.",
    )
    destination_ip: Optional[str] = Field(
        default=None,
        description="Destination IP address for the event, if applicable.",
    )

    # Logical event description
    event_type: str = Field(
        ...,
        description=(
            "High-level normalized event type (e.g. PORTSCAN, DDOS, "
            "FAILED_LOGIN, MALWARE_ALERT)."
        ),
    )
    attack_type: Optional[str] = Field(
        default=None,
        description=(
            "Attack category, when applicable. For simple demos this can match "
            "`event_type` (e.g. PORTSCAN, DDOS, BENIGN)."
        ),
    )
    severity: str = Field(
        ...,
        description="Alert severity (e.g. CRITICAL, HIGH, MEDIUM, LOW).",
    )

    # Raw payload for audit / enrichment
    raw_details: Optional[dict] = Field(
        default=None,
        description="Source-system specific payload for audit and deep analysis.",
    )

    class Config:
        allow_population_by_field_name = True
        json_schema_extra = {
            "example": {
                "source": "SIEM",  # Alias for `source_system`
                "timestamp": "2026-03-28T10:30:00Z",
                "source_system": "SIEM",
                "user": "alice",
                "host": "workstation-01",
                "source_ip": "192.168.1.100",
                "destination_ip": "10.0.0.50",
                "event_type": "PORTSCAN",
                "attack_type": "PORTSCAN",
                "severity": "HIGH",
                "raw_details": {"vendor_event_id": "12345", "original_message": "..."},
            }
        }


class AlertIngest(NormalizedAlert):
    """
    Model for ingesting a single security alert via the REST API.

    This simply wraps the `NormalizedAlert` schema so the API and the
    offline pipeline share the same normalized structure.
    """

    class Config(NormalizedAlert.Config):
        json_schema_extra = {
            "example": {
                "source": "SIEM",
                "timestamp": "2026-03-28T10:30:00Z",
                "source_system": "SIEM",
                "user": "alice",
                "host": "workstation-01",
                "source_ip": "192.168.1.100",
                "destination_ip": "10.0.0.50",
                "event_type": "PORTSCAN",
                "attack_type": "PORTSCAN",
                "severity": "HIGH",
                "raw_details": {"vendor_event_id": "12345"},
            }
        }


class BatchAlertIngest(BaseModel):
    """
    Model for ingesting multiple alerts at once.
    """
    alerts: List[AlertIngest] = Field(..., description="List of alerts to ingest")

    class Config:
        json_schema_extra = {
            "example": {
                "alerts": [
                    {
                        "source": "SIEM",
                        "timestamp": "2026-03-28T10:30:00Z",
                        "source_system": "SIEM",
                        "event_type": "DDOS",
                        "attack_type": "DDOS",
                        "severity": "HIGH"
                    },
                    {
                        "source": "EDR",
                        "timestamp": "2026-03-28T10:31:00Z",
                        "source_system": "EDR",
                        "event_type": "PORTSCAN",
                        "attack_type": "PORTSCAN",
                        "severity": "MEDIUM"
                    }
                ]
            }
        }


class AlertResponse(BaseModel):
    """
    Response model for alert ingestion.
    """
    status: str = Field(..., description="Success or error status")
    message: str = Field(..., description="Response message")
    alert_id: Optional[str] = Field(default=None, description="Generated alert ID")
    processed_at: str = Field(..., description="Processing timestamp")


class IncidentSummary(BaseModel):
    """
    Summary model for incident listing.
    """
    incident_id: str
    attack_type: str
    threat_level: str
    confidence_score: int
    alert_count: int
    status: str
    created_at: str


class IncidentDetail(BaseModel):
    """
    Detailed incident information.
    """
    incident_id: str
    attack_type: str
    threat_level: str
    confidence_score: int
    alert_count: int
    fidelity_score: int
    priority: str
    behavior_risk: str
    anomaly_confidence: int
    recommended_actions: List[str]
    auto_execute: bool
    agent_reasoning: Optional[List[str]] = None
    created_at: str
    status: str


class PlaybookResponse(BaseModel):
    """
    Response model for playbook generation.
    """
    incident_id: str
    playbook: str
    validated: bool
    generated_at: str
    threat_level: str
    confidence_score: int


class HealthResponse(BaseModel):
    """
    Health check response.
    """
    status: str
    timestamp: str
    ollama_available: bool
    agent_ready: bool
    version: str = "2.0.0-agentic"


class DecisionExplanation(BaseModel):
    """
    Detailed decision explanation.
    """
    incident_id: str
    decision_type: str
    confidence_score: int
    threat_level: str
    rationale: str
    actions: List[str]
    requires_approval: bool
    auto_execute: bool
    notification: str
