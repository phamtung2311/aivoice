# Phase 45 — Production Voice Set v1

Status: **COMPLETE — PORTABLE RESTORE PACKAGE VERIFIED**

Owner selected `podcast_deep_warm`, `podcast_warm_storyteller`, and `podcast_soft_baritone` as production podcast voices. Their exact float32 192-d arrays and Thanh Bình reference codes are persisted under `assets/production_voices`; the backend now loads them directly and verifies hashes rather than reconstructing blends. UI group is now Giọng Podcast. Phase 44A closed with technical/license pass and human quality fail.

Runtime audited: Python 3.14.7, VieNeu 3.3.0, ONNX Runtime 1.29.0, local CPU ONNX, 48 kHz. No identity, anchor, prosody, tempo, or DSP setting was changed.

Three production-path reference WAVs were rendered sequentially using the frozen resolver. Their hashes are Deep Warm `88dfd9c3e723ebd6e7be753b1120ef51d9cb5e2d4e8c64a9f0e046bff3e66cbb`, Warm Storyteller `f472c68864145b010b8ea5415f58c46c2838efe128dc9193bd63d0c7f01d9155`, Soft Baritone `5f15c888adf83d2009def91572d64b833369d7be50b240adaa57fac445a3279d`. They are sanity references, not deterministic golden bytes.

Private backup includes the frozen artifacts, docs, verifier, dependencies, references and exact 313 MiB model cache trees. Archive: `backups/aivoice_production_voice_set_v1.tar.zst`, 235 MiB, SHA256 `31bd9644ba03830b7bf0f0dd786ea616adf25e7c3c754e41741d139988f89f22`. The lightweight verifier passed.
