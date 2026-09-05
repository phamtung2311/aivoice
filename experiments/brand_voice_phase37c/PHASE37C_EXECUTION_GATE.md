# Phase 37C — VoxCPM2 Candidate 04 execution gate

## Decision

**Prepared for an approved temporary CUDA machine; not executable on the
current laptop.**  The local hardware exposes only Intel Iris Xe graphics and
no NVIDIA CUDA device.  No source checkout, environment, model download,
generation, listening clip, corpus, training run or production edit was made
by this phase.

## Model and legal gate

- Official source: `OpenBMB/VoxCPM`, pinned to
  `f772e498a45fbb5fb8e13fbf9b9c48be9fe33e69`.
- Official Voice Design checkpoint: `openbmb/VoxCPM2`, revision
  `32279effe8c19989596f05d353d1447f51d9e915`.
- The official model card lists Vietnamese (`vi`), Apache-2.0 and free
  commercial use.  It is a 2B model.
- The minimum pinned snapshot is 4,960,731,866 bytes (about 4.96 GB):
  `model.safetensors` (4,580,080,592 bytes), `audiovae.pth`
  (376,951,122 bytes), tokenizer and configuration files.  SHA-256 validation
  is locked for the two large model files in `provenance.json`.

## Exact one-shot contract

The prepared script performs **one** Voice Design generation only:

- Target text: `Hôm nay, chúng ta cùng đi qua một câu chuyện không quá ồn ào, nhưng đủ để khiến người nghe suy nghĩ lâu hơn một chút.`
- Voice Design description: stored verbatim in `voice_design.txt`.
- Exact model input: `(` + description + `)` + target.
- Fixed seed: `2040417`.  This controls the model RNG; CUDA/PyTorch does not
  promise bit-identical output across all driver and hardware combinations.
- Official design defaults: CFG 2.0 and 10 inference steps.
- `retry_badcase=False`, `retry_badcase_max_times=0`, `load_denoiser=False`,
  `denoise=False`, `normalize=False`, `streaming=False`.
- `optimize=False` is required because the upstream default warm-up would make
  an unrecorded second synthesis.  It is deliberately disabled.
- Output is one unmodified 32-bit float mono WAV, plus `metrics.json`.
  The script refuses to overwrite either output file.

Candidate 03, all user audio, corpus construction, training, comparison clips,
post-processing and production are outside this execution contract.

## Hardware classification and session estimate

| GPU class | Classification for this single short audition |
| --- | --- |
| RTX 4090 24 GB | SAFE |
| RTX 3090 24 GB | LIKELY |
| NVIDIA A10 24 GB | LIKELY |
| NVIDIA L4 24 GB | LIKELY |
| A100 40 GB | UNNECESSARY |

Use CUDA 12+, 24 GB VRAM, at least 16 GB RAM, and about 10–15 GB free disk.
The upstream project documents Python >=3.10 and CUDA >=12; Python 3.12 is the
prepared choice.  Peak VRAM and exact generation time have not been measured,
so the classifications are conservative operational estimates, not guarantees.
Expect a 30–60 minute booked session to cover setup, roughly 5 GB checkpoint
download (network-dependent), validation, one load and one output.

## Reproducible future run

Follow the instructions in `README.md` from this directory on the approved
GPU machine.  The final command runs
`scripts/run_candidate04.py` with the pinned local checkpoint.  It verifies
the checkpoint before load, requires `cuda:0`, uses `local_files_only=True`,
logs runtime/device/VRAM/RSS/RTF and audio duration/sample rate/peak/RMS/
clipping, then exits.

No execution is authorized or attempted until a suitable GPU environment is
available.
