"""Tests for prompt loading."""

from armtune.prompts.loader import load_prompts


def test_load_default_prompts():
    prompts = load_prompts()
    assert isinstance(prompts, list)
    assert len(prompts) >= 3
    for prompt in prompts:
        assert isinstance(prompt, str)
        assert len(prompt) > 0


def test_prompts_contain_json():
    prompts = load_prompts()
    import json
    for prompt in prompts:
        data = json.loads(prompt)
        assert "instruction" in data or "ticket" in data or "system" in data
