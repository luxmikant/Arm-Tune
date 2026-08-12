"""Tests for the Hugging Face connector (no network)."""

from armtune.models.hub import quant_from_filename


def test_quant_from_filename_k_quants():
    assert quant_from_filename("Llama-3.2-1B-Instruct-Q4_K_M.gguf") == "Q4_K_M"
    assert quant_from_filename("model-Q5_K_S.gguf") == "Q5_K_S"
    assert quant_from_filename("model-Q8_0.gguf") == "Q8_0"


def test_quant_from_filename_simple_quants():
    assert quant_from_filename("dolphin-2.9.4-llama3.1-8b-Q4_0.gguf") == "Q4_0"
    assert quant_from_filename("model-Q2_K.gguf") == "Q2_K"


def test_quant_from_filename_iq_and_f16():
    assert quant_from_filename("model-IQ4_XS.gguf") == "IQ4_XS"
    assert quant_from_filename("model-F16.gguf") == "F16"
    assert quant_from_filename("model-BF16.gguf") == "BF16"


def test_quant_from_filename_unknown():
    assert quant_from_filename("model-weights.gguf") == "unknown"
    assert quant_from_filename("plainfile.gguf") == "unknown"


def test_quant_case_insensitive():
    assert quant_from_filename("model-q4_k_m.gguf") == "Q4_K_M"
