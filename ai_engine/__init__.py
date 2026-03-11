"""AI Engine Package - Local LLM Integration"""

from .llm_adapter import get_llm_adapter, generate_with_ollama, LLMAdapter

__all__ = ['get_llm_adapter', 'generate_with_ollama', 'LLMAdapter']
