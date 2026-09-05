# Phase 40A — native Vietnamese synthetic speaker latent casting

## 1. Execution status

`PASS` — exactly four intended native Vietnamese latent candidates were
generated sequentially on the existing local CPU/ONNX runtime and validated.
Identity quality remains pending human QA.

## 2. Closed paths

- `QWEN VOICEDESIGN CASTING = FAIL FOR BRAND IDENTITY`
- `Candidate 03 = RETIRED`
- `OpenVoice Candidate 03 transfer = HUMAN FAIL`
- `Seed-VC A/B/C/D transfer = CANCELLED — NO VALUE WITHOUT A STRONG TARGET IDENTITY`

No previous asset was modified and none of these paths was executed in Phase
40A.

## 3. Architecture/runtime audit

Installed VieNeu version: 3.3.0. Preset source asset:
`voices_v3_turbo.json`, SHA-256
`574e6acf03823c4cafdc43f106731ce5fce6de30228fe383831b8b9064ee0bd8`.

The actual package contains 20 v3 Turbo presets. Every preset has a finite
192-dimensional float speaker embedding and finite integer reference codes with
16 codebooks. The public v3 runtime accepts a manually supplied
`{"speaker_emb": ..., "codes": ...}` dictionary. The project wrapper forwards
that dictionary without requiring voice registration; the experiment called the
native API directly and did not read/write production voice storage.

Relevant installed paths/functions:

- `vieneu/v3turbo.py::_load_v3_voices`: loads the two components separately;
- `vieneu/v3turbo.py::_resolve_ref`: accepts a voice dictionary unchanged;
- `vieneu/v3turbo.py::infer`: forwards the resolved embedding and codes;
- `vieneu/_v3_turbo_engine/onnx_runtime_lite.py::_speaker_anchor`: reshapes the
  supplied vector, then applies Linear projection and LayerNorm.

There is no speaker-embedding input normalization. Consequently no blend was
renormalized; inventing such a normalization would violate the observed runtime
contract.

## 4. Exact male preset inventory

| Name | Region | Style/character | Embedding | Codes | Norm |
|---|---|---|---|---|---:|
| Minh Đức | Bắc | tin tức | 192 | 50×16 | 12.432240 |
| Phạm Tuyên | Bắc | tự nhiên | 192 | 62×16 | 12.945850 |
| Thái Sơn | Nam | kể chuyện | 192 | 49×16 | 13.191870 |
| Xuân Vĩnh | Nam | tự nhiên | 192 | 40×16 | 12.822335 |
| Thanh Bình | Bắc | kể chuyện | 192 | 42×16 | 12.207491 |
| Minh Triết | Nam | tin tức | 192 | 56×16 | 10.813890 |
| Quang Sơn | Trung | tự nhiên | 192 | 43×16 | 10.991061 |
| Đức Trí | Nam | đọc truyện | 192 | 76×16 | 12.293865 |
| Adam | Nam | tự nhiên | 192 | 39×16 | 18.822561 |

All nine male embeddings/codes are finite. Full per-anchor hashes, all pairwise
distances/cosines, PCA coordinates, and all 20 preset shape checks are preserved
in `embedding_geometry.json`.

## 5. Embedding geometry summary

- Male cosine range: 0.096774 (`Minh Triết`/`Adam`) to 0.575559
  (`Phạm Tuyên`/`Quang Sơn`).
- First PCA components explain 26.7501%, 15.4659%, 14.5552%, 12.5983%, and
  10.4697% of variance. There is no single dominant one-dimensional speaker
  axis.
- Northern-anchor cosines: Minh Đức/Phạm Tuyên 0.385958; Minh Đức/Thanh Bình
  0.461475; Phạm Tuyên/Thanh Bình 0.280048.
- Accent allocation between speaker embedding and reference codes is not proven
  separable. To control regional risk, Phase 40A therefore uses only the three
  Northern male embeddings rather than treating Southern/Central embeddings as
  timbre-only evidence.

## 6. Fixed reference-code anchor

`Thanh Bình — Nam · Bắc · Phong cách kể chuyện`

Reason: Northern male storytelling is the highest-priority locally supported
delivery character for reflective narration, ahead of natural and news. The
same `(42,16)` code array, SHA-256
`38964457925e5cf4362c90026e4bf552ddf1cf6acc35bc9555cd06c12603efb8`,
was used unchanged for all four outputs.

## 7. Exact convex embedding formulas

- A = 0.75 × Minh Đức + 0.25 × Phạm Tuyên; norm 10.986784.
- B = 0.75 × Phạm Tuyên + 0.25 × Thanh Bình; norm 10.962793.
- C = 0.75 × Thanh Bình + 0.25 × Minh Đức; norm 10.942990.
- D = ⅓ × Minh Đức + ⅓ × Phạm Tuyên + ⅓ × Thanh Bình; norm 9.568488.

All weights are non-negative and sum to one. No extrapolation, negative
coefficient, random vector, scaling, or normalization was used. Blend pairwise
cosines range from 0.574008 to 0.899007; Euclidean distances range from 4.821393
to 10.109860.

## 8. Shared Vietnamese audition text

> Giữa những đổi thay, điều giữ chúng ta đứng vững không phải là câu trả lời có sẵn, mà là khả năng nhìn rõ điều mình tin và sống nhất quán với nó.

One normalized inference unit, no programmed 1–2 second pause.

## 9. Generation configuration and metrics

Common configuration: NumPy seed 40001; temperature 0.8; top-k 25; top-p 0.95;
repetition penalty 1.2; repetition window 64; max new frames 300; max chars 256;
reference codes enabled; watermark enabled; default semantic punctuation gaps;
no crossfade; CPU/ONNX; 48 kHz. Only `speaker_emb` changed.

| Candidate | Generation | Duration | RTF | Peak | RMS | Clipped | Peak RSS |
|---|---:|---:|---:|---:|---:|---:|---:|
| A | 6.524 s | 9.360 s | 0.697 | 0.572998 | 0.102256 | 0 | 1333.918 MiB |
| B | 5.125 s | 8.320 s | 0.616 | 0.767273 | 0.098358 | 0 | 1340.453 MiB |
| C | 3.625 s | 7.280 s | 0.498 | 0.642761 | 0.107400 | 0 | 1340.609 MiB |
| D | 4.357 s | 8.080 s | 0.539 | 0.743408 | 0.095709 | 0 | 1340.609 MiB |

Model load: 1.609 seconds. Total wall: 21.317 seconds. All four WAVs are
PCM16 mono 48 kHz, non-empty, finite, frame-complete, and contain no clipped
sample. C naturally ended at 7.28 seconds; it was preserved without reroll.

## 10. Audition and human gate

Exactly four primary WAVs exist:

- `audio/candidate_A.wav`
- `audio/candidate_B.wav`
- `audio/candidate_C.wav`
- `audio/candidate_D.wav`

Classify each as `NO`, `INTERESTING`, or `YES`. Objective metrics do not decide
speaker identity or quality.

`NATIVE VIETNAMESE BRAND IDENTITY CASTING: PENDING HUMAN QA`

No model download, user voice, Qwen, OpenVoice, Seed-VC, training, production
voice registration, or production modification occurred. Licensing remains
`CONDITIONALLY COMMERCIAL-SAFE PENDING DERIVATIVE-ASSET INTERPRETATION`.
