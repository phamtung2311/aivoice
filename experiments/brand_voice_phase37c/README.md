# Phase 37C — Candidate 04 single-audition package

## Status

Prepared only.  No model, source checkout, Python environment, GPU rental or
audio output exists in this directory.  This laptop has no NVIDIA CUDA device;
do **not** run this package locally.

The package is intentionally locked to one raw Candidate 04 audition.  It does
not use Candidate 03 or a user recording, creates no corpus and does not alter
production.

## Pinned provenance

| Surface | Pin |
| --- | --- |
| Official source | `https://github.com/OpenBMB/VoxCPM.git` |
| Audited source commit | `f772e498a45fbb5fb8e13fbf9b9c48be9fe33e69` |
| Latest official release observed | `2.0.3` / `19b6bf7590025418821a86dcb817504e0ad7e5df` |
| Official checkpoint | `openbmb/VoxCPM2` |
| Audited checkpoint revision | `32279effe8c19989596f05d353d1447f51d9e915` |
| Code and weights licence | Apache-2.0 |
| Commercial statement | Official model card says Apache-2.0 / free for commercial use. |

The future run must download the checkpoint at its listed revision and validate
the two large files against `provenance.json` before loading anything.

## Required temporary hardware

- NVIDIA CUDA 12+ driver/runtime; use an explicit `cuda:0` device.
- **24 GB VRAM is the practical target** for this first run.  A 3090, 4090,
  A10 or L4 is likely suitable; A100 40 GB is unnecessary for one short
  audition.  A 16 GB card is not selected because upstream only documents
  16 GB as the lower training prerequisite and gives no reliable peak-VRAM
  figure for this model.
- 16 GB system RAM minimum and 10–15 GB free disk for the isolated venv,
  source, approximately 4.96 GB checkpoint and cache.
- Python 3.12 is preferred.  The official project requires Python >=3.10;
  its last tagged release documented `<3.13`.

Do not use the laptop's Iris Xe as a substitute.

## One-time future procedure

Run these commands only on the temporary CUDA machine, from the directory
containing this package.  They are instructions, not commands run by this
phase.

```bash
git clone https://github.com/OpenBMB/VoxCPM.git source
git -C source checkout --detach f772e498a45fbb5fb8e13fbf9b9c48be9fe33e69
python3.12 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install torch==2.5.1+cu124 torchaudio==2.5.1+cu124 --index-url https://download.pytorch.org/whl/cu124
.venv/bin/python -m pip install -e source
.venv/bin/hf download openbmb/VoxCPM2 --revision 32279effe8c19989596f05d353d1447f51d9e915 --local-dir model
CUDA_VISIBLE_DEVICES=0 .venv/bin/python scripts/run_candidate04.py --model-dir model --output-dir output
```

Before the final command, verify that `nvidia-smi` reports an NVIDIA CUDA GPU
and that the source checkout is detached at the audited commit.  The script
validates the primary checkpoint hashes and refuses to use the Hub: it passes a
local directory and `local_files_only=True` to VoxCPM.

`optimize=False` is deliberate: upstream's default `optimize=True` performs an
unsaved warm-up synthesis.  Disabling it guarantees this phase makes exactly
one model generation, the audition itself.  The denoiser is disabled because
Voice Design has no reference audio and Phase 37C requires raw output.  The
bad-case retry is disabled so an internal retry cannot create a second take.

## Output contract

On success only these generated artifacts are expected:

- `output/candidate04_raw.wav` — 32-bit float WAV containing the unmodified
  model waveform.
- `output/metrics.json` — reproducibility/runtime/audio measurements.

The script does not perform denoising, EQ, compression, loudness normalization,
silence trimming, pitch/formant work or speed editing.  It stops after writing
the one WAV and metrics.  No second candidate, comparison, corpus or training
is authorized.

## Listening gate

The user alone decides whether this one voice can become the podcast identity:

1. Vietnamese pronunciation correct?
2. Continuous, natural phrasing?
3. One credible person rather than a preset?
4. Warm/deep/grounded enough for a podcast?
5. Calm authority without commercial-announcer delivery?
6. No robotic clause-by-clause breaks?
7. Comfortable to hear repeatedly?
8. Does it have potential to become **the** voice of the channel?

Any pronunciation, continuity, generic-identity, tiring gimmick or
announcer-style failure stops the architecture before corpus creation.
