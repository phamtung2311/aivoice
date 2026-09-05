# Phase 41E Static Pre-Run Report

## Result

**PHASE41E STATIC PREFLIGHT: PASS**

No TTS inference was run while preparing or validating this report.

## Repository audit findings

- Phase 41D Test 2's 2,163 count is `len()` of the punctuated canonical source in `final_names`.
- The manifest's 2,137 count is the sum of text actually passed in its eight TTS calls. The exact splitter removes all 19 full stops; because `total_chars` sums eight chunks separately, it also excludes the 7 spaces between those chunks. Thus 2,163 − 19 − 7 = 2,137. Script and manifest chunks match byte-for-byte.
- The final 41D report says Test 2 has 20 sentences; the exact source/splitter yields 19.
- Former V0 was one sentence per chunk, not the Phase 41D greedy 350-character control.
- Former V3 was structurally identical to V1 and copied V2 pauses, so it was not a semantic-focus experiment.
- Former V2 did use the same six text chunks as V1, with pause metadata as its intended only difference.
- Four tracked production files were already modified: `backend/app/tts/model.py`, `backend/app/tts/special_voices.py`, `backend/app/tts/voice_store.py`, and `backend/main.py`. This Phase 41E repair did not edit them; their provenance cannot be established from Git because the experiment tree is untracked.
- Phase 41E write scope: PASS. This repair touched only `experiments/brand_voice_phase41e/`. Repository-wide production cleanliness: FAIL because of the pre-existing tracked backend modifications above.

### Observed Candidate 03 rate

| Test | Source chars | Synthesized chunk chars | Duration | Source chars/s |
|---|---:|---:|---:|---:|
| 01_short_monologue | 1103 | 1089 | 56.16s | 19.640 |
| 02_explanatory_section | 2163 | 2137 | 115.36s | 18.750 |
| 03_longform_stress_test | 4356 | 4304 | 225.60s | 19.309 |

Pooled source-text rate: **7622 / 397.12 = 19.193 chars/s**.
Pooled rate over text actually passed to TTS is 18.962 chars/s; it is not used for this punctuated-source estimate.

## Canonical shared audition

```text
Để hiểu rõ điều gì khiến một con người sống với sự bình tĩnh, ta phải nhìn vào cách họ xử lý thời gian. Không phải trong những khoảnh khắc vinh quang, mà trong những giây phút thầm lặng khi mọi thứ quanh họ đang vội. Một người có thể nói rất nhiều, nhưng nếu họ không biết khi nào nên dừng lại, họ sẽ không bao giờ thực sự được nghe. Điều quan trọng không phải là ta đi nhanh đến đâu, mà là ta có biết mình đang đi về đâu hay không. Ta thường tưởng sức nặng của một lời nói nằm ở âm lượng, trong khi nó thật ra nằm ở sự chính xác và khoảng lặng bao quanh. Khi ta chậm lại để lắng nghe, ta bắt đầu nhận ra rằng sự rõ ràng không đến từ sự la hét của ý chí, mà từ sự ổn định của nội tâm. Vì vậy, cách ta nói lên điều mình tin tưởng không chỉ là cách truyền đạt ý tưởng, nó còn cho thấy cách ta sống cùng những ý tưởng ấy. Một người có thể giải thích rõ ràng nhưng vẫn chưa thực sự chạm tới người nghe nếu họ không biết nhấn đúng điểm. Suy cho cùng, cảm giác được hiểu là điều mà người ta nhớ lâu hơn bất kỳ câu văn hoa nào. Người nghe không chỉ cần một câu trả lời đúng; họ cần một nhịp dẫn đủ rõ để tự nhìn thấy điều quan trọng đối với mình. Và đó là lý do vì sao một giọng nói tốt không chỉ cần đúng, mà còn cần biết khi nào nên dừng, khi nào nên nhấn, và khi nào nên để người nghe tự mình suy ngẫm.
```

- UTF-8 SHA256: `12ad8cb1c8483eff48786494eb034580e602982fd90329fd73ce1ad641964dc2`
- Characters: 1298
- Words: 296
- Sentences: 11
- Punctuation: `{"!": 0, ",": 14, ".": 11, ":": 0, ";": 1, "?": 0, "…": 0}`
- Predicted duration at 19.193 chars/s: 67.63s (target 65–73s)

Phase 41D removes full stops before external TTS calls. The plan therefore freezes both the punctuated source and exact Phase-41D-normalized spoken lexical form. Joining every variant's `text` fields with one space exactly reproduces that canonical spoken form.

## Exact variant design

### v0_phase41d_control — 4 chunks

Exact Phase 41D chunk_text_for_longform control with max_chars=350.

| # | Chars | Before → after | Pause | Focus | Exact spoken text |
|---:|---:|---|---:|---|---|
| 0 | 330 | paragraph_start → phase41d_greedy_boundary | 0.00s | — | Để hiểu rõ điều gì khiến một con người sống với sự bình tĩnh, ta phải nhìn vào cách họ xử lý thời gian Không phải trong những khoảnh khắc vinh quang, mà trong những giây phút thầm lặng khi mọi thứ quanh họ đang vội Một người có thể nói rất nhiều, nhưng nếu họ không biết khi nào nên dừng lại, họ sẽ không bao giờ thực sự được nghe |
| 1 | 347 | phase41d_greedy_boundary → phase41d_greedy_boundary | 0.00s | — | Điều quan trọng không phải là ta đi nhanh đến đâu, mà là ta có biết mình đang đi về đâu hay không Ta thường tưởng sức nặng của một lời nói nằm ở âm lượng, trong khi nó thật ra nằm ở sự chính xác và khoảng lặng bao quanh Khi ta chậm lại để lắng nghe, ta bắt đầu nhận ra rằng sự rõ ràng không đến từ sự la hét của ý chí, mà từ sự ổn định của nội tâm |
| 2 | 332 | phase41d_greedy_boundary → phase41d_greedy_boundary | 0.00s | — | Vì vậy, cách ta nói lên điều mình tin tưởng không chỉ là cách truyền đạt ý tưởng, nó còn cho thấy cách ta sống cùng những ý tưởng ấy Một người có thể giải thích rõ ràng nhưng vẫn chưa thực sự chạm tới người nghe nếu họ không biết nhấn đúng điểm Suy cho cùng, cảm giác được hiểu là điều mà người ta nhớ lâu hơn bất kỳ câu văn hoa nào |
| 3 | 275 | phase41d_greedy_boundary → paragraph_end | 0.00s | — | Người nghe không chỉ cần một câu trả lời đúng; họ cần một nhịp dẫn đủ rõ để tự nhìn thấy điều quan trọng đối với mình Và đó là lý do vì sao một giọng nói tốt không chỉ cần đúng, mà còn cần biết khi nào nên dừng, khi nào nên nhấn, và khi nào nên để người nghe tự mình suy ngẫm |

### v1_semantic_chunking — 6 chunks

Semantic grouping only; no manual pause or parameter change.

| # | Chars | Before → after | Pause | Focus | Exact spoken text |
|---:|---:|---|---:|---|---|
| 0 | 214 | paragraph_start → semantic_thought_boundary | 0.00s | — | Để hiểu rõ điều gì khiến một con người sống với sự bình tĩnh, ta phải nhìn vào cách họ xử lý thời gian Không phải trong những khoảnh khắc vinh quang, mà trong những giây phút thầm lặng khi mọi thứ quanh họ đang vội |
| 1 | 213 | semantic_thought_boundary → semantic_thought_boundary | 0.00s | — | Một người có thể nói rất nhiều, nhưng nếu họ không biết khi nào nên dừng lại, họ sẽ không bao giờ thực sự được nghe Điều quan trọng không phải là ta đi nhanh đến đâu, mà là ta có biết mình đang đi về đâu hay không |
| 2 | 249 | semantic_thought_boundary → semantic_thought_boundary | 0.00s | — | Ta thường tưởng sức nặng của một lời nói nằm ở âm lượng, trong khi nó thật ra nằm ở sự chính xác và khoảng lặng bao quanh Khi ta chậm lại để lắng nghe, ta bắt đầu nhận ra rằng sự rõ ràng không đến từ sự la hét của ý chí, mà từ sự ổn định của nội tâm |
| 3 | 244 | semantic_thought_boundary → semantic_thought_boundary | 0.00s | — | Vì vậy, cách ta nói lên điều mình tin tưởng không chỉ là cách truyền đạt ý tưởng, nó còn cho thấy cách ta sống cùng những ý tưởng ấy Một người có thể giải thích rõ ràng nhưng vẫn chưa thực sự chạm tới người nghe nếu họ không biết nhấn đúng điểm |
| 4 | 205 | semantic_thought_boundary → semantic_thought_boundary | 0.00s | — | Suy cho cùng, cảm giác được hiểu là điều mà người ta nhớ lâu hơn bất kỳ câu văn hoa nào Người nghe không chỉ cần một câu trả lời đúng; họ cần một nhịp dẫn đủ rõ để tự nhìn thấy điều quan trọng đối với mình |
| 5 | 157 | semantic_thought_boundary → paragraph_end | 0.00s | — | Và đó là lý do vì sao một giọng nói tốt không chỉ cần đúng, mà còn cần biết khi nào nên dừng, khi nào nên nhấn, và khi nào nên để người nghe tự mình suy ngẫm |

### v2_natural_pacing — 6 chunks

Byte-identical chunk texts and engine controls to V1; only restrained assembly pauses differ.

| # | Chars | Before → after | Pause | Focus | Exact spoken text |
|---:|---:|---|---:|---|---|
| 0 | 214 | paragraph_start → semantic_thought_boundary | 0.06s | — | Để hiểu rõ điều gì khiến một con người sống với sự bình tĩnh, ta phải nhìn vào cách họ xử lý thời gian Không phải trong những khoảnh khắc vinh quang, mà trong những giây phút thầm lặng khi mọi thứ quanh họ đang vội |
| 1 | 213 | semantic_thought_boundary → semantic_thought_boundary | 0.10s | — | Một người có thể nói rất nhiều, nhưng nếu họ không biết khi nào nên dừng lại, họ sẽ không bao giờ thực sự được nghe Điều quan trọng không phải là ta đi nhanh đến đâu, mà là ta có biết mình đang đi về đâu hay không |
| 2 | 249 | semantic_thought_boundary → semantic_thought_boundary | 0.10s | — | Ta thường tưởng sức nặng của một lời nói nằm ở âm lượng, trong khi nó thật ra nằm ở sự chính xác và khoảng lặng bao quanh Khi ta chậm lại để lắng nghe, ta bắt đầu nhận ra rằng sự rõ ràng không đến từ sự la hét của ý chí, mà từ sự ổn định của nội tâm |
| 3 | 244 | semantic_thought_boundary → semantic_thought_boundary | 0.06s | — | Vì vậy, cách ta nói lên điều mình tin tưởng không chỉ là cách truyền đạt ý tưởng, nó còn cho thấy cách ta sống cùng những ý tưởng ấy Một người có thể giải thích rõ ràng nhưng vẫn chưa thực sự chạm tới người nghe nếu họ không biết nhấn đúng điểm |
| 4 | 205 | semantic_thought_boundary → semantic_thought_boundary | 0.10s | — | Suy cho cùng, cảm giác được hiểu là điều mà người ta nhớ lâu hơn bất kỳ câu văn hoa nào Người nghe không chỉ cần một câu trả lời đúng; họ cần một nhịp dẫn đủ rõ để tự nhìn thấy điều quan trọng đối với mình |
| 5 | 157 | semantic_thought_boundary → paragraph_end | 0.00s | — | Và đó là lý do vì sao một giọng nói tốt không chỉ cần đúng, mà còn cần biết khi nào nên dừng, khi nào nên nhấn, và khi nào nên để người nghe tự mình suy ngẫm |

### v3_semantic_focus — 8 chunks

Different setup/resolution boundaries and at most one primary focus phrase per major thought; no manual pauses or acoustic controls.

| # | Chars | Before → after | Pause | Focus | Exact spoken text |
|---:|---:|---|---:|---|---|
| 0 | 214 | paragraph_start → thought_transition | 0.00s | những giây phút thầm lặng | Để hiểu rõ điều gì khiến một con người sống với sự bình tĩnh, ta phải nhìn vào cách họ xử lý thời gian Không phải trong những khoảnh khắc vinh quang, mà trong những giây phút thầm lặng khi mọi thứ quanh họ đang vội |
| 1 | 115 | thought_transition → thought_transition | 0.00s | khi nào nên dừng lại | Một người có thể nói rất nhiều, nhưng nếu họ không biết khi nào nên dừng lại, họ sẽ không bao giờ thực sự được nghe |
| 2 | 154 | thought_transition → setup_resolution_boundary | 0.00s | biết mình đang đi về đâu | Điều quan trọng không phải là ta đi nhanh đến đâu, mà là ta có biết mình đang đi về đâu hay không Ta thường tưởng sức nặng của một lời nói nằm ở âm lượng, |
| 3 | 192 | setup_resolution_boundary → thought_transition | 0.00s | sự ổn định của nội tâm | trong khi nó thật ra nằm ở sự chính xác và khoảng lặng bao quanh Khi ta chậm lại để lắng nghe, ta bắt đầu nhận ra rằng sự rõ ràng không đến từ sự la hét của ý chí, mà từ sự ổn định của nội tâm |
| 4 | 132 | thought_transition → thought_transition | 0.00s | cách ta sống cùng những ý tưởng ấy | Vì vậy, cách ta nói lên điều mình tin tưởng không chỉ là cách truyền đạt ý tưởng, nó còn cho thấy cách ta sống cùng những ý tưởng ấy |
| 5 | 199 | thought_transition → thought_transition | 0.00s | cảm giác được hiểu | Một người có thể giải thích rõ ràng nhưng vẫn chưa thực sự chạm tới người nghe nếu họ không biết nhấn đúng điểm Suy cho cùng, cảm giác được hiểu là điều mà người ta nhớ lâu hơn bất kỳ câu văn hoa nào |
| 6 | 117 | thought_transition → thought_transition | 0.00s | điều quan trọng đối với mình | Người nghe không chỉ cần một câu trả lời đúng; họ cần một nhịp dẫn đủ rõ để tự nhìn thấy điều quan trọng đối với mình |
| 7 | 157 | thought_transition → paragraph_end | 0.00s | không chỉ cần đúng | Và đó là lý do vì sao một giọng nói tốt không chỉ cần đúng, mà còn cần biết khi nào nên dừng, khi nào nên nhấn, và khi nào nên để người nghe tự mình suy ngẫm |

## Variant isolation

- V0 is AST-verified against Phase 41D `chunk_text_for_longform`, with `max_chars=350`: 4 chunks of 330, 347, 332, and 275 characters.
- V1 changes segmentation only. All manual pauses are zero; engine controls are frozen.
- V2 has exactly V1's chunk texts, order, hashes, roles, boundary metadata, and engine controls. Only `pause_after_seconds` differs.
- V3 has 8 chunks versus V1's 6 and a real setup/resolution boundary after `âm lượng,`. It uses no manual pause. Each thought has one primary focus phrase expressed only through grouping/boundaries.

## Pause policy

Clause 0.03s, sentence 0.06s, and thought transition 0.10s are an **experimental heuristic**, not scientifically derived. Only V2 inserts manual silence.

## VieNeu 3.3.0 engine-control audit

- Supported and forwarded: `temperature`, `top_k`, `top_p`, `max_new_frames`, `repetition_penalty`, `repetition_window`, `denoise`, `use_ref_codes`, and `apply_watermark`.
- Chunking is supported through `max_chars`; Phase 41E passes planned chunks individually with `max_chars=800`, `batch_size=1`.
- `silence_p` and `crossfade_p` are accepted by the signature but unused by VieNeu 3.3.0 V3 Turbo. V2 therefore inserts declared silence explicitly during assembly.
- No explicit speed control exists.
- No supported seed/RNG argument exists. **Deterministic seed: NO.**

## Canonical integrity and static consistency

- canonical_speaker_hashes: **PASS**
- vieneu_3_3_0_api_audit: **PASS**
- shared_text_frozen: **PASS**
- duration_target: **PASS**
- v0_true_phase41d_control: **PASS**
- v1_segmentation_only: **PASS**
- v2_equals_v1_plus_pause_only: **PASS**
- v3_real_semantic_focus_structure: **PASS**
- lexical_reconstruction_all_variants: **PASS**
- chunk_metadata: **PASS**
- checkpoint_serialization: **PASS**
- json_parse: **PASS**
- prosody_plan_matches_builder: **PASS**

Canonical hashes verified:

- speaker embedding array: `980d5856f58a8619b6abf0c3935de74ddfb5c333b9b8fae2fd5c3b6ef7067771`
- speaker_emb.npy: `c763159d8ed6ed4b0f1916f8b0762d1902743d293fcd7874541966d7f9ee10a1`
- reference_codes.npy: `fe8f8e3e1766a7954595fa3a355e46aca8c3e27be4aba4bb1db8d9b60a960aa5`

Python compilation and JSON parsing are run separately in final verification.

## Resource-safe external execution

Close VS Code/Codex first, then run one variant per process:

```bash
cd "/home/tung/ai voice" && for variant in v0_phase41d_control v1_semantic_chunking v2_natural_pacing v3_semantic_focus; do .venv/bin/python experiments/brand_voice_phase41e/run_phase41e_prosody.py --generate --variant "$variant" || exit 1; done
```

Each chunk is written immediately and atomically checkpointed. Reuse requires matching plan/config/voice/text/WAV hashes. Interruption resumes at the first invalid or absent chunk.

STOP BEFORE INFERENCE.
