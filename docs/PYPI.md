# Publishing ArmTune Serve to PyPI

The project uses standard setuptools metadata and publishes through GitHub
Actions trusted publishing.

## Order matters — do this BEFORE creating the release

The publish workflow triggers on a GitHub Release. If the trusted publisher
does not exist on PyPI when the release is created, the upload fails with
`HTTPError: 400 Bad Request from https://upload.pypi.org/legacy/`.

### Step 1 — Configure trusted publishing first

For the very first release of `armtune-serve`, create a pending publisher first:

1. Create and verify a PyPI account at https://pypi.org/account/register/.
2. Enable two-factor authentication.
3. Open **Publishing** (pypi.org/manage/account/publishing/).
4. Choose **Add a new pending publisher** and fill in:
   - Project name: `armtune-serve`
   - Owner: `luxmikant`
   - Repository: `Arm-Tune`
   - Workflow name: `publish-pypi.yml`
   - Environment name: `pypi`
5. The pending publisher claims the name before any upload.

### Step 2 — Optional token fallback for first release

If trusted publishing is not available yet, add a repository secret:

- Name: `PYPI_API_TOKEN`
- Value: a PyPI API token created from your account settings

The workflow first tries trusted publishing. If that fails and
`armtune-serve` does not yet exist on PyPI, it retries with this token.
Use an account-scoped token so the first upload can create the project.

If the project name has already been claimed by someone else, the pending
publisher form will reject it. Pick a different name in `pyproject.toml`
before continuing.

### Step 3 — Create the GitHub environment

1. GitHub repository > **Settings > Environments**.
2. Create an environment named `pypi`.
3. Optionally add a required reviewer for release control.

### Step 4 — Release the version

1. Update `version` in `pyproject.toml`.
2. Update `CHANGELOG.md`.
3. Run tests, lint, build, and metadata check:

```bash
python -m pip install --upgrade build twine
pytest tests/ -q
ruff check armtune/ tests/
python -m build
python -m twine check dist/*
```

4. Commit the release changes.
5. Create and push an annotated tag:

```bash
git tag -a v0.1.0 -m "ArmTune Serve v0.1.0"
git push origin v0.1.0
```

6. On GitHub, create a Release for the tag (`v0.1.0`). Publishing that
   release triggers `publish-pypi.yml`.
7. Watch **Actions > Publish Python package**. The build job must pass
   `twine check`; the publish job exchanges the GitHub OIDC token with PyPI.
8. Verify from a clean environment:

```bash
python -m venv /tmp/armtune-check
source /tmp/armtune-check/bin/activate
pip install armtune-serve
armtune --version
```

## Troubleshooting

### Upload failed with 400 Bad Request

Trusted publishing and the fallback token were both unable to create/upload the
`armtune-serve` project.

1. Complete Step 1 above and verify all pending publisher fields match exactly.
2. If you use `PYPI_API_TOKEN`, make sure it is account-scoped.
3. Open the failed workflow run and click **Re-run failed jobs**.
4. No new release or tag is needed.

### Upload failed with 403 Forbidden

The trusted publisher exists but a field does not match. Compare the four
values on PyPI (owner, repository, workflow, environment) against
`publish-pypi.yml`. The workflow must run with the `pypi` environment.

### The name was taken

Edit `[project] name` in `pyproject.toml`, update the URLs and docs, and
start again at Step 1.

## TestPyPI dry run

Before the real release, test the build pipeline against TestPyPI:

```bash
python -m twine upload --repository testpypi dist/*
pip install --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple armtune-serve
```

## What PyPI provides

PyPI distributes the Python control plane and CLI. It intentionally does not
bundle llama.cpp binaries, Arm Performix, or model weights. Those are
platform-specific and are installed or downloaded by the documented setup
steps.
