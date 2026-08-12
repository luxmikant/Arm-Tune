"""Mock runtime adapter for testing without a model."""

from __future__ import annotations

import json
import os
import time

from .base import GenerationRequest, GenerationResponse, RuntimeAdapter


class MockAdapter(RuntimeAdapter):
    def __init__(self, delay_ms: float = 50.0, tokens: int = 100, **kwargs) -> None:
        self.delay_ms = delay_ms
        self.tokens = tokens
        self._initialized = False
        self._pid: int | None = None

    @property
    def model_path(self) -> str | None:
        return None

    @property
    def process_id(self) -> int | None:
        return self._pid

    def initialize(self) -> None:
        self._initialized = True
        self._pid = os.getpid()

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        if not self._initialized:
            raise RuntimeError("Not initialized.")

        start = time.perf_counter()
        time.sleep(self.delay_ms / 1000.0)
        first_token_time = time.perf_counter()

        text = json.dumps({
            "summary": "Mock response for testing.",
            "category": "general",
            "priority": "low",
            "recommended_action": "No action required.",
        })

        total = time.perf_counter() - start
        ttft = first_token_time - start
        tps = self.tokens / total if total > 0 else 0.0

        return GenerationResponse(
            text=text,
            completion_tokens=self.tokens,
            total_tokens=self.tokens,
            ttft_seconds=ttft,
            total_seconds=total,
            tokens_per_second=tps,
        )

    def shutdown(self) -> None:
        self._initialized = False
        self._pid = None

    def is_available(self) -> bool:
        return True


__all__ = ["MockAdapter"]
