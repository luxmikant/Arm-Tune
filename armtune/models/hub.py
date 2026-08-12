"""Hugging Face model hub connector.

Resolves a ``repo_id`` (+ optional quantization) into a local GGUF path,
with resumable downloads and caching under ``models/``.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

from huggingface_hub import hf_hub_download, list_repo_files

QUANT_PATTERN = re.compile(
    r"(?P<quant>Q[2-8](?:_[0-9]|_K(?:_[SLM])?)?|IQ[1-4]_[A-Z0-9]+|F16|F32|BF16)",
    re.IGNORECASE,
)


def quant_from_filename(filename: str) -> str:
    match = QUANT_PATTERN.search(filename)
    return match.group("quant").upper() if match else "unknown"


def list_gguf_models(repo_id: str, token: str | None = None) -> list[dict]:
    """List GGUF files in a Hugging Face repo with parsed quantization."""
    files = list_repo_files(repo_id, token=token)
    results = []
    for f in sorted(files):
        if not f.endswith(".gguf"):
            continue
        name = Path(f).name
        results.append(
            {
                "filename": f,
                "name": name,
                "quantization": quant_from_filename(name),
                "size_bytes": None,
            }
        )
    return results


def pull_model(
    repo_id: str,
    filename: str,
    cache_dir: str | Path = "models",
    token: str | None = None,
) -> Path:
    """Download one GGUF file into the local model cache and return its path."""
    cache_dir = Path(cache_dir) / repo_id.replace("/", "__")
    cache_dir.mkdir(parents=True, exist_ok=True)
    target = cache_dir / Path(filename).name
    if target.exists() and target.stat().st_size > 0:
        return target
    local = hf_hub_download(
        repo_id=repo_id,
        filename=filename,
        local_dir=cache_dir,
        local_dir_use_symlinks=False,
        token=token,
    )
    return Path(local)


def resolve_model(
    repo_id: str,
    quantization: str | None = None,
    cache_dir: str | Path = "models",
    token: str | None = None,
) -> tuple[Path, str]:
    """Resolve repo (+ optional quantization) to a local GGUF path.

    Returns ``(path, actual_quantization)``.
    """
    token = token or os.environ.get("HF_TOKEN")
    models = list_gguf_models(repo_id, token=token)
    if not models:
        raise ValueError(f"No GGUF files found in {repo_id}")

    if quantization:
        wanted = quantization.upper()
        match = next(
            (m for m in models if m["quantization"].upper() == wanted), None
        )
        if match is None:
            available = [m["quantization"] for m in models]
            raise ValueError(
                f"Quantization {quantization} not found in {repo_id}. "
                f"Available: {available}"
            )
    else:
        match = models[0]

    path = pull_model(repo_id, match["filename"], cache_dir=cache_dir, token=token)
    return path, match["quantization"]


__all__ = [
    "quant_from_filename",
    "list_gguf_models",
    "pull_model",
    "resolve_model",
]
