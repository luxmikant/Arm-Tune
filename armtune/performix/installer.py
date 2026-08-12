"""Arm Performix CLI installer — download and set up the binary on ARM64."""

from __future__ import annotations

import os
import stat
import subprocess
import tarfile
from pathlib import Path
from urllib.request import urlretrieve

PERFORMIX_CLI_URL = (
    "https://artifacts.tools.arm.com/arm-performix/cli/latest/"
    "ArmPerformix-cli-linux-arm64.tar.gz"
)
PERFORMIX_DIR = Path.home() / ".armtune" / "performix"

_POSSIBLE_BINARIES = ("apx", "ArmPerformix", "arm-performix")


def _find_performix_binary() -> Path | None:
    """Find the Performix binary in the install directory."""
    if not PERFORMIX_DIR.exists():
        return None
    for name in _POSSIBLE_BINARIES:
        path = PERFORMIX_DIR / name
        if path.exists() and os.access(path, os.X_OK):
            return path
    for entry in PERFORMIX_DIR.iterdir():
        if entry.is_file() and os.access(entry, os.X_OK):
            if "apx" in entry.name.lower() or "performix" in entry.name.lower():
                return entry
    return None


def is_performix_available() -> bool:
    """Check if Arm Performix CLI is installed and executable."""
    return _find_performix_binary() is not None


def get_performix_path() -> Path:
    """Get the path to the Arm Performix CLI binary."""
    bin_path = _find_performix_binary()
    if bin_path is None:
        raise FileNotFoundError(
            "Arm Performix CLI not found. Run ensure_performix() first."
        )
    return bin_path


def ensure_performix() -> Path:
    """Ensure Arm Performix CLI is installed. Downloads if missing."""
    existing = _find_performix_binary()
    if existing is not None:
        return existing

    PERFORMIX_DIR.mkdir(parents=True, exist_ok=True)
    archive_path = PERFORMIX_DIR / "ArmPerformix-cli-linux-arm64.tar.gz"

    try:
        urlretrieve(PERFORMIX_CLI_URL, archive_path)
        with tarfile.open(archive_path, "r:gz") as tar:
            tar.extractall(path=PERFORMIX_DIR)
        archive_path.unlink(missing_ok=True)

        for entry in PERFORMIX_DIR.iterdir():
            if entry.is_file() and not entry.name.endswith((".md", ".txt")):
                try:
                    os.chmod(entry, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
                except Exception:
                    pass

        bin_path = _find_performix_binary()
        if bin_path is None:
            raise RuntimeError(
                "Arm Performix binary not found after extraction. "
                f"Check contents of {PERFORMIX_DIR}"
            )

        result = subprocess.run(
            [str(bin_path), "--version"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Performix binary version check failed: {result.stderr}")

        return bin_path

    except Exception as e:
        raise RuntimeError(
            f"Failed to install Arm Performix CLI: {e}\n"
            "Manual install: download from https://developer.arm.com/servers-and-cloud-computing/"
            "arm-performix and extract to ~/.armtune/performix/"
        ) from e


__all__ = ["ensure_performix", "get_performix_path", "is_performix_available"]
