"""Arm Performix output parser — converts CLI JSON output to models."""

from __future__ import annotations

import json

from .models import PerformixBottleneck, PerformixPerfCounters, PerformixProfile


def parse_performix_output(raw: str) -> PerformixProfile:
    """Parse Arm Performix JSON output into a PerformixProfile.

    Handles several possible output schemas since the CLI format
    may vary across versions.
    """
    if not raw or not raw.strip():
        return PerformixProfile()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return PerformixProfile()

    counters = _extract_counters(data)
    bottlenecks = _extract_bottlenecks(data)
    duration = data.get("duration", data.get("duration_seconds", 0.0))
    samples = data.get("samples", data.get("sample_count", 0))

    return PerformixProfile(
        duration_seconds=float(duration),
        sample_count=int(samples),
        counters=counters,
        bottlenecks=bottlenecks,
        raw_json=raw,
    )


def _extract_counters(data: dict) -> PerformixPerfCounters:
    """Extract performance counters from Performix JSON output.

    Supports multiple schema versions: nested under 'metrics', 'counters',
    'pmu', or at the top level.
    """
    node = data
    for key in ("metrics", "counters", "pmu", "performance"):
        if key in data and isinstance(data[key], dict):
            node = data[key]
            break

    return PerformixPerfCounters(
        instructions_per_cycle=_get_float(node, [
            "ipc", "instructions_per_cycle", "IPC",
        ]),
        cycles=_get_int(node, [
            "cycles", "CPU_CYCLES", "cpu_cycles",
        ]),
        instructions=_get_int(node, [
            "instructions", "INST_RETIRED", "inst_retired",
        ]),
        branch_mispredict_pct=_get_float(node, [
            "branch_mispredict_pct", "branch_misprediction_rate",
            "BR_MIS_PRED", "branch_miss_rate",
        ]),
        l1_dcache_miss_rate=_get_float(node, [
            "l1_dcache_miss_rate", "L1D_CACHE_REFILL",
            "l1d_cache_miss_pct",
        ]),
        l1_icache_miss_rate=_get_float(node, [
            "l1_icache_miss_rate", "L1I_CACHE_REFILL",
            "l1i_cache_miss_pct",
        ]),
        ll_cache_miss_rate=_get_float(node, [
            "ll_cache_miss_rate", "LL_CACHE_MISS",
            "l3_cache_miss_rate", "last_level_cache_miss_pct",
        ]),
        memory_read_bandwidth_mbs=_get_float(node, [
            "memory_read_bandwidth", "MEM_ACCESS_RD",
            "read_bandwidth_mb", "bus_read_bw",
        ]),
        memory_write_bandwidth_mbs=_get_float(node, [
            "memory_write_bandwidth", "MEM_ACCESS_WR",
            "write_bandwidth_mb", "bus_write_bw",
        ]),
        stall_frontend_pct=_get_float(node, [
            "stall_frontend", "STALL_FRONTEND",
            "frontend_bound_pct", "frontend_stall_pct",
        ]),
        stall_backend_pct=_get_float(node, [
            "stall_backend", "STALL_BACKEND",
            "backend_bound_pct", "backend_stall_pct",
        ]),
        simd_pct=_get_float(node, [
            "simd_pct", "SIMD_INST_RETIRED",
            "neon_pct", "sve_pct", "vector_pct",
        ]),
    )


def _extract_bottlenecks(data: dict) -> list[PerformixBottleneck]:
    """Extract bottleneck recommendations from Performix output."""
    results: list[PerformixBottleneck] = []

    for key in ("bottlenecks", "issues", "recommendations", "insights"):
        items = data.get(key, [])
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict):
                    results.append(PerformixBottleneck(
                        category=item.get("category", item.get("type", "")),
                        severity=item.get("severity", item.get("level", "")),
                        description=item.get("description", item.get("message", "")),
                        recommendation=item.get("recommendation", item.get("suggestion", "")),
                    ))
            if results:
                break

    return results


def _get_float(data: dict, keys: list[str]) -> float:
    for k in keys:
        v = data.get(k)
        if v is not None:
            try:
                return float(v)
            except (ValueError, TypeError):
                continue
    return 0.0


def _get_int(data: dict, keys: list[str]) -> int:
    for k in keys:
        v = data.get(k)
        if v is not None:
            try:
                return int(v)
            except (ValueError, TypeError):
                continue
    return 0


__all__ = ["parse_performix_output"]
