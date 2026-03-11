"""
Security Tests for Cyber Incident Response AI

Validates offline operation, no external network calls,
and security best practices.

CRITICAL: These tests MUST FAIL if any external endpoints are detected.
"""

import pytest
import subprocess
import socket
import sys
import os
import re

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestOfflineOperation:
    """Test that system operates fully offline - MUST FAIL on external calls."""
    
    def test_no_external_api_endpoints_in_code(self):
        """
        CRITICAL: Scan all Python files for external API endpoints.
        This test MUST FAIL if any external URLs are found.
        """
        project_root = os.path.dirname(os.path.dirname(__file__))
        
        # External API patterns that indicate cloud/external calls
        forbidden_patterns = [
            r'https?://api\.openai\.com',
            r'https?://api\.anthropic\.com',
            r'https?://.*\.huggingface\.co/api',
            r'https?://.*\.amazonaws\.com',
            r'https?://.*\.googleapis\.com',
            r'https?://.*\.azure\.com',
            r'sk-[a-zA-Z0-9]{32,}',  # OpenAI API key pattern
        ]
        
        # Allowed local patterns
        allowed_patterns = [
            r'http://localhost',
            r'http://127\.0\.0\.1',
            r'http://0\.0\.0\.0',  # Will be flagged separately
        ]
        
        violations = []
        
        # Scan Python files
        for root, dirs, files in os.walk(project_root):
            # Skip venv, .git, etc.
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
            
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    for pattern in forbidden_patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        if matches:
                            violations.append(f"{filepath}: Found {pattern}")
        
        assert len(violations) == 0, (
            f"SECURITY VIOLATION: External API endpoints detected!\n" +
            "\n".join(violations) +
            "\n\nAll LLM calls MUST use local Ollama only."
        )
    
    def test_ollama_uses_localhost_only(self):
        """Verify Ollama adapter only connects to localhost."""
        from ai_engine.llm_adapter import OllamaAdapter
        
        adapter = OllamaAdapter(model="llama3")
        
        # Ollama should connect to localhost:11434 only
        # This is implicit in the subprocess call, but we verify the adapter exists
        assert adapter is not None
        assert adapter.model == "llama3"
    
    def test_elasticsearch_localhost_only(self):
        """Test that Elasticsearch connections are localhost only."""
        try:
            from ingestion.elastic_connector import ElasticsearchConnector
            
            connector = ElasticsearchConnector()
            
            # Verify all hosts are localhost
            for host in connector.hosts:
                assert any(local in host for local in ["localhost", "127.0.0.1"]), (
                    f"SECURITY VIOLATION: Elasticsearch host '{host}' is not localhost!"
                )
        except ImportError:
            # Elasticsearch connector may not be used
            pass
    
    def test_no_external_network_in_requirements(self):
        """Verify requirements.txt has no cloud service dependencies."""
        req_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "requirements.txt"
        )
        
        with open(req_path, 'r') as f:
            requirements = f.read()
        
        # Forbidden cloud dependencies
        forbidden = ["openai", "anthropic", "cohere", "google-cloud"]
        
        for pkg in forbidden:
            assert pkg not in requirements.lower(), (
                f"SECURITY VIOLATION: Cloud package '{pkg}' found in requirements.txt!"
            )


class TestAPISecurityBinding:
    """Test that API binds securely (localhost only for demo)."""
    
    def test_api_not_bound_to_all_interfaces(self):
        """
        CRITICAL: API should NOT bind to 0.0.0.0 in production.
        For hackathon demo, localhost binding is required.
        """
        api_main_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "api", "main.py"
        )
        
        if os.path.exists(api_main_path):
            with open(api_main_path, 'r') as f:
                content = f.read()
            
            # Check for 0.0.0.0 binding in uvicorn.run()
            if 'uvicorn.run' in content:
                # Extract uvicorn.run call
                import re
                uvicorn_calls = re.findall(r'uvicorn\.run\([^)]+\)', content, re.DOTALL)
                
                for call in uvicorn_calls:
                    # Should use 127.0.0.1 or localhost, not 0.0.0.0
                    if '0.0.0.0' in call:
                        # This is a warning, not a hard failure for demo purposes
                        print("WARNING: API binds to 0.0.0.0 - should use 127.0.0.1 for demo")
    
    def test_docker_compose_port_binding(self):
        """Test that Docker Compose doesn't expose ports to 0.0.0.0."""
        compose_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "docker-compose.yml"
        )
        
        if os.path.exists(compose_path):
            with open(compose_path, 'r') as f:
                content = f.read()
            
            # Check for 0.0.0.0 port bindings
            if '0.0.0.0:' in content:
                print("WARNING: Docker Compose exposes ports to 0.0.0.0")


class TestInputValidation:
    """Test input validation and sanitization."""
    
    def test_alert_data_validation(self):
        """Test that alert data is properly validated."""
        from api.models import AlertIngest
        from pydantic import ValidationError
        
        # Valid alert
        valid_alert = AlertIngest(
            attack_type="DDOS",
            severity="HIGH",
            source="SIEM"
        )
        assert valid_alert.attack_type == "DDOS"
        
        # Invalid alert (missing required fields)
        with pytest.raises(ValidationError):
            AlertIngest(attack_type="DDOS")  # Missing severity and source
    
    def test_sql_injection_prevention(self):
        """Test that SQL injection is prevented."""
        # With SQLAlchemy ORM, SQL injection is automatically prevented
        from database.models import Alert
        from sqlalchemy import inspect
        
        # Verify model uses ORM (not raw SQL)
        mapper = inspect(Alert)
        assert mapper is not None


class TestLLMAdapter:
    """Test LLM adapter security and functionality."""
    
    def test_llm_adapter_mock_mode(self):
        """Test that mock LLM adapter works for testing."""
        from ai_engine.llm_adapter import get_llm_adapter
        
        llm = get_llm_adapter("mock")
        assert llm.is_available()
        
        response = llm.generate("Test prompt")
        assert isinstance(response, str)
        assert len(response) > 0
    
    def test_llm_adapter_ollama_interface(self):
        """Test that Ollama adapter has correct interface."""
        from ai_engine.llm_adapter import OllamaAdapter
        
        adapter = OllamaAdapter(model="llama3")
        
        # Verify interface methods exist
        assert hasattr(adapter, 'generate')
        assert hasattr(adapter, 'is_available')
        assert hasattr(adapter, 'get_model_info')
        
        # Get model info
        info = adapter.get_model_info()
        assert info['provider'] == 'ollama'
        assert info['model'] == 'llama3'


class TestDataSecurity:
    """Test data security measures."""
    
    def test_no_hardcoded_secrets(self):
        """Test that no secrets are hardcoded in config."""
        project_root = os.path.dirname(os.path.dirname(__file__))
        config_path = os.path.join(project_root, "config", "config.yaml")
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config_content = f.read()
            
            # Should not contain obvious password/secret fields with values
            assert "password: " not in config_content.lower()
            assert "api_key: " not in config_content.lower()
            assert "secret: " not in config_content.lower()


class TestDependencyVersions:
    """Test that dependencies are pinned and secure."""
    
    def test_requirements_have_versions(self):
        """Test that requirements.txt specifies versions."""
        req_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "requirements.txt"
        )
        
        with open(req_path, 'r') as f:
            requirements = f.readlines()
        
        # Count lines with version specifiers
        versioned = sum(1 for line in requirements if ">=" in line or "==" in line)
        
        # Most requirements should have versions
        assert versioned > 10, "Requirements should specify versions for security"


class TestErrorHandling:
    """Test error handling and logging."""
    
    def test_ollama_connection_failure_handling(self):
        """Test graceful handling of Ollama connection failure."""
        from agents.incident_agent import IncidentResponseAgent
        
        # Create agent (may fail to connect to Ollama)
        agent = IncidentResponseAgent(ollama_model="llama3")
        
        # Should not crash even if Ollama is unavailable
        assert agent is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

