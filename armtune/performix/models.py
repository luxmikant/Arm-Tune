"""Data models for Arm Performix profiling results."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PerformixPerfCounters(BaseModel):
    """Performance counter metrics from Arm Performix."""

    instructions_per_cycle: float = 0.0
    cycles: int = 0
    instructions: int = 0
    branch_mispredict_pct: float = 0.0
    l1_dcache_miss_rate: float = 0.0
    l1_icache_miss_rate: float = 0.0
    ll_cache_miss_rate: float = 0.0
    memory_read_bandwidth_mbs: float = 0.0
    memory_write_bandwidth_mbs: float = 0.0
    stall_frontend_pct: float = 0.0
    stall_backend_pct: float = 0.0
    simd_pct: float = 0.0


class PerformixBottleneck(BaseModel):
    """A bottleneck identified by Performix."""

    category: str = ""
    severity: str = ""
    description: str = ""
    recommendation: str = ""


class PerformixProfile(BaseModel):
    """Complete Arm Performix profile for one run."""

    duration_seconds: float = 0.0
    sample_count: int = 0
    counters: PerformixPerfCounters = Field(default_factory=PerformixPerfCounters)
    bottlenecks: list[PerformixBottleneck] = Field(default_factory=list)
    raw_json: str = ""

    def is_empty(self) -> bool:
        return self.sample_count == 0
