#!/usr/bin/env bash
# install-performix.sh — Download and install Arm Performix CLI on ARM64 Linux
set -euo pipefail

PERFORMIX_URL="https://artifacts.tools.arm.com/arm-performix/cli/latest/ArmPerformix-cli-linux-arm64.tar.gz"
INSTALL_DIR="${HOME}/.armtune/performix"
BINARY="${INSTALL_DIR}/ArmPerformix"

ARCH=$(uname -m)
if [ "${ARCH}" != "aarch64" ] && [ "${ARCH}" != "arm64" ]; then
    echo "Warning: Not running on ARM64 (detected: ${ARCH}). Arm Performix requires ARM64."
    echo "Continuing for CI compatibility but profiling will be unavailable."
    mkdir -p "${INSTALL_DIR}"
    echo '#!/usr/bin/env bash\necho "{\"status\": \"unavailable\", \"arch\": \"'"${ARCH}"'\"}"' > "${BINARY}"
    chmod +x "${BINARY}"
    exit 0
fi

echo "Installing Arm Performix CLI for ARM64..."

mkdir -p "${INSTALL_DIR}"

if command -v curl &> /dev/null; then
    curl -fsSL "${PERFORMIX_URL}" -o "${INSTALL_DIR}/ArmPerformix.tar.gz"
elif command -v wget &> /dev/null; then
    wget -q "${PERFORMIX_URL}" -O "${INSTALL_DIR}/ArmPerformix.tar.gz"
else
    echo "Error: curl or wget required."
    exit 1
fi

tar -xzf "${INSTALL_DIR}/ArmPerformix.tar.gz" -C "${INSTALL_DIR}"
rm -f "${INSTALL_DIR}/ArmPerformix.tar.gz"

chmod +x "${BINARY}" 2>/dev/null || true

if [ -x "${BINARY}" ]; then
    echo "Arm Performix CLI installed: ${BINARY}"
    "${BINARY}" --version 2>&1 || echo "(version check skipped — may need sudo for perf counters)"
else
    echo "Warning: Arm Performix binary not found after extraction."
    echo "Check contents of ${INSTALL_DIR}"
    ls -la "${INSTALL_DIR}"
fi
