"""Hardware detection implementation — reads /proc, lscpu, psutil."""

from __future__ import annotations

import platform
import shutil
import socket
import subprocess
from pathlib import Path

import psutil

from .models import CPUInfo, GPUInfo, HardwareInfo, MemoryInfo, NUMAInfo


def _read_file(path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def _parse_cpu_from_cpuinfo(cpuinfo: str) -> tuple[str, list[str]]:
    model_name = "unknown"
    features: list[str] = []
    for line in cpuinfo.splitlines():
        line = line.strip()
        if line.startswith("model name") or line.startswith("Processor"):
            try:
                model_name = line.split(":", 1)[1].strip()
            except Exception:
                pass
        elif line.startswith("Features") or line.startswith("flags"):
            try:
                features = line.split(":", 1)[1].strip().split()
            except Exception:
                pass
    return model_name, features


def _detect_numa() -> NUMAInfo:
    try:
        if shutil.which("lscpu"):
            result = subprocess.run(["lscpu"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                out = result.stdout
                numa_nodes = 1
                cores: list[int] = []
                for line in out.splitlines():
                    if "NUMA node(s):" in line:
                        try:
                            numa_nodes = int(line.split(":")[1].strip())
                        except Exception:
                            pass
                    elif "CPU(s) per NUMA node:" in line or "CPU(s) per NUMA node" in line:
                        try:
                            cores.append(int(line.split(":")[1].strip()))
                        except Exception:
                            pass
                distances: list[list[int]] = []
                return NUMAInfo(numa_nodes=numa_nodes, cores_per_node=cores, node_distances=distances)
    except Exception:
        pass
    return NUMAInfo()


def detect_hardware() -> HardwareInfo:
    arch = platform.machine()
    model_name = "unknown"
    features: list[str] = []

    cpuinfo_text = _read_file("/proc/cpuinfo")
    if cpuinfo_text:
        model_name, features = _parse_cpu_from_cpuinfo(cpuinfo_text)

    physical_cores = psutil.cpu_count(logical=False) or 1
    logical_cores = psutil.cpu_count(logical=True) or 1

    cpu_freq = psutil.cpu_freq()
    frequency_mhz = cpu_freq.current if cpu_freq else None

    vendor = "arm" if ("aes" in features or arch == "aarch64") else "unknown"

    vm = psutil.virtual_memory()
    swap = psutil.swap_memory()

    memory = MemoryInfo(
        total_gb=round(vm.total / (1024**3), 2),
        available_gb=round(vm.available / (1024**3), 2),
        used_gb=round(vm.used / (1024**3), 2),
        swap_total_gb=round(swap.total / (1024**3), 2),
    )

    numa = _detect_numa()
    gpu = GPUInfo()

    os_release = ""
    for path in ("/etc/os-release", "/etc/lsb-release"):
        content = _read_file(path)
        if content:
            for line in content.splitlines():
                if line.startswith("PRETTY_NAME="):
                    os_release = line.split("=", 1)[1].strip('"')
                    break
        if os_release:
            break

    return HardwareInfo(
        cpu=CPUInfo(
            architecture=arch,
            model_name=model_name,
            vendor=vendor,
            physical_cores=physical_cores,
            logical_cores=logical_cores,
            frequency_mhz=frequency_mhz,
            features=features,
        ),
        memory=memory,
        numa=numa,
        gpu=gpu,
        hostname=socket.gethostname(),
        kernel=platform.release(),
        os_release=os_release or platform.platform(),
    )


get_hardware_info = detect_hardware

__all__ = ["detect_hardware", "get_hardware_info"]
