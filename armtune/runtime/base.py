"""Runtime adapter interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class GenerationRequest:
    prompt: str
    max_tokens: int = 256
    temperature: float = 0.0
    seed: int = 42


@dataclass
class GenerationResponse:
    text: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    ttft_seconds: float = 0.0
    total_seconds: float = 0.0
    tokens_per_second: float = 0.0
    prompt_tokens_per_second: float = 0.0


class RuntimeAdapter(ABC):
    @abstractmethod
    def initialize(self) -> None: ...

    @abstractmethod
    def generate(self, request: GenerationRequest) -> GenerationResponse: ...

    @abstractmethod
    def shutdown(self) -> None: ...

    @abstractmethod
    def is_available(self) -> bool: ...

    @property
    @abstractmethod
    def model_path(self) -> str | None: ...

    @property
    @abstractmethod
    def process_id(self) -> int | None: ...


__all__ = ["GenerationRequest", "GenerationResponse", "RuntimeAdapter"]
