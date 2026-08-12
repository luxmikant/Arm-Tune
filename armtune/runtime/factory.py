"""Runtime adapter factory — builds adapters from a Profile."""

from __future__ import annotations

import shutil
from collections.abc import Callable
from pathlib import Path

from ..config import Profile
from .base import RuntimeAdapter

AdapterFactory = Callable[[Profile], RuntimeAdapter]


def _discover_model(profile: Profile) -> str | None:
    if profile.model.model_path and Path(profile.model.model_path).exists():
        return profile.model.model_path
    models_dir = Path("models")
    if models_dir.is_dir():
        ggufs = sorted(models_dir.rglob("*.gguf"))
        if ggufs:
            return str(ggufs[-1])
    return None


def make_llama_server_adapter(profile: Profile) -> RuntimeAdapter:
    from .llama_server import LlamaServerAdapter

    model_path = _discover_model(profile)
    return LlamaServerAdapter(
        model_path=model_path,
        n_threads=profile.runtime.threads,
        n_threads_batch=profile.runtime.batch_threads,
        n_ctx=profile.model.context_size,
        n_parallel=profile.runtime.concurrency,
        batch_size=profile.model.batch_size,
        enable_mmap=profile.runtime.enable_mmap,
        enable_mlock=profile.runtime.enable_mlock,
        enable_prompt_cache=profile.runtime.enable_prompt_cache,
    )


def make_llama_lib_adapter(profile: Profile) -> RuntimeAdapter:
    from .llama_cpp import LlamaCppAdapter

    model_path = _discover_model(profile)
    return LlamaCppAdapter(
        model_path=model_path,
        n_threads=profile.runtime.threads,
        n_ctx=profile.model.context_size,
    )


def make_mock_adapter(profile: Profile) -> RuntimeAdapter:
    from .mock import MockAdapter

    return MockAdapter()


def build_adapter_factory(runtime_backend: str = "auto") -> AdapterFactory:
    """Return an adapter factory for the given backend.

    ``auto`` prefers the llama-server binary (supports KleidiAI builds),
    then the Python bindings, then the mock adapter.
    """
    backend = runtime_backend.lower()

    if backend in {"llama-server", "llama-server-arm"}:
        return make_llama_server_adapter
    if backend in {"llama-lib", "llama-cpp", "llama-cpp-python"}:
        return make_llama_lib_adapter
    if backend == "mock":
        return make_mock_adapter

    # auto
    if shutil.which("llama-server"):
        return make_llama_server_adapter

    from importlib.util import find_spec

    if find_spec("llama_cpp") is not None:
        return make_llama_lib_adapter

    return make_mock_adapter


def get_runtime_adapter(adapter_type: str = "auto", **kwargs) -> RuntimeAdapter:
    """Legacy direct-adapter constructor (kept for tests)."""
    if adapter_type == "llama-cpp":
        from .llama_cpp import LlamaCppAdapter

        return LlamaCppAdapter(**kwargs)
    if adapter_type == "llama-server":
        from .llama_server import LlamaServerAdapter

        return LlamaServerAdapter(**kwargs)
    if adapter_type == "mock":
        from .mock import MockAdapter

        return MockAdapter(**kwargs)
    raise ValueError(f"Unknown adapter type: {adapter_type}")


__all__ = [
    "AdapterFactory",
    "build_adapter_factory",
    "get_runtime_adapter",
    "make_llama_server_adapter",
    "make_llama_lib_adapter",
    "make_mock_adapter",
]
