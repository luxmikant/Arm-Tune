# Contributing to ArmTune Serve

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,dashboard]"
pytest tests/ -q
ruff check armtune/ tests/
```

Windows is supported for unit tests and dashboard development. Real inference
benchmarks must run on Arm64 Linux.

## Changes that are especially useful

- Reproducible benchmark results from Graviton, Cobalt, Axion, or Ampere.
- Validated Arm Performix output and parser improvements.
- New llama.cpp runtime flags backed by measurements.
- Quality datasets and scoring improvements for structured workloads.
- Documentation that helps a first-time Arm developer.

## Pull request expectations

- Explain the user or engineering problem.
- Include tests for parsing, scoring, ranking, or data transformations.
- Do not commit GGUF model files or benchmark caches.
- Include the CPU model, runtime commit, and exact command for performance claims.
- Keep unrelated formatting changes out of the pull request.

## Performance claims

Performance results must state:

- hardware and operating system;
- model and quantization;
- llama.cpp commit and build flags;
- thread, batch, context, and concurrency settings;
- warmup, request count, seed, and prompt set;
- whether Arm Performix captured the inference process.
