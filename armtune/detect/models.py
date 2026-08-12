"""Hardware information data models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CPUInfo(BaseModel):
    architecture: str
    model_name: str = "unknown"
    vendor: str = "unknown"
    physical_cores: int = 0
    logical_cores: int = 0
    frequency_mhz: float | None = None
    features: list[str] = Field(default_factory=list)
    implementer: str = ""
    variant: str = ""


class MemoryInfo(BaseModel):
    total_gb: float
    available_gb: float
    used_gb: float
    swap_total_gb: float = 0.0
    page_size_kb: int = 4


class NUMAInfo(BaseModel):
    numa_nodes: int = 1
    cores_per_node: list[int] = Field(default_factory=list)
    node_distances: list[list[int]] = Field(default_factory=list)


class GPUInfo(BaseModel):
    available: bool = False
    devices: list[dict] = Field(default_factory=list)


class HardwareInfo(BaseModel):
    cpu: CPUInfo
    memory: MemoryInfo
    numa: NUMAInfo
    gpu: GPUInfo
    hostname: str = "unknown"
    kernel: str = "unknown"
    os_release: str = "unknown"

    def is_arm64(self) -> bool:
        return self.cpu.architecture in {"aarch64", "arm64"}

    def to_dict(self) -> dict:
        return self.model_dump()
