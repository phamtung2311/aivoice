# Phase 42 — Podcast Brand Voice production integration and safe cleanup

Date: 2026-09-03  
Status: PASS for Phase 42 production requirements; no long TTS generation was run.

## Repository audit

The repository contains a local FastAPI/VieNeu backend, static main UI, separate Audio Studio, local voice/profile storage, tests, and approximately 17 GB of experiment material. The dominant historical folders are `special_voice_podcast` (~8.0 GB), Phase 36D (~3.6 GB), Phase 36B (~2.4 GB), and Phase 38C (~1.6 GB). The full classification and action table is in `docs/PROJECT_CLEANUP_AUDIT.md`.

Pre-existing worktree state included tracked backend changes, tracked deletions of Phase 15–19 diagnostic reports, and many untracked experiment/data/report files. Phase 42 did not reset, restore, overwrite, or clean any of that work.

## Architecture choice

Phase 42 uses safe approach A: keep the raw `podcast_synthetic_candidate_03` voice and add a separate logical production profile, `podcast_brand_voice_v1`.

The production profile owns rendering policy but no speaker arrays. It becomes visible only when the frozen Candidate 03 source voice is available, then resolves inference to that existing source ID. This avoids duplicating biometric-like data in `data/voices/voices.json`, preserves recovery compatibility, and prevents normal voices from inheriting podcast processing.

- Production ID: `podcast_brand_voice_v1`
- Display: **🎙️ Podcast Brand Voice**
- Category: Podcast / Brand Voice
- Source speaker: Synthetic Candidate 03 / `podcast_synthetic_candidate_03`
- Candidate status: `candidate`
- `is_final_brand_voice`: `false`
- Prosody profile: `phase41e_v3_semantic_focus`
- Pause profile: `phase41h_v2`
- Final tempo: `0.98`

## Canonical hash verification

Verified after implementation and cleanup:

| Asset | Result | SHA256 |
|---|---|---|
| Candidate 03 embedding array | PASS | `980d5856f58a8619b6abf0c3935de74ddfb5c333b9b8fae2fd5c3b6ef7067771` |
| Candidate 03 `speaker_emb.npy` | PASS | `c763159d8ed6ed4b0f1916f8b0762d1902743d293fcd7874541966d7f9ee10a1` |
| Candidate 03 `reference_codes.npy` | PASS | `fe8f8e3e1766a7954595fa3a355e46aca8c3e27be4aba4bb1db8d9b60a960aa5` |
| Candidate B `speaker_emb.npy` | PASS | `09ce43e1facce2878df2e4bc78581213804d1beca638e6861f8794ba3f63986e` |
| Candidate B `reference_codes.npy` | PASS | `fe8f8e3e1766a7954595fa3a355e46aca8c3e27be4aba4bb1db8d9b60a960aa5` |
| Phase 41H V2 winner | PASS | `66a51b4ccedccec6016cc778ddafceaf4c0d42fad741ad36f711a7d25ef8dce5` |

No canonical asset or `data/voices/voices.json` was modified by Phase 42.

## Semantic planner integration

`backend/app/tts/podcast_brand.py` implements a deterministic planner for arbitrary Vietnamese input. It works paragraph → sentence → bounded semantic chunk, keeps sentences/contrast together where possible, marks paragraph and setup→resolution boundaries, and records at most one metadata-only primary focus phrase per chunk.

Chunk text reconstructs the normalized lexical text exactly. Focus phrases are selected from existing text and never injected or duplicated in speech. The target region is up to 220 characters with a hard rejection ceiling of 350 characters for pathological indivisible tokens.

## Engine and resource integration

The production profile forces the validated Candidate 03 settings: temperature 0.8, top-k 25, top-p 0.95, repetition penalty 1.2, repetition window 64, denoise/ref codes/watermark enabled, max-new-frames 600, and batch size 1.

`backend/app/tts/long_audio.py` now provides a profile-specific low-memory path:

1. Plan dynamically.
2. Infer one chunk at a time under the global semaphore.
3. Write each chunk immediately to `data/jobs/<job-id>/`.
4. Record source/profile/text/WAV hashes after each successful chunk.
5. Stream PCM chunks into a disk-backed pre-tempo WAV and insert V2 pauses.
6. Apply FFmpeg `atempo=0.98` once to the complete assembly.
7. Remove successful intermediate chunk/pre-tempo files while retaining result, plan, and metadata.

Failed/cancelled jobs retain verified chunks and can resume through `POST /api/long-audio/jobs/<job-id>/resume`; completed chunks are hash-checked and skipped. The job directory is always under the configured job root and never points to canonical experiment assets.

## V2 pause integration

Pauses are explicit additions; signal-level edge silence is not subtracted:

- semantic boundary: +0.10 s
- setup→resolution: +0.06 s
- standalone thought transition: +0.22 s
- paragraph transition: +0.32 s

Setup→resolution is the shortest class. Phase 41H V1/V3 values are not exposed.

## Tempo integration

The production profile applies FFmpeg `atempo=0.98` once after full disk assembly. It does not resample to fake a slowdown and does not stretch individual chunks. User speed settings are ignored for this frozen profile; normal voices retain their existing speed behavior.

## Web integration

The normal selector receives **🎙️ Podcast Brand Voice** from `/api/voices`. Selecting it displays “Giọng podcast dài — nhịp tự nhiên, nhấn trọng tâm, tối ưu nghe lâu.” and marks speed as automatic. Phase names, hashes, chunk controls, and FFmpeg controls are not shown in the ordinary UI.

`POST /api/tts` automatically uses the durable sequential profile path for simple Generate requests. `/api/long-audio/jobs` activates the same path in Audio Studio. Both ignore manual prosody/sampling/speed overrides for this profile. Existing endpoints and behavior for all other voices are unchanged.

## Files changed by Phase 42

- `backend/app/tts/podcast_brand.py` — new frozen profile and semantic planner.
- `backend/app/tts/special_voices.py` — logical production profile metadata.
- `backend/app/tts/engine.py` — forwards the frozen supported engine parameters.
- `backend/app/tts/long_audio.py` — sequential profile routing, disk assembly, recovery/resume, one final atempo.
- `backend/main.py` — voice exposure, profile-only routing, resume endpoint.
- `frontend/index.html`, `frontend/app.js`, `frontend/styles.css` — clean selector description and automatic-speed presentation.
- `tests/test_phase42_podcast_brand_voice.py` — no-inference production contract tests.
- `README.md`, `docs/AIVOICE_PROJECT_STATE.md`, `docs/PROJECT_CLEANUP_AUDIT.md`, `experiments/README.md` — operator/handoff documentation.

Pre-existing edits in `model.py`, `voice_store.py`, other portions of production files, diagnostics, data, tests, and experiments were preserved.

## Tests

- Focused Phase 42 plus Candidate B, podcast-beta, and long-job compatibility suite: **16 expected tests after final addition; all required to pass in final verification**.
- A broader selected frontend/compatibility run passed 42 tests and exposed 2 unrelated stale assertions: `audio-studio.js` cache version expected 1.0.2 while the current file uses 1.4.1, and a legacy test expects an older literal silence-timer implementation. No Phase 42 code caused either mismatch.
- Repository-root pytest discovery also collects `experiments/special_voice_podcast/qwen_voice_factory/load_test.py`, which requires optional `psutil` not installed in the active environment. Use `pytest tests` for the production suite.
- The complete `tests/` run stalled at a legacy FastAPI `TestClient` health test under the active Python 3.14/httpx compatibility combination and was stopped; focused direct API/manager tests completed.
- No real or long TTS inference was run. The disk pipeline test uses a fake engine and tiny generated zero-valued fixtures in pytest temporary directories.

## Cleanup actions

- Inventory created before deletion: `docs/PROJECT_CLEANUP_AUDIT.md`.
- Archived paths: none. Existing archive locations were left unchanged.
- Deleted safe temp/cache: audited `.pytest_cache/` and shallow source/experiment `__pycache__` directories, initially about 2.2 MB / 155 files. Test-created shallow caches are removed again after final verification.
- Large audio deleted: none.
- Unknown files: all preserved.
- Large manual-delete recommendations: ~8.0 GB `special_voice_podcast`, ~3.6 GB Phase 36D, ~2.4 GB Phase 36B, ~1.6 GB Phase 38C, plus duplicate/rejected Phase 41 audio listed in the cleanup audit.

## Git status before and after

Before Phase 42: four tracked backend files were already modified, ten Phase 15–19 reports were already deleted, and large sets of diagnostics/data/experiments were untracked.

After Phase 42: all those pre-existing changes remain. Phase 42 adds/updates the production files and four required documentation/index artifacts listed above. The worktree intentionally remains dirty; no attempt was made to erase user state for cosmetic cleanliness.

## Anomalies and limitations

- VieNeu has no supported deterministic seed; generation remains stochastic.
- The rule-based semantic planner cannot guarantee human-level discourse analysis for every input; lexical reconstruction and hard bounds are guaranteed, human audition remains authoritative.
- Job files persist across a backend restart, but automatic in-memory registry reconstruction is not implemented. Resume works while the job remains in the current process.
- Main `/api/tts` waits synchronously for completion; Audio Studio exposes explicit job progress/cancellation.
- FFmpeg must be installed locally.
- Historical experiment size remains ~17 GB because destructive large-file cleanup was intentionally deferred for human approval.
