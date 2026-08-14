"""Hugging Face model hub connector.

Resolves a ``repo_id`` (+ optional quantization) into a local GGUF path,
with resumable downloads and caching under ``models/``. Also provides model
search and model-card metadata for UI surfaces (dashboard, console).
"""

from __future__ import annotations

import os
import re
import time
from pathlib import Path

from huggingface_hub import hf_hub_download, list_repo_files

try:
    from huggingface_hub import list_models, list_repo_tree, model_info
except ImportError:  # pragma: no cover - older huggingface_hub
    list_models = None  # type: ignore[assignment]
    list_repo_tree = None  # type: ignore[assignment]
    model_info = None  # type: ignore[assignment]

QUANT_PATTERN = re.compile(
    r"(?P<quant>Q[2-8](?:_[0-9]|_K(?:_[SLM])?)?|IQ[1-4]_[A-Z0-9]+|F16|F32|BF16)",
    re.IGNORECASE,
)

_tree_cache: dict[tuple[str, int], tuple[float, list[dict]]] = {}
_TREE_TTL_SECONDS = 300


def quant_from_filename(filename: str) -> str:
    match = QUANT_PATTERN.search(filename)
    return match.group("quant").upper() if match else "unknown"


def _repo_tree(repo_id: str, token: str | None = None) -> list[dict]:
    """Cached recursive repo file listing including sizes.

    Returns list of ``{"path": str, "size": int | None}``.
    """
    cache_key = (repo_id, 1 if token else 0)
    cached = _tree_cache.get(cache_key)
    if cached and (time.time() - cached[0]) < _TREE_TTL_SECONDS:
        return cached[1]

    entries: list[dict] = []
    if list_repo_tree is not None:
        try:
            for item in list_repo_tree(repo_id, recursive=True, token=token):
                size = getattr(item, "size", None)
                entries.append(
                    {"path": getattr(item, "path", ""), "size": size}
                )
        except Exception:
            entries = []
    if not entries:
        for path in list_repo_files(repo_id, token=token):
            entries.append({"path": path, "size": None})

    _tree_cache[cache_key] = (time.time(), entries)
    return entries


def list_gguf_models(repo_id: str, token: str | None = None) -> list[dict]:
    """List GGUF files in a Hugging Face repo with parsed quantization and size."""
    entries = _repo_tree(repo_id, token=token)
    results = []
    for entry in sorted(entries, key=lambda e: e["path"]):
        f = entry["path"]
        if not f.endswith(".gguf"):
            continue
        name = Path(f).name
        results.append(
            {
                "filename": f,
                "name": name,
                "quantization": quant_from_filename(name),
                "size_bytes": entry.get("size"),
            }
        )
    return results


def search_models(
    query: str,
    limit: int = 10,
    token: str | None = None,
) -> list[dict]:
    """Search Hugging Face for models matching a query.

    Returns list of ``{"repo_id", "downloads", "likes", "tags", "updated"}``.
    """
    if list_models is None:
        return []
    try:
        raw = list(list_models(search=query, limit=limit, token=token))
    except Exception:
        return []
    results = []
    for m in raw:
        results.append(
            {
                "repo_id": getattr(m, "id", ""),
                "downloads": int(getattr(m, "downloads", 0) or 0),
                "likes": int(getattr(m, "likes", 0) or 0),
                "tags": [str(t) for t in (getattr(m, "tags", None) or [])][:8],
                "updated": str(getattr(m, "last_modified", "") or ""),
            }
        )
    return results


def get_model_card(repo_id: str, token: str | None = None) -> dict:
    """Fetch model-card metadata for a repo.

    Returns ``{"license", "tags", "downloads", "likes", "pipeline_tag",
    "created", "card_text"}``. Never raises; missing fields default to None.
    """
    card: dict = {
        "license": None,
        "tags": [],
        "downloads": None,
        "likes": None,
        "pipeline_tag": None,
        "created": None,
        "card_text": "",
    }
    if model_info is None:
        return card
    try:
        info = model_info(repo_id, token=token, files_metadata=False)
        card_data = getattr(info, "card_data", None) or {}
        if isinstance(card_data, dict):
            card["license"] = card_data.get("license")
            tags = card_data.get("tags")
            if isinstance(tags, list):
                card["tags"] = [str(t) for t in tags][:12]
            card["pipeline_tag"] = card_data.get("pipeline_tag")
        card["downloads"] = int(getattr(info, "downloads", 0) or 0)
        card["likes"] = int(getattr(info, "likes", 0) or 0)
        card["created"] = str(getattr(info, "created_at", "") or "")
        card_text = getattr(info, "card_text", None) or ""
        card["card_text"] = card_text[:4000]
    except Exception:
        pass
    return card


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


def human_size(size_bytes: int | None) -> str:
    """Format a byte count for UI display."""
    if not size_bytes:
        return "?"
    value = float(size_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} {unit}"
        value /= 1024
    return f"{size_bytes} B"


__all__ = [
    "quant_from_filename",
    "list_gguf_models",
    "search_models",
    "get_model_card",
    "pull_model",
    "resolve_model",
    "human_size",
]
