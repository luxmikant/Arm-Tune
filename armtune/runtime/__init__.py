"""Runtime adapters for LLM inference (llama.cpp + future vLLM)."""

from .base import GenerationRequest, GenerationResponse, RuntimeAdapter
from .factory import get_runtime_adapter

__all__ = ["GenerationRequest", "GenerationResponse", "RuntimeAdapter", "get_runtime_adapter"]
