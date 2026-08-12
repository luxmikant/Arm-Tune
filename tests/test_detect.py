"""Tests for hardware detection."""

from armtune.detect.models import CPUInfo, GPUInfo, HardwareInfo, MemoryInfo, NUMAInfo


def test_cpu_info_defaults():
    cpu = CPUInfo(architecture="aarch64")
    assert cpu.architecture == "aarch64"
    assert cpu.model_name == "unknown"
    assert cpu.physical_cores == 0


def test_hardware_info_is_arm64():
    hw = HardwareInfo(
        cpu=CPUInfo(architecture="aarch64", model_name="Neoverse N1"),
        memory=MemoryInfo(total_gb=16, available_gb=8, used_gb=8),
        numa=NUMAInfo(),
        gpu=GPUInfo(),
    )
    assert hw.is_arm64()
    assert not HardwareInfo(
        cpu=CPUInfo(architecture="x86_64"),
        memory=MemoryInfo(total_gb=8, available_gb=4, used_gb=4),
        numa=NUMAInfo(),
        gpu=GPUInfo(),
    ).is_arm64()


def test_hardware_info_to_dict():
    hw = HardwareInfo(
        cpu=CPUInfo(architecture="aarch64"),
        memory=MemoryInfo(total_gb=16, available_gb=8, used_gb=8),
        numa=NUMAInfo(),
        gpu=GPUInfo(),
    )
    d = hw.to_dict()
    assert d["cpu"]["architecture"] == "aarch64"
    assert d["memory"]["total_gb"] == 16.0
