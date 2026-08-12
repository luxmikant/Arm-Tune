"""Runtime adapter factory."""

from __future__ import annotations

from .base import RuntimeAdapter


def get_runtime_adapter(adapter_type: str = "llama-cpp", **kwargs) -> RuntimeAdapter:
    if adapter_type == "llama-cpp":
        from .llama_cpp import LlamaCppAdapter
        return LlamaCppAdapter(**kwargs)
    elif adapter_type == "mock":
        from .mock import MockAdapter
        return MockAdapter(**kwargs)
    else:
        raise ValueError(f"Unknown adapter type: {adapter_type}")


__all__ = ["get_runtime_adapter"]
