"""Tests for the llama-server adapter prompt handling (offline)."""

import json

from armtune.runtime.llama_server import LlamaServerAdapter


def test_workload_prompt_becomes_chat_messages():
    prompt = json.dumps({
        "system": "You are a support-ticket classifier.",
        "instruction": "Classify this ticket.",
        "ticket": "Charged twice for subscription.",
        "expected_category": "billing",
    })
    messages = LlamaServerAdapter.build_messages(prompt)
    assert messages[0]["role"] == "system"
    assert "classifier" in messages[0]["content"]
    assert messages[1]["role"] == "user"
    assert "Charged twice" in messages[1]["content"]
    assert "ONLY JSON" in messages[1]["content"]


def test_plain_prompt_becomes_single_user_message():
    messages = LlamaServerAdapter.build_messages("just some text")
    assert messages == [{"role": "user", "content": "just some text"}]


def test_missing_fields_still_produce_two_messages():
    prompt = json.dumps({"ticket": "login broken"})
    messages = LlamaServerAdapter.build_messages(prompt)
    assert len(messages) == 2
    assert "login broken" in messages[1]["content"]
