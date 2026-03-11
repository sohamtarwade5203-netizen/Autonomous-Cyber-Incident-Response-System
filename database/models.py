"""
Database Models for Cyber Incident Response AI

SQLAlchemy models for persistent storage of alerts, incidents, playbooks, and decisions.
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Alert(Base):
    """Security alert model."""
    __tablename__ = 'alerts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_id = Column(String(100), unique=True, nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    source = Column(String(50), nullable=False, index=True)
    attack_type = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), nullable=False, index=True)
    
    # Network details
    src_ip = Column(String(45))  # IPv6 support
    dst_ip = Column(String(45))
    src_port = Column(Integer)
    dst_port = Column(Integer)
    protocol = Column(String(20))
    
    # Anomaly detection results
    is_anomaly = Column(Boolean, default=False, index=True)
    anomaly_score = Column(Float)
    burst_score = Column(Float)
    
    # Relationship to incident
    incident_id = Column(Integer, ForeignKey('incidents.id'), nullable=True, index=True)
    incident = relationship("Incident", back_populates="alerts")
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<Alert(id={self.alert_id}, type={self.attack_type}, severity={self.severity})>"


class Incident(Base):
    """Correlated security incident model."""
    __tablename__ = 'incidents'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    incident_id = Column(String(100), unique=True, nullable=False, index=True)
    attack_type = Column(String(50), nullable=False, index=True)
    
    # Incident metrics
    alert_count = Column(Integer, nullable=False)
    anomaly_confidence = Column(Float, nullable=False)
    behavior_risk = Column(String(20), nullable=False, index=True)
    priority = Column(String(20), nullable=False, index=True)
    fidelity_score = Column(Float, nullable=False)
    
    # Status tracking
    status = Column(String(20), default='open', nullable=False, index=True)  # open, investigating, resolved, closed
    
    # Relationships
    alerts = relationship("Alert", back_populates="incident")
    playbook = relationship("Playbook", back_populates="incident", uselist=False)
    decision = relationship("Decision", back_populates="incident", uselist=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<Incident(id={self.incident_id}, type={self.attack_type}, priority={self.priority})>"


class Playbook(Base):
    """AI-generated incident response playbook model."""
    __tablename__ = 'playbooks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    incident_id = Column(Integer, ForeignKey('incidents.id'), unique=True, nullable=False, index=True)
    incident = relationship("Incident", back_populates="playbook")
    
    # Playbook content
    playbook_text = Column(Text, nullable=False)
    
    # Generation metadata
    model_used = Column(String(50), nullable=False)  # e.g., "llama3"
    validated = Column(Boolean, default=False)
    validation_score = Column(Float)
    
    # Execution tracking
    executed = Column(Boolean, default=False)
    execution_status = Column(String(20))  # pending, in_progress, completed, failed
    execution_notes = Column(Text)
    
    # Timestamps
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    executed_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<Playbook(incident_id={self.incident_id}, validated={self.validated})>"


class Decision(Base):
    """Autonomous decision record model."""
    __tablename__ = 'decisions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    incident_id = Column(Integer, ForeignKey('incidents.id'), unique=True, nullable=False, index=True)
    incident = relationship("Incident", back_populates="decision")
    
    # Decision details
    decision_type = Column(String(50), nullable=False, index=True)  # AUTO_EXECUTE, RECOMMEND, ADVISORY
    threat_level = Column(String(20), nullable=False, index=True)
    confidence_score = Column(Float, nullable=False)
    
    # Actions and rationale
    recommended_actions = Column(JSON)  # List of actions
    rationale = Column(Text, nullable=False)
    
    # Execution control
    auto_execute = Column(Boolean, default=False)
    requires_approval = Column(Boolean, default=True)
    approved_by = Column(String(100), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    
    # Agent reasoning trace
    agent_reasoning = Column(JSON)  # List of reasoning steps
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<Decision(incident_id={self.incident_id}, type={self.decision_type}, confidence={self.confidence_score})>"


class AuditLog(Base):
    """Audit trail for all system actions."""
    __tablename__ = 'audit_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Action details
    action_type = Column(String(50), nullable=False, index=True)  # ALERT_INGESTED, INCIDENT_CREATED, PLAYBOOK_GENERATED, etc.
    entity_type = Column(String(50), nullable=False)  # alert, incident, playbook, decision
    entity_id = Column(String(100), nullable=False, index=True)
    
    # User/system tracking
    actor = Column(String(100), default='system', nullable=False)
    
    # Details
    details = Column(JSON)
    
    def __repr__(self):
        return f"<AuditLog(action={self.action_type}, entity={self.entity_type}:{self.entity_id})>"
