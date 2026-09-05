# Phase 42D — Golden parity repair report

## Outcome

**PHASE42D GOLDEN PARITY REPAIR: PASS (STATIC/UNIT + EXTERNAL SMOKE HUMAN QA)**

The smallest parity-focused repair was applied without changing Candidate 03, Candidate B, canonical assets, global tempo, or the normal-voice rendering path. No long TTS or FFmpeg transform was run by Codex. The user subsequently ran the prepared short external smoke render and passed it by human listening.

## History

- Initial Phase 42 production integration passed its code tests.
- Later web listening failed human QA because the prosody/intonation sounded inconsistent (“ngữ điệu lung tung”).
- Phase 42C correctly classified production as non-equivalent and identified speaker, inference, TTS-text, semantic-plan, and pause-placement differences.
- Phase 42D repairs those specific parity differences; it does not retroactively mark the earlier web audio acceptable.

## Repaired parity

- Speaker: direct lossless canonical Candidate 03 arrays; three frozen hashes verified; no fallback.
- Inference: exact validated VieNeu values, explicit `max_chars=800`, enforced 48 kHz, generic UI overrides ignored.
- TTS strings: centralized validated terminal-punctuation policy; 55/55 exact fixture strings.
- Planner: 55 chunks and 54/54 exact inter-chunk boundaries; 0 validated-only and 0 production-only.
- Pauses: 31 semantic, 7 setup→resolution, 16 paragraph transitions; total 8.64 s; none after final.
- Tempo: one final full-assembly `atempo=0.98`.
- Double chunking: prevented for preplanned brand chunks.
- Normal voices: adjustable behavior preserved.
- Diagnostic manifest: implemented.
- Audio Studio: brand-specific generic controls visually locked; backend enforcement remains authoritative.

## Regression evidence

Focused Phase 42D plus adjacent long-audio/Audio Studio suite:

`25 passed in 2.02s`

The focused Phase 42 file contains 15 tests and covers canonical hashes/failure, inference forwarding, UI override isolation, normal-voice controls, text conversion, exact Phase 41G planner parity, absence of fixture-sentence hardcoding, pause placement, one final tempo call, resume behavior, and diagnostic metadata. Adjacent suites cover the pre-existing long-audio and Audio Studio paths.

An attempted broad `tests/test_api.py` invocation did not complete within the 30-second command window and produced no result; it is not counted as a pass or failure. No real TTS output was requested by the Phase 42D tests.

## External smoke test

Start the backend from the repository root, then run:

`.venv/bin/python experiments/phase42d_golden_parity/run_external_smoke.py`

The script submits the first frozen Phase 41G paragraph (validated chunks 0–3, approximately 30 seconds) and intentionally includes conflicting generic UI values plus a fake marked TTS Script. The script was prepared but not executed by Codex.

The user executed it externally with this result:

- Runtime state: `COMPLETED: 4/4`
- WAV: `experiments/phase42d_golden_parity/phase42d_smoke.wav`
- WAV SHA256: `3cd568d0ed4dc5704983d11433f26059fdb3ccd8930ee351cb29f9d37bb4d504`
- Duration: `30.25102083333333 s`
- Format: 48,000 Hz, mono, 16-bit PCM
- Runtime manifest: `data/jobs/long_3047e1df51874de4/podcast_pipeline_manifest.json`
- Runtime profile: `podcast_brand_voice_v1`
- Runtime chunks: 4
- Runtime Candidate 03 embedding-array SHA256: `980d5856f58a8619b6abf0c3935de74ddfb5c333b9b8fae2fd5c3b6ef7067771`
- Runtime inference-config SHA256: `f7e2c00fd03a541d61a35f0455aaccc02fe32ed1b143dc023d68f2be5119849f`
- Runtime final tempo: `0.98`
- Generic UI parameters: `ignored`
- Human result: **PASS**
- Human feedback: “nghe ổn rồi”

**PHASE42D EXTERNAL SMOKE HUMAN QA = PASS**

This supports that the repaired production backend path is perceptually acceptable for the short smoke sample and that the previously reported chaotic/inconsistent intonation was not reproduced. It is not a full long-form production validation.

## Files

- `ENGINE_PARITY.md`
- `PLANNER_PARITY.md`
- `PAUSE_PARITY.md`
- `WEB_PROFILE_TRACE.md`
- `PHASE42D_REPORT.md`
- `run_external_smoke.py`

## Current gate

Static and unit parity: **PASS**  
Short external render: **PASS**  
Short external human listening: **PASS**  
Browser/web UI → real production job → human listening: **PENDING**

Candidate 03 remains `status = candidate` and `is_final_brand_voice = false`.
