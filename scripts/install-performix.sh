#!/usr/bin/env bash
# install-performix.sh — Download and install Arm Performix CLI on ARM64 Linux
set -euo pipefail

PERFORMIX_URL="https://artifacts.tools.arm.com/arm-performix/cli/latest/ArmPerformix-cli-linux-arm64.tar.gz"
INSTALL_DIR="${HOME}/.armtune/performix"

ARCH=$(uname -m)
if [ "${ARCH}" != "aarch64" ] && [ "${ARCH}" != "arm64" ]; then
    echo "Warning: Not running on ARM64 (detected: ${ARCH}). Skipping Arm Performix install."
    mkdir -p "${INSTALL_DIR}"
    exit 0
fi

echo "Installing Arm Performix CLI for ARM64..."
mkdir -p "${INSTALL_DIR}"

if command -v curl &> /dev/null; then
    curl -fsSL "${PERFORMIX_URL}" -o "${INSTALL_DIR}/arm-performix.tar.gz"
elif command -v wget &> /dev/null; then
    wget -q "${PERFORMIX_URL}" -O "${INSTALL_DIR}/arm-performix.tar.gz"
else
    echo "Error: curl or wget required."
    exit 1
fi

tar -xzf "${INSTALL_DIR}/arm-performix.tar.gz" -C "${INSTALL_DIR}"
rm -f "${INSTALL_DIR}/arm-performix.tar.gz"

# Find the Performix binary (may be named 'apx', 'ArmPerformix', etc.)
PERFORMIX_BIN=""
for candidate in "${INSTALL_DIR}/apx" "${INSTALL_DIR}/ArmPerformix" "${INSTALL_DIR}/arm-performix"; do
    if [ -f "${candidate}" ] && [ -x "${candidate}" ]; then
        PERFORMIX_BIN="${candidate}"
        break
    fi
done

# If not found by name, search for large executable files
if [ -z "${PERFORMIX_BIN}" ]; then
    PERFORMIX_BIN=$(find "${INSTALL_DIR}" -maxdepth 1 -type f -executable 2>/dev/null | head -1)
fi

# Ensure all binaries are executable
find "${INSTALL_DIR}" -maxdepth 1 -type f -exec chmod +x {} \; 2>/dev/null || true

if [ -n "${PERFORMIX_BIN}" ] && [ -x "${PERFORMIX_BIN}" ]; then
    echo "Arm Performix CLI found: ${PERFORMIX_BIN}"
    "${PERFORMIX_BIN}" --version 2>&1 || echo "(version check skipped — may need elevated permissions)"
else
    echo "Warning: Arm Performix binary not found after extraction."
    echo "Contents of ${INSTALL_DIR}:"
    ls -la "${INSTALL_DIR}"
fi
