# Phase 30N Report

## Timestamp

2026-08-31 (Asia/Ho_Chi_Minh).

## Status

`MANUAL_PHASE30N_REQUIRED`

## Objective

Compare cadence handling only while preserving the selected M-A identity.

## Identity Lock

All variants use exact preserved M-A conditioning from `phase30m_04`; no Qwen,
new identity, mixing, or reference regeneration is allowed.

## Keeper Integrity

All keeper hashes passed before preparation.

## Pause Pipeline Audit

The production path preprocesses text, splits sentences, groups outer chunks at
240 characters, obtains per-chunk VieNeu audio, measures edge silence, adds only
a deficit gap (period target 130 ms), then joins audio. Commas, periods, question
marks, exclamation marks, newlines, generated chunk edges, and the joiner are all
potential silence sources. There is no production crossfade in this path.

## Generated vs Inserted Silence

Phase 30M showed M-A pauses above the 130 ms explicit join target. Phase 30N
therefore uses the same generated chunk WAVs once and varies only assembly policy,
allowing generated boundary silence and inserted silence to be measured separately.

## Experiment Design

N-CONTROL uses current 130 ms period joining; N-A uses an 85 ms explicit join;
N-B retains 130 ms joining with signal-aware boundary ceilings; N-C combines both.
Speed remains 1.0 and punctuation/text remain unchanged.

## Measurements

The manual runner writes pause-analysis metrics and each variant's duration,
format, peak/RMS, clipping, join target, and boundary policy.

## Blind Audition

The runner will create one private mapping and four blind WAVs, preserving valid
artifacts on a rerun.

## User Verdict

Pending blind listening.

## Production Changes

None.

## Decision

`MANUAL_PHASE30N_REQUIRED`.

## Next Step

Run the finite experiment once in a normal Fedora terminal; do not modify
production join settings before blind listening.

## Manual Run Failure

The prior manual run downloaded VieNeu artifacts and then failed at
`save_wav(... phase30n/internal/N-CONTROL.wav ...)`. It was an output-path
failure, not a Qwen or identity failure.

## Output Directory Root Cause

Verified: `phase30n/internal/` did not exist at the failure time, while the
runner attempted to save N-CONTROL inside it. The filesystem has approximately
348 GiB free; the phase root is valid and writable. The repaired runner creates
phase root, internal, audition, measurements, and chunks directories before model
load, then writes and removes a tiny internal preflight file. It exits clearly
before inference if that check fails.

## Hugging Face Download Audit

The runner previously constructed `TTSEngine` before changing HOME/offline
settings, so VieNeu initialization resolved through the normal Hugging Face Hub
cache and downloaded `pnnbao-ump/VieNeu-TTS-v3-Turbo` assets. The completed local
snapshot is at `/home/tung/.cache/huggingface/hub/models--pnnbao-ump--VieNeu-TTS-v3-Turbo/snapshots/2da0efab622a1722125991736524f080b751ef5b` and includes config, denoiser,
speaker encoder, tokenizer, acoustic/decode/prefill ONNX, backbone data, and
heads. No assets were deleted.

## Offline Runtime Hotfix

Before importing/loading Hub-dependent runtime code, the repaired runner sets
`HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`, and `HF_HOME` to the verified local
cache. It checks every required snapshot artifact and exits
`LOCAL_VIENEU_CACHE_MISSING` with missing paths rather than downloading.

## Resume / Checkpoint Safety

Two valid shared generated chunks already exist at `phase30n/chunks/chunk_00.wav`
and `chunk_01.wav`; they are preserved and reused. The original runner had kept
them on disk before the assembly failure, so no completed VieNeu chunk inference
is lost. Internal variants, private mapping, and audition copies are also reused
or repaired idempotently on future runs.
