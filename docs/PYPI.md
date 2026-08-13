# Publishing ArmTune Serve to PyPI

The project uses standard setuptools metadata and publishes through GitHub
Actions trusted publishing. No long-lived PyPI token is stored in GitHub.

## First-time PyPI setup

1. Create and verify a PyPI account.
2. Enable two-factor authentication.
3. Confirm that the project name `armtune-serve` is available.
4. On PyPI, open **Publishing** and add a trusted publisher:
   - Owner: `luxmikant`
   - Repository: `Arm-Tune`
   - Workflow: `publish-pypi.yml`
   - Environment: `pypi`
5. In GitHub, create an environment named `pypi` under repository settings.
6. Optionally add an approval rule to the environment for release control.

## Validate locally

```bash
python -m pip install --upgrade build twine
python -m build
python -m twine check dist/*
```

The build should produce:

```text
dist/armtune_serve-<version>.tar.gz
```

## TestPyPI first

```bash
python -m twine upload --repository testpypi dist/*
  --extra-index-url https://pypi.org/simple armtune-serve
```

## Release a version

1. Update `version` in `pyproject.toml`.
2. Update `CHANGELOG.md`.
3. Run tests, lint, build, and `twine check`.
4. Commit the release changes.
5. Create and push an annotated tag:

```bash
```

6. The `publish-pypi.yml` workflow builds and uploads the package.
7. Verify the release from a clean environment:

```bash
python -m venv /tmp/armtune-check
source /tmp/armtune-check/bin/activate
pip install armtune-serve
armtune --version
```

## What PyPI provides

PyPI distributes the Python control plane and CLI. It intentionally does not
bundle llama.cpp binaries, Arm Performix, or model weights. Those are
platform-specific and are installed or downloaded by the documented setup
steps.
