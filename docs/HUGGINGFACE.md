# Publishing the ArmTune model repository to Hugging Face

The target repository is:

```text
https://huggingface.co/lshar/ARM-TUNE-CPU-INFERENCE-OPT
```

The repository should contain a model card and, only if you have permission to
redistribute it, the GGUF model artifacts. Do not upload a gated model or a
base model under a license that does not allow redistribution.

## One-time setup

### 1. Install Git Xet for large files

```bash
git xet install
```

### 2. Authenticate (password auth is no longer supported)

Hugging Face disabled HTTPS password authentication. Use one of the two
methods below.

#### Option A — User access token (simplest)

1. Create a token at https://huggingface.co/settings/tokens with **write**
   scope.
2. Login once so the CLI stores the token:

```bash
hf auth login
# or
huggingface-cli login
```

3. Configure Git to remember the credential:

```bash
git config --global credential.helper store
```

4. The next `git push` will prompt for a username and password. Enter your
   Hugging Face username and paste the **token** as the password. It is
   stored for future pushes.

#### Option B — SSH key (no token in Git)

1. Generate a key if you do not have one:

```bash
ssh-keygen -t ed25519 -C "armtune@example.com"
```

2. Add the public key (`~/.ssh/id_ed25519.pub`) at
   https://huggingface.co/settings/keys.
3. Point the cloned repository at the SSH remote:

```bash
git remote set-url origin git@hf.co:lshar/ARM-TUNE-CPU-INFERENCE-OPT.git
git push
```

Never commit the token or the key to this repository.

## Publish the prepared model card

```bash
git clone https://huggingface.co/lshar/ARM-TUNE-CPU-INFERENCE-OPT
cd ARM-TUNE-CPU-INFERENCE-OPT

# Copy the prepared card from the GitHub checkout.
cp ../huggingface/README.md README.md

# Copy only permitted model artifacts, for example:
# cp /path/to/Llama-3.2-1B-Instruct-Q4_K_M.gguf .

git add README.md *.gguf
git commit -m "docs: add ArmTune CPU inference model card"
git push
```

On Windows PowerShell:

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
