# Phase 41E Final Technical Report

## Objective and audit status

Phase 41E tests whether external text segmentation and restrained boundary pacing can improve the natural rhythm, pause placement, rate stability, and semantic focus of frozen Synthetic Podcast Candidate 03. It does not redesign, blend, retrain, pitch-shift, EQ, compress, reverberate, or otherwise modify the voice identity.

This is a post-generation, read-only audio audit. No additional TTS inference was run.

Technical artifact audit: **PASS**  
Human listening decision: **COMPLETE**

## Completed blind human QA

- **BLIND WINNER: 04**
- Saved mapping reveals Blind 04 as **`v3_semantic_focus`**.
- **PHASE41E PROSODY WINNER: `v3_semantic_focus`**
- Main positive finding: semantic emphasis / semantic stress is successful and quite good.
- Remaining issue: delivery is still slightly too fast.

Blind 01 was slightly too fast. Blind 02 was also slightly too fast; some emphasis worked, but speech continued too quickly immediately after the emphasized phrase. Blind 03 received no strong positive preference. Blind 04 was best and placed semantic stress well.

The winning V3 structure, generated waveform, semantic emphasis, Candidate 03 embedding, and reference codes are frozen. Phase 41F is limited to micro tempo adjustment derived from the exact V3 final WAV and will not rerender TTS.

## Canonical speaker integrity

The frozen files remain under `experiments/brand_voice_phase41b/baseline/PODCAST_SYNTHETIC_CANDIDATE_03/`.

- Speaker embedding array SHA256: `980d5856f58a8619b6abf0c3935de74ddfb5c333b9b8fae2fd5c3b6ef7067771`
- `speaker_emb.npy` file SHA256: `c763159d8ed6ed4b0f1916f8b0762d1902743d293fcd7874541966d7f9ee10a1`
- `reference_codes.npy` file SHA256: `fe8f8e3e1766a7954595fa3a355e46aca8c3e27be4aba4bb1db8d9b60a960aa5`

All three hashes match the frozen Phase 41B/41D values and the bindings in `resume_state.json`: **PASS**.

## Frozen shared audition text

```text
Để hiểu rõ điều gì khiến một con người sống với sự bình tĩnh, ta phải nhìn vào cách họ xử lý thời gian. Không phải trong những khoảnh khắc vinh quang, mà trong những giây phút thầm lặng khi mọi thứ quanh họ đang vội. Một người có thể nói rất nhiều, nhưng nếu họ không biết khi nào nên dừng lại, họ sẽ không bao giờ thực sự được nghe. Điều quan trọng không phải là ta đi nhanh đến đâu, mà là ta có biết mình đang đi về đâu hay không. Ta thường tưởng sức nặng của một lời nói nằm ở âm lượng, trong khi nó thật ra nằm ở sự chính xác và khoảng lặng bao quanh. Khi ta chậm lại để lắng nghe, ta bắt đầu nhận ra rằng sự rõ ràng không đến từ sự la hét của ý chí, mà từ sự ổn định của nội tâm. Vì vậy, cách ta nói lên điều mình tin tưởng không chỉ là cách truyền đạt ý tưởng, nó còn cho thấy cách ta sống cùng những ý tưởng ấy. Một người có thể giải thích rõ ràng nhưng vẫn chưa thực sự chạm tới người nghe nếu họ không biết nhấn đúng điểm. Suy cho cùng, cảm giác được hiểu là điều mà người ta nhớ lâu hơn bất kỳ câu văn hoa nào. Người nghe không chỉ cần một câu trả lời đúng; họ cần một nhịp dẫn đủ rõ để tự nhìn thấy điều quan trọng đối với mình. Và đó là lý do vì sao một giọng nói tốt không chỉ cần đúng, mà còn cần biết khi nào nên dừng, khi nào nên nhấn, và khi nào nên để người nghe tự mình suy ngẫm.
```

- UTF-8 SHA256: `12ad8cb1c8483eff48786494eb034580e602982fd90329fd73ce1ad641964dc2`
- Characters: 1,298
- Whitespace-delimited words: 296
- Sentences: 11

Phase 41D's control splitter removes full stops before TTS. All four plans reconstruct the same normalized spoken lexical text exactly; punctuation treatment is consistent across variants.

## Frozen engine controls

All generation used VieNeu 3.3.0 V3 Turbo on the ONNX backend with the frozen controls: temperature 0.8, top-k 25, top-p 0.95, repetition penalty 1.2, repetition window 64, denoise enabled, reference codes enabled, watermark enabled, 48 kHz output, maximum 600 new frames, external chunking, internal `max_chars=800`, and batch size 1.

VieNeu 3.3.0 accepts `silence_p` and `crossfade_p` in the V3 Turbo signature but does not consume them in that implementation. Phase 41E V2 silence was therefore inserted explicitly at assembly. No speed, pitch, volume, EQ, compression, formant, or emotion control was used.

## Exact variant plans and isolation

### V0 — Phase 41D control

Exact AST-verified Phase 41D `chunk_text_for_longform` behavior with greedy packing to 350 characters. Four chunks, no manual silence.

| # | Chars | Boundary after | Exact TTS text |
|---:|---:|---|---|
| 0 | 330 | Phase 41D greedy boundary | Để hiểu rõ điều gì khiến một con người sống với sự bình tĩnh, ta phải nhìn vào cách họ xử lý thời gian Không phải trong những khoảnh khắc vinh quang, mà trong những giây phút thầm lặng khi mọi thứ quanh họ đang vội Một người có thể nói rất nhiều, nhưng nếu họ không biết khi nào nên dừng lại, họ sẽ không bao giờ thực sự được nghe |
| 1 | 347 | Phase 41D greedy boundary | Điều quan trọng không phải là ta đi nhanh đến đâu, mà là ta có biết mình đang đi về đâu hay không Ta thường tưởng sức nặng của một lời nói nằm ở âm lượng, trong khi nó thật ra nằm ở sự chính xác và khoảng lặng bao quanh Khi ta chậm lại để lắng nghe, ta bắt đầu nhận ra rằng sự rõ ràng không đến từ sự la hét của ý chí, mà từ sự ổn định của nội tâm |
| 2 | 332 | Phase 41D greedy boundary | Vì vậy, cách ta nói lên điều mình tin tưởng không chỉ là cách truyền đạt ý tưởng, nó còn cho thấy cách ta sống cùng những ý tưởng ấy Một người có thể giải thích rõ ràng nhưng vẫn chưa thực sự chạm tới người nghe nếu họ không biết nhấn đúng điểm Suy cho cùng, cảm giác được hiểu là điều mà người ta nhớ lâu hơn bất kỳ câu văn hoa nào |
| 3 | 275 | Paragraph end | Người nghe không chỉ cần một câu trả lời đúng; họ cần một nhịp dẫn đủ rõ để tự nhìn thấy điều quan trọng đối với mình Và đó là lý do vì sao một giọng nói tốt không chỉ cần đúng, mà còn cần biết khi nào nên dừng, khi nào nên nhấn, và khi nào nên để người nghe tự mình suy ngẫm |

### V1 — semantic chunking only

Six coherent semantic groups. Only segmentation differs from V0; engine controls and speaker inputs are unchanged. Every manual pause is zero.

| # | Chars | Semantic role | Exact TTS text |
|---:|---:|---|---|
| 0 | 214 | Opening and contrast | Để hiểu rõ điều gì khiến một con người sống với sự bình tĩnh, ta phải nhìn vào cách họ xử lý thời gian Không phải trong những khoảnh khắc vinh quang, mà trong những giây phút thầm lặng khi mọi thứ quanh họ đang vội |
| 1 | 213 | Behavior and principle | Một người có thể nói rất nhiều, nhưng nếu họ không biết khi nào nên dừng lại, họ sẽ không bao giờ thực sự được nghe Điều quan trọng không phải là ta đi nhanh đến đâu, mà là ta có biết mình đang đi về đâu hay không |
| 2 | 249 | Setup and realization | Ta thường tưởng sức nặng của một lời nói nằm ở âm lượng, trong khi nó thật ra nằm ở sự chính xác và khoảng lặng bao quanh Khi ta chậm lại để lắng nghe, ta bắt đầu nhận ra rằng sự rõ ràng không đến từ sự la hét của ý chí, mà từ sự ổn định của nội tâm |
| 3 | 244 | Expression and reception | Vì vậy, cách ta nói lên điều mình tin tưởng không chỉ là cách truyền đạt ý tưởng, nó còn cho thấy cách ta sống cùng những ý tưởng ấy Một người có thể giải thích rõ ràng nhưng vẫn chưa thực sự chạm tới người nghe nếu họ không biết nhấn đúng điểm |
| 4 | 205 | Listener resolution | Suy cho cùng, cảm giác được hiểu là điều mà người ta nhớ lâu hơn bất kỳ câu văn hoa nào Người nghe không chỉ cần một câu trả lời đúng; họ cần một nhịp dẫn đủ rõ để tự nhìn thấy điều quan trọng đối với mình |
| 5 | 157 | Closing thought | Và đó là lý do vì sao một giọng nói tốt không chỉ cần đúng, mà còn cần biết khi nào nên dừng, khi nào nên nhấn, và khi nào nên để người nghe tự mình suy ngẫm |

### V2 — natural pacing

The six exact chunk texts, ordering, hashes, roles, boundaries, engine controls, and speaker inputs are identical to V1. Only assembly-time pauses differ.

| # | Chars | Pause after | Exact TTS text hash |
|---:|---:|---:|---|
| 0 | 214 | 0.06s | `d5776c7f3175817ea804267f4aaccf4766f8c49ad73718d805d8c71ee175e21c` |
| 1 | 213 | 0.10s | `e7042062937b11bd4997665bd50da958dde742abffa15b9e3cf0c6604fbae880` |
| 2 | 249 | 0.10s | `cd159b7bc9449cf55867ed4469b42e886738a52ee7f274020b0a3774b90d6ae8` |
| 3 | 244 | 0.06s | `fd75fcb026fbfe676d8aa97c1ecb40bb053a2a7997d94cdef99993323180bee7` |
| 4 | 205 | 0.10s | `d2a9a1c18ea3367eaf10932c598395e8e63e19da222af647ce3b06033c5325af` |
| 5 | 157 | 0.00s | `5492b105099f4f7173c2d4281e2a6adbdff622ab6a0e72f703b5ad9fc1227507` |

Inserted manual silence: **0.42s total**. The policy remains an experimental heuristic, not a scientifically derived prosody model.

### V3 — semantic focus structure

Eight focus-aware chunks, no manual silence and no acoustic emphasis manipulation. Each major thought records at most one focus phrase. The setup/resolution split after `âm lượng,` creates a real structural difference from V1.

| # | Chars | Role | Primary focus | Exact TTS text |
|---:|---:|---|---|---|
| 0 | 214 | Context then contrast | những giây phút thầm lặng | Để hiểu rõ điều gì khiến một con người sống với sự bình tĩnh, ta phải nhìn vào cách họ xử lý thời gian Không phải trong những khoảnh khắc vinh quang, mà trong những giây phút thầm lặng khi mọi thứ quanh họ đang vội |
| 1 | 115 | Behavior resolution | khi nào nên dừng lại | Một người có thể nói rất nhiều, nhưng nếu họ không biết khi nào nên dừng lại, họ sẽ không bao giờ thực sự được nghe |
| 2 | 154 | Principle then setup | biết mình đang đi về đâu | Điều quan trọng không phải là ta đi nhanh đến đâu, mà là ta có biết mình đang đi về đâu hay không Ta thường tưởng sức nặng của một lời nói nằm ở âm lượng, |
| 3 | 192 | Contrast resolution | sự ổn định của nội tâm | trong khi nó thật ra nằm ở sự chính xác và khoảng lặng bao quanh Khi ta chậm lại để lắng nghe, ta bắt đầu nhận ra rằng sự rõ ràng không đến từ sự la hét của ý chí, mà từ sự ổn định của nội tâm |
| 4 | 132 | Idea and lived alignment | cách ta sống cùng những ý tưởng ấy | Vì vậy, cách ta nói lên điều mình tin tưởng không chỉ là cách truyền đạt ý tưởng, nó còn cho thấy cách ta sống cùng những ý tưởng ấy |
| 5 | 199 | Clarity then human result | cảm giác được hiểu | Một người có thể giải thích rõ ràng nhưng vẫn chưa thực sự chạm tới người nghe nếu họ không biết nhấn đúng điểm Suy cho cùng, cảm giác được hiểu là điều mà người ta nhớ lâu hơn bất kỳ câu văn hoa nào |
| 6 | 117 | Listener agency | điều quan trọng đối với mình | Người nghe không chỉ cần một câu trả lời đúng; họ cần một nhịp dẫn đủ rõ để tự nhìn thấy điều quan trọng đối với mình |
| 7 | 157 | Closing resolution | không chỉ cần đúng | Và đó là lý do vì sao một giọng nói tốt không chỉ cần đúng, mà còn cần biết khi nào nên dừng, khi nào nên nhấn, và khi nào nên để người nghe tự mình suy ngẫm |

## Final WAV verification

All final files are mono, 48,000 Hz, PCM16 WAVs. Hashes were recalculated from disk and match `manifest.json`.

| Variant | Final path | SHA256 | Chunk audio | Manual silence | Assembled duration | Peak | Full-scale samples |
|---|---|---|---:|---:|---:|---:|---:|
| V0 | `experiments/brand_voice_phase41e/audio/v0_phase41d_control_final.wav` | `765d4258c3da5af8709738faf66b3526b115d6352a321414d582edbc19d3cea9` | 65.36s | 0.00s | 65.36s | 0.94391 | 0 |
| V1 | `experiments/brand_voice_phase41e/audio/v1_semantic_chunking_final.wav` | `16000b1cd0f7880ec2ff6c7566de57d17f4e12471c4a9af61044c7e6f38d927e` | 66.16s | 0.00s | 66.16s | 0.92041 | 0 |
| V2 | `experiments/brand_voice_phase41e/audio/v2_natural_pacing_final.wav` | `0c2baa5225cc71e76d7b92fb9197def2335c3c775433a9f1873d77d882405508` | 68.72s | 0.42s | 69.14s | 0.99997 | 2 |
| V3 | `experiments/brand_voice_phase41e/audio/v3_semantic_focus_final.wav` | `51e4bd659d4d3d9d9dae236f08d5d6c9aaa704cf825553cd81cf5707bb874569` | 68.88s | 0.00s | 68.88s | 0.99997 | 7 |

“Full-scale samples” means PCM samples at magnitude 32,767. It identifies possible isolated clipping but does not establish audible distortion by itself.

## Per-chunk and pacing metrics

Character rate uses the exact text submitted in that TTS call. Word rate uses whitespace-delimited words. Variance and standard deviation below are population statistics across chunks, unweighted by chunk duration. They describe the generated artifacts but cannot isolate causal effects because generation is stochastic.

### V0 chunk metrics

| Chunk | Chars | Words | Duration | Chars/s | Words/s | Peak | Full-scale samples |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 330 | 72 | 16.00s | 20.625 | 4.500 | 0.84369 | 0 |
| 1 | 347 | 84 | 18.88s | 18.379 | 4.449 | 0.94391 | 0 |
| 2 | 332 | 75 | 16.00s | 20.750 | 4.688 | 0.77649 | 0 |
| 3 | 275 | 65 | 14.48s | 18.992 | 4.489 | 0.74036 | 0 |

- Mean chunk rate: 19.686 chars/s; population SD 1.025; variance 1.051; coefficient of variation 5.21%.
- Mean word rate: 4.531 words/s; population SD 0.092.
- Longest chunk: #1, 18.88s. Shortest: #3, 14.48s.

### V1 chunk metrics

| Chunk | Chars | Words | Duration | Chars/s | Words/s | Peak | Full-scale samples |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 214 | 46 | 10.80s | 19.815 | 4.259 | 0.83704 | 0 |
| 1 | 213 | 49 | 10.72s | 19.869 | 4.571 | 0.92041 | 0 |
| 2 | 249 | 61 | 13.84s | 17.991 | 4.408 | 0.88712 | 0 |
| 3 | 244 | 54 | 11.68s | 20.890 | 4.623 | 0.75772 | 0 |
| 4 | 205 | 48 | 10.88s | 18.842 | 4.412 | 0.80035 | 0 |
| 5 | 157 | 38 | 8.24s | 19.053 | 4.612 | 0.74509 | 0 |

- Mean chunk rate: 19.410 chars/s; population SD 0.916; variance 0.838; coefficient of variation 4.72%.
- Mean word rate: 4.481 words/s; population SD 0.132.
- Longest chunk: #2, 13.84s. Shortest: #5, 8.24s.

### V2 chunk metrics

| Chunk | Chars | Words | Duration | Chars/s | Words/s | Peak | Full-scale samples |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 214 | 46 | 11.12s | 19.245 | 4.137 | 0.91495 | 0 |
| 1 | 213 | 49 | 10.72s | 19.869 | 4.571 | 0.82974 | 0 |
| 2 | 249 | 61 | 13.52s | 18.417 | 4.512 | 0.99997 | 2 |
| 3 | 244 | 54 | 12.32s | 19.805 | 4.383 | 0.93765 | 0 |
| 4 | 205 | 48 | 11.68s | 17.551 | 4.110 | 0.84543 | 0 |
| 5 | 157 | 38 | 9.36s | 16.774 | 4.060 | 0.82724 | 0 |

- Mean chunk rate: 18.610 chars/s; population SD 1.151; variance 1.325; coefficient of variation 6.18%.
- Mean word rate: 4.295 words/s; population SD 0.202.
- Longest chunk: #2, 13.52s. Shortest: #5, 9.36s.
- The 0.42s assembly silence is excluded from per-chunk speech rates and included in the 69.14s final duration.

### V3 chunk metrics

| Chunk | Chars | Words | Duration | Chars/s | Words/s | Peak | Full-scale samples |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 214 | 46 | 11.76s | 18.197 | 3.912 | 0.89758 | 0 |
| 1 | 115 | 26 | 6.24s | 18.429 | 4.167 | 0.64767 | 0 |
| 2 | 154 | 36 | 8.32s | 18.510 | 4.327 | 0.99997 | 7 |
| 3 | 192 | 48 | 10.80s | 17.778 | 4.444 | 0.75192 | 0 |
| 4 | 132 | 30 | 6.88s | 19.186 | 4.360 | 0.75787 | 0 |
| 5 | 199 | 45 | 10.24s | 19.434 | 4.395 | 0.83566 | 0 |
| 6 | 117 | 27 | 6.08s | 19.243 | 4.441 | 0.83054 | 0 |
| 7 | 157 | 38 | 8.56s | 18.341 | 4.439 | 0.75778 | 0 |

- Mean chunk rate: 18.640 chars/s; population SD 0.546; variance 0.298; coefficient of variation 2.93%.
- Mean word rate: 4.311 words/s; population SD 0.174.
- Longest chunk: #0, 11.76s. Shortest: #6, 6.08s.

## Stochastic limitation

VieNeu 3.3.0 exposes no supported deterministic seed or RNG-control API. Consequently, these four outputs are **not a deterministic A/B test**. Differences may contain both:

- intended prosody, segmentation, and assembly-pause effects; and
- uncontrolled stochastic generation effects.

The numeric measurements describe files; they do not establish that one design is better. No numeric winner is declared. Blind human audition remains authoritative.

## Checkpoint and resume audit

`resume_state.json` binds reuse to the configuration SHA256, plan SHA256, all three canonical voice hashes, each chunk text SHA256, and each chunk WAV SHA256. It contains completed records for all 24 expected chunks: 4 V0, 6 V1, 6 V2, and 8 V3. The final file hashes match `manifest.json`. Chunk WAV hashes recalculated from disk match checkpoint records.

The external runner writes each chunk to a temporary WAV, atomically replaces its target, then atomically updates the checkpoint. On interruption, reuse occurs only when the binding, text hash, file existence, and WAV hash all match. Final assembly occurs after all chunks for the selected variant are present or safely reused.

## Anomalies and evidence limits

- V2 chunk #2 has 2 full-scale PCM samples; V3 chunk #2 has 7. These are possible isolated clipping points and require listening to judge audibility.
- V0 and V1 contain no full-scale samples.
- No peak RSS or generation-time telemetry was written to the Phase 41E manifest/checkpoint. Memory/RSS therefore cannot be reported numerically. The artifact layout confirms sequential per-chunk disk writes, but it is not a memory measurement.
- The different durations and pacing statistics cannot be attributed solely to the intended variant treatment because generation was unseeded.
- No missing chunk, empty WAV, sample-rate mismatch, channel mismatch, final-hash mismatch, or duration-assembly mismatch was found.

## Production and repository status

Phase 41E files are isolated under `experiments/brand_voice_phase41e/`. The frozen speaker assets still match their canonical hashes. This audit did not run inference and did not edit production source files.

At report time, `git status --short` contained 4 tracked modified files, 10 tracked deleted files, and 117 untracked entries. The tracked modifications predate this audit:

```text
 M backend/app/tts/model.py
 M backend/app/tts/special_voices.py
 M backend/app/tts/voice_store.py
 M backend/main.py
```

Ten historical Phase 15–19 diagnostic reports remain marked deleted. The complete Phase 41E directory is untracked as `?? experiments/brand_voice_phase41e/`. Therefore the overall repository is not clean, although no production mutation is attributable to this audit.

## Blind audition package

Blind package creation: **PASS**.

- `blind/01.wav`, `blind/02.wav`, `blind/03.wav`, and `blind/04.wav` exist.
- Each blind file is a byte-identical copy of exactly one final variant WAV.
- Clip names and WAV contents do not expose variant names.
- The one-time randomized mapping is stored separately in `blind_mapping.json` and is intentionally omitted here.
- Listener questions are in `blind/HUMAN_REVIEW.md`; that document does not reveal or ask the listener to infer the mapping.

SYNTHETIC CANDIDATE 03 PROSODY + SEMANTIC FOCUS:
HUMAN QA COMPLETE — PHASE41E PROSODY WINNER: v3_semantic_focus
