"""Tests for runtime factory selection (offline)."""

import os
from unittest.mock import patch

from armtune.config import Objective, Profile
from armtune.runtime.factory import build_adapter_factory, llama_server_available
from armtune.runtime.llama_server import LlamaServerAdapter
from armtune.runtime.mock import MockAdapter


def _profile() -> Profile:
    return Profile(
        name="t",
        objective=Objective.BALANCED,
        model={"name": "m", "quantization": "Q4_K_M"},
        runtime={"threads": 1},
    )


def _reset_env(env: dict | None):
    for key in ("ARMTUNE_LLAMA_SERVER", "PATH"):
        if key in env:
            os.environ[key] = env[key]
        else:
            os.environ.pop(key, None)


def test_env_var_selects_llama_server():
    saved = dict(os.environ)
    try:
        os.environ["ARMTUNE_LLAMA_SERVER"] = "/opt/llama.cpp/build/bin/llama-server"
        with patch("armtune.runtime.factory.shutil.which", return_value=None):
            assert llama_server_available()
            factory = build_adapter_factory("auto")
            adapter = factory(_profile())
            assert isinstance(adapter, LlamaServerAdapter)
            assert adapter._binary == "/opt/llama.cpp/build/bin/llama-server"
    finally:
        _reset_env(saved)


def test_no_binary_no_lib_selects_mock():
    saved = dict(os.environ)
    try:
        os.environ.pop("ARMTUNE_LLAMA_SERVER", None)
        with (
            patch("armtune.runtime.factory.shutil.which", return_value=None),
            patch("importlib.util.find_spec", return_value=None),
        ):
            assert not llama_server_available()
            factory = build_adapter_factory("auto")
            assert isinstance(factory(_profile()), MockAdapter)
    finally:
        _reset_env(saved)
