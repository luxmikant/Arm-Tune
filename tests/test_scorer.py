"""Tests for the quality scorer."""

from armtune.analyze.scorer import QualityScorer


def test_perfect_json():
    scorer = QualityScorer()
    output = '{"summary": "Duplicate billing", "category": "billing", "priority": "high", "recommended_action": "Refund"}'
    score = scorer.score(output)
    assert score >= 0.7, f"Expected >= 0.7, got {score}"


def test_empty_output():
    scorer = QualityScorer()
    assert scorer.score("") == 0.0
    assert scorer.score("   ") == 0.0


def test_invalid_json():
    scorer = QualityScorer()
    score = scorer.score("this is not json at all and has no structure")
    assert score < 0.5


def test_markdown_wrapped_json():
    scorer = QualityScorer()
    output = '```json\n{"summary": "Bug report", "category": "technical", "priority": "medium", "recommended_action": "Debug"}\n```'
    score = scorer.score(output)
    assert score >= 0.7, f"Expected >= 0.7, got {score}"


def test_partial_keys():
    scorer = QualityScorer()
    output = '{"summary": "Issue"}'  # missing several keys
    score = scorer.score(output)
    assert 0.1 < score < 0.6
