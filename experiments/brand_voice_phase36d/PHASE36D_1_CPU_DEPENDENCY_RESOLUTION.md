# Phase 36D.1 — VietVoice CPU dependency resolution

## Gate result

`CPU_PATH_NOT_VIABLE`

The requested CPU-only Torch dependency was installed only in the isolated Phase 36D venv. It resolves the first import failure, but a second undeclared dependency prevents the public VietVoice API from importing on the current Python 3.14 runtime. No model asset was downloaded and no inference ran.

## Step 1 — source audit

### Every Torch use

`vietvoicetts/core/tts_engine.py:7` is the only runtime Torch reference in the checked-out source:

```python
import torch
```

There are no `torch.` calls, tensor operations, CUDA checks, device transfers, model loads, or Torch utility calls anywhere in the Candidate 03 clone path. The import is unused.

### Actual inference path

- `vietvoicetts/core/model.py:32-45`, `ModelSessionManager._get_optimal_providers()`: obtains providers from `onnxruntime.get_available_providers()` and selects CUDA only when it is offered; otherwise it selects `CPUExecutionProvider`.
- `ModelSessionManager._load_models_from_file()`: reads `preprocess.onnx`, `transformer.onnx`, and `decode.onnx` from `model-bin.pt` and creates `onnxruntime.InferenceSession` for each.
- `vietvoicetts/core/tts_engine.py:_run_preprocess`, `_run_transformer_steps`, and `_run_decode`: call only `session.run(...)` on these ONNX sessions.
- `TTSEngine.synthesize()` is the reference-audio/reference-text clone path. It has no CUDA-only Torch operation.

Thus ONNX Runtime is the synthesis runtime, and a CPU execution provider remains the intended non-CUDA inference provider.

## Step 2 — approved CPU Torch installation

Installed only in `experiments/brand_voice_phase36d/.venv`:

- package: `torch==2.14.0+cpu`
- index: `https://download.pytorch.org/whl/cpu`
- main wheel download: `196,260,719` bytes (~187 MiB)
- small pure-Python support dependencies: filelock, fsspec, Jinja2, MarkupSafe, mpmath, networkx, setuptools, sympy

No CUDA package was installed. No main AIVoice environment or source tree was modified.

## Step 3 — actual runtime verification

The following imports independently succeed:

- `import torch`
- `import onnxruntime`

Observed versions/runtime:

```text
torch: 2.14.0+cpu
torch.version.cuda: None
torch.cuda.is_available(): False
onnxruntime: 1.29.0
available providers: AzureExecutionProvider, CPUExecutionProvider
```

The isolated venv is now `1.1G` on disk.

However, the required final check fails:

```bash
experiments/brand_voice_phase36d/.venv/bin/python -c "import vietvoicetts"
```

Failure:

```text
ModuleNotFoundError: No module named 'pyaudioop'
```

Why: on Python 3.14, `pydub.utils` first imports removed stdlib module `audioop`, then falls back to `pyaudioop`. The project declares `pydub` but does not declare `pyaudioop`, so its documented CPU installation cannot import on this runtime. `vietvoicetts/core/audio_processor.py` imports `pydub.AudioSegment` as part of public package import.

## Model-download gate

`model-bin.pt` was not downloaded. The expected 1,508,003,328-byte archive remains absent from `experiments/brand_voice_phase36d/model_cache/`.

The prepared `run_vietvoice_candidate03_poc.py` has no third-party source edit and would be suitable after a viable import environment exists. In the current approved dependency scope it cannot proceed, because it imports `vietvoicetts` and fails before model loading.

No audio was generated, no VieNeu process ran, and production remains untouched.
