#!/usr/bin/env bash
# build-llama-cpp.sh — Build llama.cpp for ARM64 with two variants:
#   1. arm-optimized: KleidiAI + -mcpu=native (Arm kernels: NEON/I8MM/SVE)
#   2. generic:       plain CPU build (baseline for comparison)
# Outputs binaries into llama.cpp/build-<variant>/bin/llama-server
set -euo pipefail

JOBS="${JOBS:-$(nproc)}"
LLAMA_TAG="${LLAMA_TAG:-master}"
WORK_DIR="${WORK_DIR:-.}"
BUILD_GENERIC="${BUILD_GENERIC:-1}"

cd "${WORK_DIR}"

if [ ! -d "llama.cpp" ]; then
    echo "Cloning llama.cpp (${LLAMA_TAG})..."
    git clone --depth 1 --branch "${LLAMA_TAG}" https://github.com/ggml-org/llama.cpp
fi

echo "=== Building arm-optimized variant (KleidiAI + native) ==="
cmake -S llama.cpp -B llama.cpp/build-arm-opt \
    -DCMAKE_BUILD_TYPE=Release \
    -DGGML_CPU_KLEIDIAI=ON \
    -DGGML_NATIVE=ON \
    -DBUILD_SHARED_LIBS=OFF \
    -DCMAKE_C_FLAGS="-mcpu=native" \
    -DCMAKE_CXX_FLAGS="-mcpu=native"
cmake --build llama.cpp/build-arm-opt --config Release -j "${JOBS}"

echo "=== Verifying arm-optimized binary ==="
ls -la llama.cpp/build-arm-opt/bin/llama-server
grep "GGML_CPU_KLEIDIAI" llama.cpp/build-arm-opt/CMakeCache.txt || echo "WARNING: GGML_CPU_KLEIDIAI not found in CMakeCache"
llama.cpp/build-arm-opt/bin/llama-server --version 2>&1 || true

if [ "${BUILD_GENERIC}" = "1" ]; then
    echo "=== Building generic baseline variant ==="
    cmake -S llama.cpp -B llama.cpp/build-generic \
        -DCMAKE_BUILD_TYPE=Release \
        -DBUILD_SHARED_LIBS=OFF
    cmake --build llama.cpp/build-generic --config Release -j "${JOBS}"
    ls -la llama.cpp/build-generic/bin/llama-server
fi

echo "=== Done ==="
echo "arm-optimized binary: llama.cpp/build-arm-opt/bin/llama-server"
if [ "${BUILD_GENERIC}" = "1" ]; then
    echo "generic binary:       llama.cpp/build-generic/bin/llama-server"
fi
