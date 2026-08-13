# Publishing the ArmTune model repository to Hugging Face

The target repository is:

```text
https://huggingface.co/lshar/ARM-TUNE-CPU-INFERENCE-OPT
```

The repository should contain a model card and, only if you have permission to
redistribute it, the GGUF model artifacts. Do not upload a gated model or a
base model under a license that does not allow redistribution.

## One-time setup

Install Git Xet for large files:

```bash
git xet install
```

Authenticate with Hugging Face using one of:

```bash
huggingface-cli login
# or
hf auth login
```

Use a write-enabled token. Never put the token in this repository.

## Publish the prepared model card

```bash
cd ARM-TUNE-CPU-INFERENCE-OPT

# Copy the prepared card from the GitHub checkout.
cp ../huggingface/README.md README.md

# Copy only permitted model artifacts, for example:
# cp /path/to/Llama-3.2-1B-Instruct-Q4_K_M.gguf .

git add README.md *.gguf
git commit -m "docs: add ArmTune CPU inference model card"
git push
```

On Windows PowerShell, replace the copy command with:

```powershell
Copy-Item ..\huggingface\README.md .\README.md -Force
git add README.md *.gguf
git commit -m "docs: add ArmTune CPU inference model card"
git push
```

## What to fill before publishing

Replace every `<fill after benchmark>` field in the card with the actual
Arm64 artifact values. Include the hardware, model file SHA, base model license,
runtime commit, and benchmark command. Do not publish invented performance
numbers.
