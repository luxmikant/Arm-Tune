"""Arm Performix CLI installer — download and set up the binary on ARM64."""

from __future__ import annotations

import os
import stat
import subprocess
import tarfile
from pathlib import Path

import requests

PERFORMIX_CLI_URL = (
    "https://artifacts.tools.arm.com/arm-performix/cli/latest/"
    "ArmPerformix-cli-linux-arm64.tar.gz"
)
PERFORMIX_DIR = Path.home() / ".armtune" / "performix"
PERFORMIX_BIN = PERFORMIX_DIR / "ArmPerformix"


def is_performix_available() -> bool:
    """Check if Arm Performix CLI is installed and executable."""
    return PERFORMIX_BIN.exists() and os.access(PERFORMIX_BIN, os.X_OK)


def get_performix_path() -> Path:
    """Get the path to the Arm Performix CLI binary."""
    return PERFORMIX_BIN


def ensure_performix() -> Path:
    """Ensure Arm Performix CLI is installed. Downloads if missing."""
    if is_performix_available():
        return PERFORMIX_BIN

    PERFORMIX_DIR.mkdir(parents=True, exist_ok=True)

    archive_path = PERFORMIX_DIR / "ArmPerformix-cli-linux-arm64.tar.gz"

    try:
        _download(PERFORMIX_CLI_URL, archive_path)
        _extract(archive_path, PERFORMIX_DIR)
        archive_path.unlink(missing_ok=True)

        os.chmod(PERFORMIX_BIN, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)

        result = subprocess.run(
            [str(PERFORMIX_BIN), "--version"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            raise RuntimeError(f"Performix binary check failed: {result.stderr}")
    except Exception as e:
        raise RuntimeError(
            f"Failed to install Arm Performix CLI: {e}\n"
            "Manual install: download from https://developer.arm.com/servers-and-cloud-computing/"
            "arm-performix and extract to ~/.armtune/performix/"
        )

    return PERFORMIX_BIN


def _download(url: str, dest: Path) -> None:
    response = requests.get(url, stream=True, timeout=120)
    response.raise_for_status()
    with open(dest, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)


def _extract(archive: Path, dest: Path) -> None:
    with tarfile.open(archive, "r:gz") as tar:
        tar.extractall(path=dest)


__all__ = ["ensure_performix", "get_performix_path", "is_performix_available"]
