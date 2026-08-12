"""Prompt loader for evaluation workloads."""

from __future__ import annotations

import json
from pathlib import Path


def load_prompts(path: str | Path | None = None) -> list[str]:
    """Load evaluation prompts from a path or use built-in defaults."""
    if path:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Prompts file not found: {path}")
        return _load_file(p)

    builtin = Path(__file__).parent / "tickets.json"
    if builtin.exists():
        return _load_file(builtin)

    return _default_prompts()


def _load_file(path: Path) -> list[str]:
    if path.suffix == ".jsonl":
        prompts: list[str] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                prompts.append(line)
        return prompts

    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        if all(isinstance(x, str) for x in data):
            return data
        return [json.dumps(item) for item in data]

    if isinstance(data, dict) and "prompts" in data:
        return data["prompts"]

    return []


def _default_prompts() -> list[str]:
    return [
        json.dumps({
            "system": "You are a support-ticket classifier. Return ONLY valid JSON.",
            "instruction": "Classify this ticket and summarize.",
            "ticket": "User reports being charged twice for the same subscription. "
                      "Invoice #4521 dated Jan 15 and Invoice #4522 dated Jan 16 "
                      "both show $49.99.",
        }),
        json.dumps({
            "system": "You are a support-ticket classifier. Return ONLY valid JSON.",
            "instruction": "Classify this ticket and summarize.",
            "ticket": "Cannot log in to the dashboard after password reset. "
                      "Email verification link returns 'token expired' error.",
        }),
        json.dumps({
            "system": "You are a support-ticket classifier. Return ONLY valid JSON.",
            "instruction": "Classify this ticket and summarize.",
            "ticket": "API latency increased from 200ms to 800ms after the "
                      "latest deployment. Affected endpoint: /api/v1/search.",
        }),
        json.dumps({
            "system": "You are a support-ticket classifier. Return ONLY valid JSON.",
            "instruction": "Classify this ticket and summarize.",
            "ticket": "Suspicious login attempts from IP 203.0.113.42. "
                      "5 failed attempts in 10 minutes. Account locked.",
        }),
        json.dumps({
            "system": "You are a support-ticket classifier. Return ONLY valid JSON.",
            "instruction": "Classify this ticket and summarize.",
            "ticket": "Request to add dark mode to the dashboard. "
                      "Current light theme causes eye strain for nighttime users.",
        }),
    ]


__all__ = ["load_prompts"]
