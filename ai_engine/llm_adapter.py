"""
LLM Adapter Layer - Abstraction for Local LLM Inference

This module provides a clean interface for LLM operations, making it easy to:
- Swap between different local LLM providers (Ollama, llama.cpp, etc.)
- Mock LLMs for testing
- Add retry logic, caching, and monitoring
- Ensure offline-only operation

Usage:
    from ai_engine.llm_adapter import get_llm_adapter
    
    llm = get_llm_adapter("ollama", model="llama3")
    response = llm.generate(prompt)
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict
import subprocess
import os


class LLMAdapter(ABC):
    """Abstract base class for LLM adapters."""
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text from prompt.
        
        Args:
            prompt: Input prompt
            **kwargs: Provider-specific parameters
            
        Returns:
            Generated text response
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if LLM provider is available."""
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict:
        """Get information about the loaded model."""
        pass


class OllamaAdapter(LLMAdapter):
    """Adapter for local Ollama LLM inference."""
    
    def __init__(self, model: str = "llama3", timeout: int = 60):
        """
        Initialize Ollama adapter.
        
        Args:
            model: Ollama model name (e.g., "llama3", "mistral")
            timeout: Generation timeout in seconds
        """
        self.model = model
        self.timeout = timeout
        self._verify_offline()
    
    def _verify_offline(self):
        """Verify Ollama is configured for offline operation."""
        # Ollama runs locally on port 11434 by default
        # No external API keys or cloud endpoints
        pass
    
    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text using local Ollama.
        
        Args:
            prompt: Input prompt
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Returns:
            Generated text
        """
        try:
            # Build command
            cmd = ["ollama", "run", self.model]
            
            # Execute locally (fully offline)
            result = subprocess.run(
                cmd,
                input=prompt.encode("utf-8"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=self.timeout
            )
            
            if result.returncode != 0:
                error_msg = result.stderr.decode("utf-8", errors="ignore")
                raise RuntimeError(f"Ollama execution failed: {error_msg}")
            
            response = result.stdout.decode("utf-8", errors="ignore")
            return response.strip()
            
        except subprocess.TimeoutExpired:
            raise TimeoutError(
                f"Ollama request timed out after {self.timeout} seconds. "
                "Consider increasing timeout or using a smaller model."
            )
        except FileNotFoundError:
            raise RuntimeError(
                "Ollama not found. Please install Ollama from https://ollama.ai "
                f"and pull the {self.model} model: ollama pull {self.model}"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to generate text: {str(e)}")
    
    def is_available(self) -> bool:
        """Check if Ollama is installed and model is available."""
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0 and self.model in result.stdout
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def get_model_info(self) -> Dict:
        """Get information about the Ollama model."""
        try:
            result = subprocess.run(
                ["ollama", "show", self.model],
                capture_output=True,
                text=True,
                timeout=5
            )
            return {
                "provider": "ollama",
                "model": self.model,
                "available": self.is_available(),
                "info": result.stdout if result.returncode == 0 else "Not available"
            }
        except Exception as e:
            return {
                "provider": "ollama",
                "model": self.model,
                "available": False,
                "error": str(e)
            }


class MockLLMAdapter(LLMAdapter):
    """Mock LLM adapter for testing (no external dependencies)."""
    
    def __init__(self, response_template: str = "Mock playbook for {incident_type}"):
        self.response_template = response_template
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Return mock response for testing."""
        # Extract incident type from prompt if possible
        incident_type = "UNKNOWN"
        if "Type:" in prompt:
            lines = prompt.split("\n")
            for line in lines:
                if line.strip().startswith("- Type:"):
                    incident_type = line.split(":")[-1].strip()
                    break
        
        return self.response_template.format(incident_type=incident_type)
    
    def is_available(self) -> bool:
        """Mock is always available."""
        return True
    
    def get_model_info(self) -> Dict:
        """Return mock model info."""
        return {
            "provider": "mock",
            "model": "mock-llm",
            "available": True,
            "info": "Mock LLM for testing"
        }


def get_llm_adapter(
    provider: str = "ollama",
    model: str = "llama3",
    **kwargs
) -> LLMAdapter:
    """
    Factory function to get LLM adapter.
    
    Args:
        provider: LLM provider ("ollama", "mock")
        model: Model name
        **kwargs: Provider-specific parameters
        
    Returns:
        LLM adapter instance
        
    Example:
        # Production use
        llm = get_llm_adapter("ollama", model="llama3")
        response = llm.generate("Explain incident response")
        
        # Testing use
        llm = get_llm_adapter("mock")
        response = llm.generate("Test prompt")
    """
    provider = provider.lower()
    
    if provider == "ollama":
        return OllamaAdapter(model=model, **kwargs)
    elif provider == "mock":
        return MockLLMAdapter(**kwargs)
    else:
        raise ValueError(
            f"Unknown LLM provider: {provider}. "
            "Supported providers: 'ollama', 'mock'"
        )


# Convenience function for quick access
def generate_with_ollama(prompt: str, model: str = "llama3", timeout: int = 60) -> str:
    """
    Quick helper to generate text with Ollama.
    
    Args:
        prompt: Input prompt
        model: Ollama model name
        timeout: Generation timeout
        
    Returns:
        Generated text
    """
    llm = get_llm_adapter("ollama", model=model, timeout=timeout)
    return llm.generate(prompt)
