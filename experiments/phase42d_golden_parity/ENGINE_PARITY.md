# Phase 42D — Engine and speaker parity

## Result

**PASS**

The Podcast Brand Voice no longer renders through the six-decimal JSON compatibility copy. Before any chunk inference, the job loads the canonical Candidate 03 arrays directly, verifies all frozen hashes, and passes the resulting native profile dictionary to `TTSEngine.generate`. Any missing, unreadable, or hash-mismatched canonical asset raises an error; there is no fallback to a named/default voice.

## Runtime identity

| Evidence | Expected | Runtime |
|---|---|---|
| speaker embedding array SHA256 | `980d5856f58a8619b6abf0c3935de74ddfb5c333b9b8fae2fd5c3b6ef7067771` | exact |
| `speaker_emb.npy` file SHA256 | `c763159d8ed6ed4b0f1916f8b0762d1902743d293fcd7874541966d7f9ee10a1` | exact |
| `reference_codes.npy` file SHA256 | `fe8f8e3e1766a7954595fa3a355e46aca8c3e27be4aba4bb1db8d9b60a960aa5` | exact |

The serialized `data/voices/voices.json` Candidate 03 profile remains available for compatibility. Its embedding is still the previously audited six-decimal representation and is not numerically exact. The logical `podcast_brand_voice_v1` route does not use that representation.

Candidate B and all canonical Candidate 03 assets were left untouched.

## Effective inference configuration

| Setting | Production value |
|---|---:|
| VieNeu | 3.3.0 |
| mode | v3turbo |
| backend | onnx |
| temperature | 0.8 |
| top_k | 25 |
| top_p | 0.95 |
| repetition_penalty | 1.2 |
| repetition_window | 64 |
| denoise | true |
| use_ref_codes | true |
| silence_p | 0.15 |
| crossfade_p | 0.0 |
| apply_watermark | true |
| sample rate | 48,000 Hz, enforced |
| max_new_frames | 600 |
| max_chars | 800 |
| batch_size | 1 |

Canonical effective-config SHA256: `f7e2c00fd03a541d61a35f0455aaccc02fe32ed1b143dc023d68f2be5119849f`.

`TTSEngine.generate` now has an explicit preplanned-text path. It sends exactly one already-approved semantic TTS string to `ModelLoader.infer`, forwards `max_chars=800` plus the full frozen configuration, and rejects a model sample rate other than 48 kHz. Normal voices retain the existing generic normalization, splitting, speed, and adjustable sampling behavior.

Focused tests verify the exact arguments at both the long-job → engine boundary and the engine → model boundary without loading VieNeu or synthesizing speech.

