# Phase 36D.3 — Python 3.12 compatibility environment gate

## Result

`READY_FOR_MODEL_DOWNLOAD`

The public VietVoice API imports cleanly in a separate Python 3.12 runtime and ONNX Runtime exposes `CPUExecutionProvider`. No model has been downloaded and no synthesis was invoked.

## Installation method

The Fedora package method was audited first. Fedora 44 officially provides `python3.12`, but system installation requires an interactive sudo password that is unavailable to this agent. The system Python was not changed.

The fallback is an isolated user-local official Python Build Standalone distribution:

- archive: `cpython-3.12.14+20260901-x86_64-unknown-linux-gnu-install_only_stripped.tar.gz`
- transfer size: 34,143,368 bytes
- installed runtime: `experiments/brand_voice_phase36d/python312/`
- executable: `experiments/brand_voice_phase36d/python312/bin/python3.12`
- version: Python 3.12.14
- `/usr/bin/python3` remains Python 3.14.7

## Fresh compatibility venv

- venv: `experiments/brand_voice_phase36d/.venv_py312`
- VietVoice checkout: existing `experiments/brand_voice_phase36d/VietVoice-TTS`
- checkout commit: `d4e8a22525437fc976ee9bc4dfd41ceb4b311248`
- install: documented editable `[cpu]` extra, then required undeclared CPU-only Torch

No CUDA package was installed.

## Runtime verification

```text
Python: 3.12.14
VietVoice: 0.1.0
Torch: 2.14.0+cpu
torch.version.cuda: None
torch.cuda.is_available(): False
ONNX Runtime: 1.29.0
ONNX providers: AzureExecutionProvider, CPUExecutionProvider
Public API: ModelConfig and TTSApi imported successfully
```

The verified public API import only referenced `ModelConfig` and `TTSApi`; it did not instantiate `ModelConfig`, because instantiation would auto-download the model archive.

## Disk usage

- Python 3.12 standalone runtime: 113 MiB
- new `.venv_py312`: 1.1 GiB
- VietVoice source checkout: 956 KiB
- new compatibility runtime + venv + checkout: approximately 1.21 GiB
- prior Phase 36D Python 3.14 venv remains unchanged at 1.1 GiB
- complete `experiments/brand_voice_phase36d/` directory: 2.2 GiB

## Model / production confirmation

- `model-bin.pt` is absent.
- No audio generation or VieNeu process ran.
- Candidate 03 assets were not touched.
- No production source, production dependency, main AIVoice `.venv`, or Fedora Python default was changed.
- The original prepared `run_vietvoice_candidate03_poc.py` can proceed from this new environment without third-party source edits after the next phase explicitly authorizes the model download.
