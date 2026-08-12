"""Tests for config loading."""

from armtune.config import Objective, Profile, QuantizationFormat


def test_objective_enum():
    assert Objective.LOW_LATENCY.value == "low-latency"
    assert Objective.HIGH_THROUGHPUT.value == "high-throughput"
    assert Objective.LOW_MEMORY.value == "low-memory"
    assert Objective.BALANCED.value == "balanced"


def test_quantization_enum():
    assert QuantizationFormat.Q4_K_M.value == "Q4_K_M"
    assert QuantizationFormat.Q8_0.value == "Q8_0"


def test_profile_defaults():
    profile = Profile(
        name="test",
        objective=Objective.BALANCED,
        model={
            "name": "test-model",
            "quantization": "Q4_K_M",
        },  # type: ignore[arg-type]
        runtime={
            "threads": 4,
            "concurrency": 1,
        },  # type: ignore[arg-type]
    )
    assert profile.name == "test"
    assert profile.objective == Objective.BALANCED
    assert profile.runtime.threads == 4
