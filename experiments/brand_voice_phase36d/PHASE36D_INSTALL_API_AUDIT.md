# Phase 36D — install/API audit stop report

## Result

**STOPPED before model download and before any generation.**

The installed implementation materially contradicts the documented CPU install path. This PoC must not continue by silently changing dependencies or editing third-party source.

## Isolated install

- repository: `experiments/brand_voice_phase36d/VietVoice-TTS`
- commit: `d4e8a22525437fc976ee9bc4dfd41ceb4b311248`
- virtual environment: `experiments/brand_voice_phase36d/.venv`
- installed package version: `vietvoicetts==0.1.0` (editable)
- installed CPU runtime: `onnxruntime==1.29.0`

## Expected minimal model asset

The installed default URL resolves to a single archive:

- `model-bin.pt`
- exact HTTP content length: `1,508,003,328` bytes (~1.41 GiB)
- intended cache location: `experiments/brand_voice_phase36d/model_cache/model-bin.pt`

It was **not downloaded**.

## Verified source API

The source implements the reference-clone interface:

```python
api.synthesize_to_file(
    text,
    output_path,
    reference_audio=reference_wav,
    reference_text=exact_reference_transcript,
)
```

It validates that `reference_audio` and `reference_text` are supplied together, loads audio as mono/24 kHz, and hands them to ONNX Runtime. It selects CUDA if available and otherwise `CPUExecutionProvider`. Installed `ModelConfig` defaults are 24 kHz, 32 NFE steps, fuse step 1, speed 1.0, seed 9527, 15-second maximum chunk duration, and 0.1-second multi-chunk crossfade.

The prepared, unrendered target is:

`Một câu chuyện rõ ràng cần được kể liền mạch, có điểm nhấn đúng chỗ.`

It is shorter than the Phase 36B target because the 6.96-second canonical reference plus that earlier text exceeds the installed 15-second one-chunk limit.

## Blocking implementation contradiction

The CPU extra in `pyproject.toml` installs ONNX Runtime but does **not** declare Torch. Yet `vietvoicetts/core/tts_engine.py` unconditionally executes `import torch` during package import, despite this path using ONNX Runtime.

Observed clean-environment command:

```bash
experiments/brand_voice_phase36d/.venv/bin/python -c "import vietvoicetts, onnxruntime"
```

Observed result:

```text
ModuleNotFoundError: No module named 'torch'
```

Therefore the advertised isolated CPU installation cannot import its own public API. Installing undeclared CPU Torch or modifying the checkout would be a local workaround, not the audited documented CPU path. Per Phase 36D instruction, neither was done.

## Frozen identity / production confirmation

- Candidate 03 reference was not copied, converted, or modified.
- No user voice was accessed.
- No model asset was downloaded.
- No VietVoice output WAV or audition was produced.
- No VieNeu control was generated or changed.
- Production code, dependencies, and the main AIVoice `.venv` remain untouched.

## Files changed

- `experiments/brand_voice_phase36d/VietVoice-TTS/` — isolated shallow source checkout.
- `experiments/brand_voice_phase36d/.venv/` — isolated dependency environment.
- `experiments/brand_voice_phase36d/run_vietvoice_candidate03_poc.py` — prepared but not run; it has a no-overwrite guard and uses the frozen canonical reference.
- `experiments/brand_voice_phase36d/PHASE36D_INSTALL_API_AUDIT.md` — this report.
