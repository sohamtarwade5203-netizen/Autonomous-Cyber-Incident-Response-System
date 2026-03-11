"""
Pipeline Unit Tests for Cyber Incident Response AI

Tests core pipeline components: anomaly detection, UEBA correlation,
fidelity ranking, and decision engine.
"""

import pytest
import pandas as pd
import numpy as np
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.tools import (
    analyze_incident_severity,
    determine_threat_level,
    calculate_confidence_score,
    validate_playbook_quality
)
from agents.decision_engine import decision_engine


class TestAnomalyDetection:
    """Test anomaly detection functionality."""
    
    def test_isolation_forest_detection(self):
        """Test PyOD Isolation Forest anomaly detection."""
        from pyod.models.iforest import IForest
        
        # Create synthetic data
        normal_data = np.random.randn(100, 2)
        anomalies = np.random.randn(10, 2) * 3 + 5  # Outliers
        X = np.vstack([normal_data, anomalies])
        
        # Train model
        model = IForest(contamination=0.1, random_state=42)
        model.fit(X)
        
        # Predict
        predictions = model.predict(X)
        
        # Should detect some anomalies
        assert predictions.sum() > 0
        assert predictions.sum() < len(X)


class TestUEBACorrelation:
    """Test UEBA correlation logic."""
    
    def test_incident_severity_analysis(self):
        """Test incident severity analysis."""
        incident = {
            "attack_type": "DDOS",
            "alert_count": 10000,
            "anomaly_confidence": 95,
            "behavior_risk": "CRITICAL"
        }
        
        analysis = analyze_incident_severity(incident)
        
        assert "severity_level" in analysis
        assert "risk_factors" in analysis
        assert analysis["severity_level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    
    def test_threat_level_determination(self):
        """Test threat level determination."""
        incident = {
            "attack_type": "DDOS",
            "alert_count": 50000,
            "fidelity_score": 85
        }
        
        threat_level = determine_threat_level(incident)
        
        assert threat_level in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        # DDOS with high alert count should be high threat
        assert threat_level in ["HIGH", "CRITICAL"]
    
    def test_confidence_score_calculation(self):
        """Test confidence score calculation."""
        incident = {
            "anomaly_confidence": 90,
            "fidelity_score": 85,
            "behavior_risk": "HIGH",
            "alert_count": 1000
        }
        
        confidence = calculate_confidence_score(incident)
        
        assert 0 <= confidence <= 100
        # High metrics should yield high confidence
        assert confidence >= 70


class TestDecisionEngine:
    """Test autonomous decision engine."""
    
    def test_auto_execute_decision(self):
        """Test auto-execute decision for high confidence."""
        incident = {
            "attack_type": "DDOS",
            "alert_count": 100000,
            "fidelity_score": 95,
            "anomaly_confidence": 98,
            "behavior_risk": "CRITICAL"
        }
        
        decision = decision_engine.make_decision(incident, confidence=95, threat_level="CRITICAL")
        
        assert decision["decision_type"] == "AUTO_EXECUTE"
        assert decision["auto_execute"] is True
        assert len(decision["actions"]) > 0
    
    def test_recommend_decision(self):
        """Test recommend decision for medium confidence."""
        incident = {
            "attack_type": "PORTSCAN",
            "alert_count": 500,
            "fidelity_score": 75,
            "anomaly_confidence": 72
        }
        
        decision = decision_engine.make_decision(incident, confidence=75, threat_level="MEDIUM")
        
        assert decision["decision_type"] == "RECOMMEND"
        assert decision["requires_approval"] is True
    
    def test_advisory_decision(self):
        """Test advisory decision for low confidence."""
        incident = {
            "attack_type": "BENIGN",
            "alert_count": 10,
            "fidelity_score": 45
        }
        
        decision = decision_engine.make_decision(incident, confidence=45, threat_level="LOW")
        
        assert decision["decision_type"] == "ADVISORY"
        assert decision["auto_execute"] is False


class TestPlaybookValidation:
    """Test playbook generation and validation."""
    
    def test_valid_playbook(self):
        """Test validation of a well-formed playbook."""
        playbook = """
        # Incident Response Playbook
        
        ## Step 1: Initial Assessment
        - Verify alert details
        - Assess impact
        
        ## Step 2: Containment
        - Block suspicious IPs
        - Isolate affected systems
        
        ## Step 3: Investigation
        - Collect evidence
        - Analyze logs
        
        ## Step 4: Eradication
        - Remove malware
        - Patch vulnerabilities
        
        ## Step 5: Recovery
        - Restore services
        - Monitor for recurrence
        """
        
        validation = validate_playbook_quality(playbook)
        
        assert validation["valid"] is True
        assert validation["score"] >= 60
    
    def test_invalid_playbook(self):
        """Test validation of a poorly-formed playbook."""
        playbook = "This is not a proper playbook."
        
        validation = validate_playbook_quality(playbook)
        
        assert validation["valid"] is False
        assert len(validation["issues"]) > 0


class TestDataProcessing:
    """Test data processing utilities."""
    
    def test_alert_dataframe_processing(self):
        """Test processing of alert DataFrame."""
        # Create sample alert data
        alerts = pd.DataFrame({
            "timestamp": pd.date_range("2025-01-01", periods=100, freq="1min"),
            "attack_type": ["DDOS"] * 50 + ["PORTSCAN"] * 50,
            "severity": ["HIGH"] * 30 + ["MEDIUM"] * 70,
            "src_ip": ["192.168.1.1"] * 100
        })
        
        # Basic processing
        assert len(alerts) == 100
        assert "attack_type" in alerts.columns
        assert alerts["attack_type"].nunique() == 2
    
    def test_temporal_aggregation(self):
        """Test temporal aggregation of alerts."""
        alerts = pd.DataFrame({
            "timestamp": pd.date_range("2025-01-01", periods=100, freq="1min"),
            "attack_type": ["DDOS"] * 100
        })
        
        # Aggregate by 5-minute windows
        alerts["time_window"] = pd.to_datetime(alerts["timestamp"]).dt.floor("5min")
        aggregated = alerts.groupby("time_window").size()
        
        assert len(aggregated) == 20  # 100 minutes / 5 = 20 windows


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
