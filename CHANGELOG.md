# Changelog

All notable changes to ArmTune Serve are documented here.

## [Unreleased]

- Improve Performix command discovery using captured `apx --help` output.
- Add persistent Arm server validation for NUMA and affinity experiments.
- Add optional CPU-GPU measurement backend.

## [0.1.0] - 2026-08-13

- Initial public Arm64 inference optimization toolkit.
- Hardware capability detection for Arm Linux systems.
- llama.cpp and llama-server runtime adapters.
- Hugging Face GGUF model discovery and download.
- Arm Performix integration and transparent profiling status.
- TTFT, tokens/sec, P50/P95/P99, queue, RSS, and quality metrics.
- Thread, concurrency, and quantization benchmark sweeps.
- Quality-gated recommendation engine.
- JSON, CSV, Markdown, and chart reports.
- Gradio dashboard.
- Native Arm64 GitHub Actions workflows.
