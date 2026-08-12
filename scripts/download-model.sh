#!/usr/bin/env bash
# download-model.sh — Download a GGUF model for CPU inference
set -euo pipefail

MODEL_DIR="${1:-models}"
MODEL_REPO="${2:-unsloth/Llama-3.2-1B-Instruct-GGUF}"
MODEL_FILE="${3:-Llama-3.2-1B-Instruct-Q4_K_M.gguf}"

mkdir -p "${MODEL_DIR}"

if [ -f "${MODEL_DIR}/${MODEL_FILE}" ]; then
    echo "Model already downloaded: ${MODEL_DIR}/${MODEL_FILE}"
    echo "${MODEL_DIR}/${MODEL_FILE}"
    exit 0
fi

echo "Downloading ${MODEL_REPO}/${MODEL_FILE}..."

if command -v huggingface-cli &> /dev/null; then
    huggingface-cli download "${MODEL_REPO}" "${MODEL_FILE}" --local-dir "${MODEL_DIR}" --local-dir-use-symlinks False
else
    BASE_URL="https://huggingface.co/${MODEL_REPO}/resolve/main/${MODEL_FILE}"
    if command -v curl &> /dev/null; then
        curl -fSL "${BASE_URL}" -o "${MODEL_DIR}/${MODEL_FILE}"
    elif command -v wget &> /dev/null; then
        wget -q "${BASE_URL}" -O "${MODEL_DIR}/${MODEL_FILE}"
    else
        echo "Error: curl or wget required."
        exit 1
    fi
fi

echo "${MODEL_DIR}/${MODEL_FILE}"
