"""Arm Performix integration — download, profile, parse hardware counters."""

from .installer import ensure_performix, get_performix_path, is_performix_available
from .models import PerformixBottleneck, PerformixPerfCounters, PerformixProfile
from .profiler import attach_profile, profile_process, run_performix_sample

__all__ = [
    "ensure_performix",
    "get_performix_path",
    "is_performix_available",
    "PerformixProfile",
    "PerformixPerfCounters",
    "PerformixBottleneck",
    "attach_profile",
    "profile_process",
    "run_performix_sample",
]
