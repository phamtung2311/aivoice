# Phase 43A checkpoint

Status: **COMPLETE — HUMAN CASTING PACKAGE READY**

## Completed and verified

- Engine selected: installed VieNeu 3.3.0 V3 Turbo, ONNX/CPU, 48 kHz; `voices_v3_turbo.json` SHA256 `574e6acf03823c4cafdc43f106731ce5fce6de30228fe383831b8b9064ee0bd8`.
- Synthetic-only policy: eight planned convex combinations of the three installed Northern male embeddings (Thanh Bình, Phạm Tuyên, Minh Đức); no owner audio, Candidate 03, celebrity/podcaster clone, training, UI, or production change.
- Shared policy: same reference-code anchor Thanh Bình, same raw inference controls, exact supplied Text A/B, peak-only normalization to -1 dBFS, no Phase 41 prosody/cadence/tempo, pitch, EQ, compression, or formant processing.
- Voice 01–04 A/B are present and their hashes match `metadata/casting_manifest.json`. Their first generation attempt is retained; a stale-manifest race from interrupted tool sessions was reconciled without quality-based selection. Quarantine artifacts remain in `metadata/quarantine/` for audit.

## Do not redo

Do not regenerate Voice 01–04 A/B. Do not run the runner outside the filesystem sandbox: that executor used a stale workspace snapshot and caused false hash-mismatch reconciliation events.

## Final state

All 16 A/B WAVs are hash-verified PCM16/48-kHz mono files. `HUMAN_REVIEW.md` is ready. No winner has been selected, and this phase stops after human listening.
