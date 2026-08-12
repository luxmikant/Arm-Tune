"""Configuration models for ArmTune Serve.

Profiles define the combination of model, runtime, and benchmark settings
for a single benchmark run. Objectives drive the recommendation engine.
"""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class Objective(str, Enum):
    LOW_LATENCY = "low-latency"
    HIGH_THROUGHPUT = "high-throughput"
    LOW_MEMORY = "low-memory"
    BALANCED = "balanced"


class QuantizationFormat(str, Enum):
    Q2_K = "Q2_K"
    Q2_K_L = "Q2_K_L"
    Q3_K_S = "Q3_K_S"
    Q3_K_M = "Q3_K_M"
    Q3_K_L = "Q3_K_L"
    Q4_0 = "Q4_0"
    Q4_1 = "Q4_1"
    Q4_K_S = "Q4_K_S"
    Q4_K_M = "Q4_K_M"
    Q5_K_S = "Q5_K_S"
    Q5_K_M = "Q5_K_M"
    Q6_K = "Q6_K"
    Q8_0 = "Q8_0"
    IQ4_NL = "IQ4_NL"
    IQ4_XS = "IQ4_XS"
    F16 = "F16"
    F32 = "F32"
    BF16 = "BF16"
    UNKNOWN = "UNKNOWN"


class ModelConfig(BaseModel):
    name: str
    family: str = ""
    repo_id: str = ""
    quantization: QuantizationFormat
    context_size: int = 2048
    batch_size: int = 512
    model_path: str | None = None
    gpu_layers: int = 0


class RuntimeConfig(BaseModel):
    threads: int = Field(default=4, ge=1)
    batch_threads: int = Field(default=0, ge=0)
    concurrency: int = Field(default=1, ge=1)
    runtime_backend: str = "auto"
    enable_prompt_cache: bool = False
    enable_mmap: bool = True
    enable_mlock: bool = False


class BenchmarkConfig(BaseModel):
    warmup_requests: int = 2
    measurement_requests: int = 10
    repetitions: int = Field(default=1, ge=1)
    max_tokens: int = 256
    temperature: float = 0.0
    seed: int = 42
    prompt_set: str = "support_tickets"


class PerformixConfig(BaseModel):
    enabled: bool = True
    sample_period_ms: int = 10
    collect_cache_metrics: bool = True
    collect_instruction_metrics: bool = True
    collect_memory_bandwidth: bool = True
    output_format: str = "json"


class Profile(BaseModel):
    name: str
    objective: Objective
    model: ModelConfig
    runtime: RuntimeConfig
    benchmark: BenchmarkConfig = Field(default_factory=BenchmarkConfig)
    performix: PerformixConfig = Field(default_factory=PerformixConfig)
    label: str = ""

    def model_post_init(self, __context: Any) -> None:
        if not self.label:
            self.label = self.name


def load_profile(path: Path | str) -> Profile:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Profile not found: {path}")
    content = path.read_text(encoding="utf-8")
    if path.suffix in {".yaml", ".yml"}:
        data = yaml.safe_load(content)
    elif path.suffix == ".json":
        data = json.loads(content)
    else:
        raise ValueError(f"Unsupported format: {path.suffix}")
    return Profile(**data)


def load_all_profiles(config_dir: Path | str = "configs") -> dict[str, Profile]:
    config_dir = Path(config_dir)
    if not config_dir.exists():
        return {}
    profiles: dict[str, Profile] = {}
    for path in sorted(config_dir.glob("*.yaml")):
        try:
            profile = load_profile(path)
            profiles[profile.name] = profile
        except Exception as e:
            print(f"Warning: skipping {path}: {e}")
    return profiles


__all__ = [
    "Objective",
    "QuantizationFormat",
    "ModelConfig",
    "RuntimeConfig",
    "BenchmarkConfig",
    "PerformixConfig",
    "Profile",
    "load_profile",
    "load_all_profiles",
]
