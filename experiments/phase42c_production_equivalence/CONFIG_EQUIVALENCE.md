# Phase 42C — Configuration and identity equivalence

Static comparison only. No model was loaded and no TTS was run.

## Inference settings

| Setting | Validated Phase 41G | Current production | Result |
|---|---:|---:|---|
| mode | v3turbo | factory default v3turbo | PASS |
| backend | onnx | onnx | PASS |
| temperature | 0.8 | 0.8 | PASS |
| top_k | 25 | 25 | PASS |
| top_p | 0.95 | 0.95 | PASS |
| repetition_penalty | 1.2 | 1.2 | PASS |
| repetition_window | 64 | 64 | PASS |
| denoise | true | true | PASS |
| use_ref_codes | true | true | PASS |
| apply_watermark | true | true | PASS |
| sample rate | 48,000 Hz | VieNeu v3turbo runtime constant 48,000 Hz | PASS |
| max_new_frames | 600 | 600 | PASS |
| batch_size | 1 | 1 | PASS |
| silence_p | 0.15 explicit | omitted; VieNeu default 0.15 | effective value PASS |
| crossfade_p | 0.0 explicit | omitted; VieNeu default 0.0 | effective value PASS |
| VieNeu max_chars | 800 | omitted; VieNeu default 256 | **FAIL** |
| outer generic max_chunk_chars | not used in experimental direct call | 350 | different path |
| inference speed | no model speed transform | 1.0 | PASS |

The required sampling values reach `V3TurboVieNeuTTS.infer` through `TTSEngine.generate` and `ModelLoader.infer`. The strict configuration result is **FAIL** because the exact argument set is not identical: production omits `max_chars=800` and relies on the VieNeu default of 256. A static call to the installed VieNeu 3.3.0 chunk normalizer verified 54 inner chunks from 54 production inputs, with no split indexes, so this difference does not trigger an inner split on the Phase 41G fixture.

## Input-string equivalence

- Validated Phase 41G sends the exact `semantic_plan.json` chunk strings directly to `Vieneu.infer`.
- Production sends newly planned strings through `TTSEngine.generate`.
- Validated strings remove terminal sentence punctuation according to their documented reconstruction rule.
- Production strings retain terminal periods.
- Exact same-index input-string matches: **0/54**.

This is acoustically relevant: punctuation and grouping are part of the model input and can affect within-chunk prosody before any assembly pause is inserted.

## Runtime speaker resolution

Logical resolution:

`podcast_brand_voice_v1`
→ `podcast_synthetic_candidate_03`
→ `data/voices/voices.json`
→ `voice_store.deserialize_profile`
→ VieNeu v3turbo named preset lookup.

| Asset | Canonical | Resolved runtime | Result |
|---|---|---|---|
| speaker embedding array SHA256 | `980d5856f58a8619b6abf0c3935de74ddfb5c333b9b8fae2fd5c3b6ef7067771` | `4df3952e40259c716845cbfba83a697493aa72ec0e0d1e6133688aec51ece2d9` | **FAIL** |
| reference-code array SHA256 | `38964457925e5cf4362c90026e4bf552ddf1cf6acc35bc9555cd06c12603efb8` | `38964457925e5cf4362c90026e4bf552ddf1cf6acc35bc9555cd06c12603efb8` | PASS |
| canonical speaker_emb.npy file SHA256 | `c763159d8ed6ed4b0f1916f8b0762d1902743d293fcd7874541966d7f9ee10a1` | canonical file unchanged | PASS |
| canonical reference_codes.npy file SHA256 | `fe8f8e3e1766a7954595fa3a355e46aca8c3e27be4aba4bb1db8d9b60a960aa5` | canonical file unchanged | PASS |

The persisted JSON serialization rounds embedding values to six decimals. At runtime, 183 of 192 float32 elements differ from the canonical array; maximum absolute error is `4.842877388000488e-07`. The difference is numerically small but fails exact equivalence and may contribute to stochastic acoustic differences. Reference codes are exact.

VieNeu v3turbo uses speaker embedding plus reference codes; it does not use a separate reference-text parameter for this profile path. Reference text is therefore not an experimental/production input in this v3turbo stack.

Candidate 03 remains unchanged on disk and remains:

- `status = candidate`
- `is_final_brand_voice = false`

## Pause profile

| Boundary class | Validated Phase 41H V2 | Production |
|---|---:|---:|
| semantic thought | 31 × 0.10 s = 3.10 s | 37 × 0.10 s = 3.70 s |
| setup→resolution | 7 × 0.06 s = 0.42 s | 0 × 0.06 s = 0.00 s |
| paragraph transition | 16 × 0.32 s = 5.12 s | 16 × 0.32 s = 5.12 s |
| total explicit silence before atempo | **8.64 s** | **8.82 s** |

The numeric policy constants are present, but their application is not equivalent because the production planner emits different labels. In particular, it emits no setup→resolution boundaries for this fixture.

## Tempo location and assembly order

Production order is:

semantic planning
→ sequential original-speed chunk TTS
→ concatenate chunks in index order and add explicit zero PCM
→ one final `ffmpeg atempo=0.98`

Tempo location: **PASS**. There is no per-chunk atempo, no segment speed plus final speed, and the ordinary UI value `1` is ignored for the brand profile.

Assembly ordering is index-sequential and therefore structurally correct. The content being assembled is nevertheless different because the production chunks and boundary classifications are different.
