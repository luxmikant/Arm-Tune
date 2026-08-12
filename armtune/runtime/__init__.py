"""Runtime adapters for LLM inference (llama.cpp + future vLLM)."""

from .base import GenerationRequest, GenerationResponse, RuntimeAdapter
from .factory import build_adapter_factory, get_runtime_adapter
from .llama_server import LlamaServerAdapter

__all__ = [
    "GenerationRequest",
    "GenerationResponse",
    "RuntimeAdapter",
    "LlamaServerAdapter",
    "build_adapter_factory",
    "get_runtime_adapter",
]
