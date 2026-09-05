# Phase 42C — Production equivalence audit

## Result

**PHASE42C PRODUCTION EQUIVALENCE: FAIL**

**Human QA: FAIL — web prosody/intonation inconsistent (“ngữ điệu lung tung”).**

The current web implementation is not equivalent to the experimentally validated stack. The strongest demonstrated cause is that the automatic production planner does not reproduce the validated Phase 41G semantic grouping. Strict speaker-array and inference-argument equivalence also fail, and the changed boundary labels produce a different pause schedule.

No TTS inference, FFmpeg transformation, voice mutation, parameter tuning, or planner fix was performed in this audit.

## Known-good reference

- Stack: Synthetic Candidate 03 + Phase41E `v3_semantic_focus` + Phase41F `0.98x` + Phase41H V2 cadence
- Known-good WAV: `experiments/brand_voice_phase41h/audio/v2_natural.wav`
- WAV SHA256: `66a51b4ccedccec6016cc778ddafceaf4c0d42fad741ad36f711a7d25ef8dce5`
- Phase 41G semantic plan SHA256: `67b4d48416ccb47b4f2586c9188cf313d30836554241a757a85152f6802196d9`
- Candidate 03 canonical embedding-array SHA256: `980d5856f58a8619b6abf0c3935de74ddfb5c333b9b8fae2fd5c3b6ef7067771`

## Exact-source planning comparison

- Source: `experiments/brand_voice_phase41g/podcast_text.txt`
- File SHA256: `547ba4195a4d1e14a06763209204a5a9f5ebd48b3f23ed84d3659bff7bc5c5ce`
- Stripped UTF-8 SHA256: `04e27a95375cef05ff87bd2d930b581254f039350e092b1b2dd0939cefcfecb7`
- Paragraphs: 17
- Sentences: 86
- `normalize_text` changed this fixture: no
- `preprocess_text` changed this fixture: no

| Metric | Validated Phase 41G | Current production |
|---|---:|---:|
| chunks | 55 | 54 |
| minimum chars | 77 | 65 |
| median chars | 152 | 157 |
| mean chars | 147.5455 | 151.8889 |
| maximum chars | 219 | 219 |
| semantic boundaries | 31 | 37 |
| setup→resolution boundaries | 7 | 0 |
| paragraph transitions | 16 | 16 |
| exact same-index text matches | — | 0/54 |
| explicit V2-style silence before atempo | 8.64 s | 8.82 s |

Boundary comparison in cumulative whitespace-token coordinates:

- matching inter-chunk positions: **47**;
- validated-only positions: **7** — 61, 596, 633, 861, 1687, 1707, 1792;
- production-only positions: **6** — 72, 614, 653, 879, 1082, 1695.

Production reconstructs the source after whitespace canonicalization: **PASS**. It does not reproduce the validated spoken chunk strings: production retains terminal periods, while the validated plan removes them. The complete mismatch inventory and both snippets for every mismatch are in `PLAN_DIFF.md`.

**AUTOMATIC SEMANTIC PLANNER = NOT EQUIVALENT TO VALIDATED V3**

The `primary_focus_phrase` field is metadata only. It is recorded in plan/job metadata but is not passed as an acoustic emphasis control. Therefore its presence does not demonstrate focus-equivalent TTS grouping.

## Hypothesis audit

1. Different semantic boundaries: **CONFIRMED** — 54 vs 55 chunks and 13 nonmatching boundary positions.
2. Paragraph/sentence information lost before planning: **NOT CONFIRMED for this fixture** — 17 paragraph groups and 86 sentences remain detectable, but the heuristic regrouping differs.
3. Frontend submits edited TTS Script: **submitted when populated, but not used by this brand backend**.
4. Manual pause markers alter brand structure: **NO** — brand route ignores TTS Script/markers.
5. Different normalization path: **CONFIRMED at model-input level** — local NLP normalization is a no-op here, but production retains punctuation that validated TTS strings omit.
6. Different inference arguments: **CONFIRMED strictly** — production relies on `max_chars=256` default instead of experimental `max_chars=800`; listed sampling values otherwise match.
7. Different speaker/reference resolution: **CONFIRMED strictly** — codes match, runtime JSON embedding does not byte-match the canonical embedding array.
8. Different per-segment TTS path: **CONFIRMED** — experiment calls VieNeu directly with validated strings/assets; production passes newly planned strings and a named persisted profile through `TTSEngine` and `ModelLoader`.
9. Final assembly order differs: **NOT CONFIRMED** — production preserves planned index order.
10. Tempo in wrong location: **NOT CONFIRMED** — one final full-waveform atempo is used.
11. Long-audio rechunks semantic chunks: **NO resulting extra chunks on this fixture**.
12. Safety splitter divides a semantic chunk: **NO on this fixture** — all 54 remain one-for-one.
13. API treats brand as ordinary voice: **NO in the backend render branch**; the frontend presents the raw ID and ordinary speed control, but the handler overrides brand behavior.
14. Focus metadata exists without affecting grouping/acoustics: **CONFIRMED for acoustic use** — it is metadata only; grouping comes from generic length-aware sentence packing.
15. Automatic heuristic reproduces hand-validated V3: **REFUTED**.

## Root-cause classification

- **A. SPEAKER RESOLUTION MISMATCH** — exact canonical embedding array is not resolved; JSON round-trip changes 183/192 values.
- **B. INFERENCE CONFIG MISMATCH** — strict argument path differs at `max_chars` (800 validated vs 256 effective production default).
- **C. NORMALIZATION MISMATCH** — specifically the final TTS input realization: validated chunks strip terminal punctuation, production retains it; the NLP normalizer itself is not the cause on this source.
- **D. SEMANTIC PLANNER MISMATCH** — primary root cause; 55 vs 54 chunks, 13 displaced boundaries, and no reproduced setup→resolution labels.
- **F. PAUSE ASSEMBLY MISMATCH** — constants match, boundary application does not; 8.64 s vs 8.82 s with different locations.

Not selected:

- **E. DOUBLE CHUNKING** — no resulting split for this exact source.
- **G. TEMPO/SPEED MISMATCH** — final location/value are correct.
- **H. FRONTEND REQUEST/PAYLOAD MISMATCH** — the frontend sends extra editable fields, but the brand backend correctly ignores them and uses original text.

## Relative importance

The most important mismatch is **D: semantic planner mismatch**, compounded by different punctuation-bearing TTS input strings. It changes within-chunk context, grouping, and boundary placement before synthesis; post-TTS silence cannot repair incorrect within-chunk prosody.

The speaker embedding mismatch is exact and must be fixed for rigorous equivalence, but its maximum numeric deviation is under 5×10⁻⁷, so this static audit does not claim it is the dominant audible cause. VieNeu is unseeded, so no static audit can attribute a particular audible realization exclusively to one factor.

## Recommended next fix

In the next implementation phase, make production consume or deterministically reproduce the validated semantic-plan schema and exact TTS chunk strings first, including punctuation policy and boundary classes. Resolve Candidate 03 from the canonical arrays without six-decimal JSON loss, and forward the exact experimental VieNeu arguments. Keep the already-correct final assembly order and one final `atempo=0.98`. Then perform a small controlled verification before any long web render.

This recommendation is not implemented here.

## Artifacts

- `production_semantic_plan.json` — complete current production plan for the exact Phase 41G text
- `PLAN_DIFF.md` — aggregate metrics, all 13 nonmatching boundary positions, and every same-index text mismatch with validated/production snippets
- `WEB_PIPELINE_TRACE.md` — actual browser-to-audio execution chain
- `CONFIG_EQUIVALENCE.md` — inference, speaker, pause, and tempo comparison

## Repository state

The worktree was already dirty before this audit, including Phase 42 integration changes and many unrelated historical/untracked artifacts. This audit did not clean, revert, or mutate those files. It added only the Phase 42C audit directory and its reports.

## Preservation

Candidate 03 canonical files were read only and remain unchanged.

- `status = candidate`
- `is_final_brand_voice = false`

**DO NOT MODIFY THE VOICE.**

