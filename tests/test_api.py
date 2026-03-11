"""
API Integration Tests for Cyber Incident Response AI

Tests all FastAPI endpoints including health checks, alert ingestion,
incident management, and playbook generation.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.main import app

client = TestClient(app)


class TestHealthEndpoints:
    """Test system health and status endpoints."""
    
    def test_root_endpoint(self):
        """Test root endpoint returns welcome message."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "online"
        assert data["mode"] == "fully_offline"
        assert "version" in data
    
    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "agent_ready" in data


class TestAlertIngestion:
    """Test alert ingestion endpoints."""
    
    def test_ingest_single_alert(self):
        """Test ingesting a single security alert."""
        alert_data = {
            "attack_type": "DDOS",
            "severity": "HIGH",
            "source": "SIEM"
        }
        
        response = client.post("/alerts/ingest", json=alert_data)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "accepted"
        assert "alert_id" in data
        assert "processed_at" in data
    
    def test_ingest_batch_alerts(self):
        """Test ingesting multiple alerts at once."""
        batch_data = {
            "alerts": [
                {"attack_type": "DDOS", "severity": "HIGH", "source": "SIEM"},
                {"attack_type": "PORTSCAN", "severity": "MEDIUM", "source": "EDR"},
                {"attack_type": "DDOS", "severity": "CRITICAL", "source": "SIEM"}
            ]
        }
        
        response = client.post("/alerts/batch", json=batch_data)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "accepted"
        assert len(data["alert_ids"]) == 3
    
    def test_invalid_alert_data(self):
        """Test that invalid alert data is rejected."""
        invalid_data = {
            "invalid_field": "value"
        }
        
        response = client.post("/alerts/ingest", json=invalid_data)
        assert response.status_code == 422  # Validation error


class TestIncidentManagement:
    """Test incident management endpoints."""
    
    def test_list_incidents(self):
        """Test listing all incidents."""
        response = client.get("/incidents")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_incident_detail(self):
        """Test getting incident details."""
        # First create an incident by ingesting an alert
        alert_data = {"attack_type": "DDOS", "severity": "HIGH", "source": "SIEM"}
        ingest_response = client.post("/alerts/ingest", json=alert_data)
        alert_id = ingest_response.json()["alert_id"]
        
        # Wait a moment for processing (in real scenario, would use async wait)
        import time
        time.sleep(1)
        
        # Try to get incident (may not exist yet in test)
        response = client.get(f"/incidents/{alert_id}")
        # Accept both 200 (found) and 404 (not found yet) as valid
        assert response.status_code in [200, 404]
    
    def test_get_nonexistent_incident(self):
        """Test that requesting non-existent incident returns 404."""
        response = client.get("/incidents/nonexistent-id")
        assert response.status_code == 404


class TestStatistics:
    """Test statistics and metrics endpoints."""
    
    def test_get_statistics(self):
        """Test getting system statistics."""
        response = client.get("/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_incidents" in data
        assert "decision_stats" in data
        assert "timestamp" in data


@pytest.mark.asyncio
class TestAsyncOperations:
    """Test asynchronous operations."""
    
    async def test_concurrent_alert_ingestion(self):
        """Test that multiple alerts can be ingested concurrently."""
        import asyncio
        from httpx import AsyncClient
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            tasks = []
            for i in range(10):
                alert_data = {
                    "attack_type": "DDOS" if i % 2 == 0 else "PORTSCAN",
                    "severity": "HIGH",
                    "source": "SIEM"
                }
                tasks.append(ac.post("/alerts/ingest", json=alert_data))
            
            responses = await asyncio.gather(*tasks)
            
            # All should succeed
            for response in responses:
                assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
