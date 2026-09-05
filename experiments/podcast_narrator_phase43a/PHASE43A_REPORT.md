# Phase 43A — Vietnamese Podcast Narrator Casting 2.0

Status: **COMPLETE — HUMAN CASTING PACKAGE READY**

## Scope and policy

Phase 43A is the final synthetic casting package for reference only. It contains eight fixed synthetic Vietnamese male identities, each rendered with the same exact Text A and Text B and the same raw generation policy. No voice has been ranked or selected.

The engine is installed VieNeu 3.3.0 V3 Turbo on local ONNX/CPU. The installed `voices_v3_turbo.json` SHA256 is `574e6acf03823c4cafdc43f106731ce5fce6de30228fe383831b8b9064ee0bd8`. Every identity is a convex blend of the same three installed Northern male synthetic presets, with the same Thanh Bình reference-code anchor and unchanged inference controls across A/B. No owner audio, Candidate 03, clone, training, production/UI change, Phase 41 prosody/cadence/tempo, pitch, EQ, compression, formant processing, or bespoke DSP was used. Per-file peak normalization to -1 dBFS is the sole audio treatment.

VieNeu has no supported deterministic seed. The package is for human casting, not a deterministic A/B claim.

## Completion and integrity

All 16 required WAVs exist. A final audit verified each manifest-selected file exists, SHA256 matches its manifest entry, and is PCM16, 48 kHz, mono. Voice 01–04 were preserved without regeneration.

Three interrupted-session artifacts (05A, 05B, and 06A) were already technically valid on disk when this resume began. They were safely adopted into the manifest rather than overwritten or regenerated. Voice 06B, 07A, 07B, 08A, and 08B completed in one accepted technical attempt each. No slot required a retry and no quality-based artifact selection occurred. Superseded artifacts from the earlier stale-manifest incident remain in `metadata/quarantine/`.

The prior external executor path was not used. Rendering was one slot at a time in the workspace sandbox.

## Output summary

| Voice | Text A duration | Text B duration |
|---|---:|---:|
| 01 | 27.28 s | 25.79 s |
| 02 | 31.92 s | 28.35 s |
| 03 | 30.88 s | 28.91 s |
| 04 | 29.84 s | 27.63 s |
| 05 | 28.56 s | 27.63 s |
| 06 | 30.48 s | 28.43 s |
| 07 | 28.08 s | 25.87 s |
| 08 | 30.96 s | 28.99 s |

The complete paths, SHA256 values, engine policy, identity definitions, attempt records, and technical metrics are in `metadata/casting_manifest.json`.

## Human casting package

`HUMAN_REVIEW.md` provides the complete, neutral 8-voice listening list. It deliberately does not rank voices, prescribe a winner, or ask the listener to infer a technical cause.

## Strategic direction

After this reference-only synthetic package, the project direction is **existing Vietnamese voice search / casting**. The owner prefers selecting a strong existing Vietnamese narrator rather than further synthetic generation, cloning, training, or extensive modification. No Phase 43B work is proposed or performed.
