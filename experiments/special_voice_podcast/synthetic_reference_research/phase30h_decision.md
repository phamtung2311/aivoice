# Phase 30H decision

## Status

SYNTHETIC_REFERENCE_PATH_EXPERIMENTAL

## Primary path

Qwen3-TTS-12Hz-1.7B-VoiceDesign, English description
→ one synthetic 6–8 second English WAV
→ installed VieNeu reference encoding
→ Vietnamese VieNeu V3Turbo output

Qwen is exactly one primary technology; it creates the non-human identity. VieNeu is the experimental Vietnamese identity bridge and proposed final daily TTS.

## Why experimental

Qwen officially omits Vietnamese. VieNeu accepts arbitrary waveform reference audio, but no evidence validates English synthetic reference to Vietnamese identity preservation. Two generative stages can compound artifacts/drift. Apache licensing lowers code/weight friction but does not prove training-data provenance, output rights, or no resemblance to training speakers; retain records and conduct release-specific review.

## Phase 30I: one experiment

In a separate Python 3.12 environment, download the exact Qwen VoiceDesign release, make at most three non-imitative English synthetic identities, assess their WAVs, and pass only the best one to VieNeu for one short Vietnamese blind audition. Stop if Vietnamese intelligibility, tonal quality, timbre, or identity stability fails. Do not add another bridge.

