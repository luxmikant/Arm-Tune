"""Structured quality scorer for support-ticket classification output."""

from __future__ import annotations

import json


class QualityScorer:
    """Scores LLM output quality for the support-ticket classification task.

    Validates JSON structure and grades content completeness.
    Returns a score from 0.0 (invalid) to 1.0 (perfect).
    """

    EXPECTED_KEYS = {"summary", "category", "priority", "recommended_action"}
    VALID_PRIORITIES = {"low", "medium", "high", "critical"}
    VALID_CATEGORIES = {
        "billing", "technical", "account", "general",
        "security", "performance", "feature_request", "other",
    }

    def score(self, generated_text: str, prompt: str = "") -> float:
        if not generated_text or not generated_text.strip():
            return 0.0

        parsed = self._extract_json(generated_text)
        if parsed is None:
            return 0.1

        expected = {}
        if prompt:
            expected_data = self._extract_json(prompt)
            if expected_data is not None:
                expected = expected_data

        score = 0.0
        weight = 1.0 / len(self.EXPECTED_KEYS)

        for key in self.EXPECTED_KEYS:
            if key not in parsed:
                continue
            value = parsed[key]
            if not isinstance(value, str) or not value.strip():
                continue
            if key == "priority":
                if value.lower() in self.VALID_PRIORITIES:
                    score += weight
            elif key == "category":
                if value.lower() in self.VALID_CATEGORIES:
                    score += weight
                    expected_value = str(expected.get("expected_category", "")).lower()
                    if expected_value and value.lower() == expected_value:
                        score += weight
            elif key == "summary":
                if len(value.strip()) > 5:
                    score += weight * 0.9
            elif key == "recommended_action":
                if len(value.strip()) > 5:
                    score += weight * 0.9

        return min(score + 0.1, 1.0) if score > 0 else 0.2

    def _extract_json(self, text: str) -> dict | None:
        text = text.strip()

        if text.startswith("```"):
            marker_end = text.find("\n")
            if marker_end > 0:
                text = text[marker_end + 1:]
            end_marker = text.rfind("```")
            if end_marker > 0:
                text = text[:end_marker]

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        for start_char, end_char in [("{", "}"), ("[", "]")]:
            s = text.find(start_char)
            e = text.rfind(end_char)
            if s >= 0 and e > s:
                try:
                    return json.loads(text[s:e + 1])
                except json.JSONDecodeError:
                    continue

        return None


__all__ = ["QualityScorer"]
