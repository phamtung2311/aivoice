# AIVoice project state

Primary handoff document, updated for Phase 42D on 2026-09-04.

## 1. Current production architecture

AIVoice is a local FastAPI backend plus a static HTML/CSS/JavaScript frontend. VieNeu runs locally on CPU. `/api/voices` supplies the selector, `/api/tts` supplies simple one-click synthesis, and `/api/long-audio/jobs` supplies inspectable sequential jobs used by Audio Studio. Normal voices retain the pre-Phase-42 engine path.

The Podcast Brand Voice is an opt-in logical rendering profile. After Phase 42C found that the JSON compatibility profile was not bit-equivalent, Phase 42D changed production to load and hash-verify the canonical Candidate 03 `.npy` arrays directly. It normalizes input before planning, converts each semantic group through the validated TTS punctuation policy, bypasses generic re-chunking, generates one chunk at a time, writes each WAV immediately, inserts exact V2 pauses during disk-backed assembly, then invokes FFmpeg `atempo=0.98` once on the complete WAV.

## 2. Current best speaker

Synthetic Candidate 03 is the best human-selected podcast speaker. Its technical status remains `candidate`; `is_final_brand_voice` remains `false`. The raw compatibility voice `podcast_synthetic_candidate_03` must remain available.

Canonical directory:

`experiments/brand_voice_phase41b/baseline/PODCAST_SYNTHETIC_CANDIDATE_03/`

## 3. Canonical hashes

| Asset | SHA256 |
|---|---|
| Candidate 03 embedding array bytes | `980d5856f58a8619b6abf0c3935de74ddfb5c333b9b8fae2fd5c3b6ef7067771` |
| Candidate 03 `speaker_emb.npy` file | `c763159d8ed6ed4b0f1916f8b0762d1902743d293fcd7874541966d7f9ee10a1` |
| Candidate 03 `reference_codes.npy` file | `fe8f8e3e1766a7954595fa3a355e46aca8c3e27be4aba4bb1db8d9b60a960aa5` |
| Candidate B `speaker_emb.npy` file | `09ce43e1facce2878df2e4bc78581213804d1beca638e6861f8794ba3f63986e` |
| Candidate B `reference_codes.npy` file | `fe8f8e3e1766a7954595fa3a355e46aca8c3e27be4aba4bb1db8d9b60a960aa5` |

## 4. Winning podcast rendering stack

Production ID: `podcast_brand_voice_v1`  
Display name: **🎙️ Podcast Brand Voice**

- Speaker: Synthetic Candidate 03
- Prosody: Phase 41E `v3_semantic_focus`
- Tempo: Phase 41F `0.98x`
- Pauses: Phase 41H V2 Natural Podcast Cadence
- Explicit pre-tempo pause policy: semantic `+0.10 s`, setup→resolution `+0.06 s`, standalone thought transition `+0.22 s`, paragraph transition `+0.32 s`
- Engine defaults: temperature 0.8, top-k 25, top-p 0.95, repetition penalty 1.2, repetition window 64, denoise/ref codes/watermark enabled, max new frames 600, batch size 1

Winning Phase 41H validation WAV:

`experiments/brand_voice_phase41h/audio/v2_natural.wav`  
SHA256 `66a51b4ccedccec6016cc778ddafceaf4c0d42fad741ad36f711a7d25ef8dce5`  
Duration `450.685375 s`

## 5. Phase map

- Phase 40A–40B: Candidate B lineage and golden baseline.
- Phase 41A–41B: Candidate 03 audition lineage and immutable canonical package.
- Phase 41D: explanatory long-form control/evidence.
- Phase 41E: semantic-focus prosody; V3 human winner.
- Phase 41F: isolated tempo audition; 0.98x human winner.
- Phase 41G: 55-chunk long-form validation source.
- Phase 41H: semantic breathing cadence; V2 human winner.
- Phase 42: initial production profile, safe sequential pipeline, UI integration, and project index; code tests passed, but later human web listening failed.
- Phase 42C: read-only equivalence audit identified speaker, inference, TTS-text, planner, and pause differences.
- Phase 42D: golden parity repair; static regression reproduces all 55 validated TTS strings and 54/54 boundaries. The user externally rendered a 4-chunk, 30.251-second smoke sample and passed it by human listening (“nghe ổn rồi”). Full browser/web UI production-job listening remains pending.
- Earlier Phase 30–39 folders are historical/reference unless explicitly named as a current special voice dependency.

## 6. Canonical folders

- Candidate 03: `experiments/brand_voice_phase41b/baseline/PODCAST_SYNTHETIC_CANDIDATE_03/`
- Candidate B: `experiments/brand_voice_phase40b/baseline/PODCAST_CANDIDATE_B_BASELINE/`
- Current cadence evidence: `experiments/brand_voice_phase41h/`
- Live compatibility voice store: `data/voices/voices.json`
- Production policy: `backend/app/tts/podcast_brand.py`
- Production runtime identity: hash-verified canonical Candidate 03 `.npy` files

## 7. Files never to edit manually

Do not edit canonical `.npy` files, their manifests, `data/voices/voices.json` speaker arrays, blind mappings before QA, or winning WAVs. Provision profiles through the existing scripts/API. The production profile deliberately resolves to existing Candidate 03 rather than copying arrays.

## 8. Run backend and frontend

From the repository root:

```bash
.venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8000
python3 -m http.server 5173 --directory frontend
```

Open `http://127.0.0.1:5173`. FFmpeg must be on `PATH` for Podcast Brand Voice final tempo processing.

## 9. Generate Podcast Brand Voice

In the main web page, paste a Vietnamese podcast script, choose **🎙️ Podcast Brand Voice**, and press Generate. The backend ignores user speed, manual prosody markup, and sampling overrides for this frozen profile. It performs normalization, discourse-aware semantic planning, validated TTS-text conversion, lossless canonical Candidate 03 inference, V2 pauses, disk assembly, and final 0.98x tempo automatically.

API clients can POST the normal request shape to `/api/tts` with `voice: "podcast_brand_voice_v1"`. Audio Studio can use the same ID through `/api/long-audio/jobs`.

## 10. Resource safety and recovery

Podcast chunks are generated serially under `data/jobs/<job-id>/`. Each completed chunk is written immediately and recorded by text/WAV hash in `metadata.json`. A failed or cancelled in-memory job can be resumed through `POST /api/long-audio/jobs/<job-id>/resume`; verified chunks are reused. Assembly streams PCM from disk and does not retain the full set of chunk arrays in RAM. Successful jobs remove intermediate chunks and retain the final WAV, plan, hashes, and metadata.

## 11. Known limitations

- VieNeu has no supported deterministic seed; two TTS renders are not deterministic A/B realizations.
- The semantic planner is deterministic, rule-based Vietnamese text structure—not a linguistic oracle. Human listening remains authoritative.
- Phase 42D static parity, unit tests, and the external backend smoke human QA pass. This short sample is not full long-form production validation; browser/web UI → real production job → human listening remains pending.
- Recovery metadata survives on disk, but the in-memory job registry does not reload automatically after a backend restart.
- `/api/tts` waits for the local long-form job to finish; Audio Studio exposes richer progress/cancel behavior.
- CPU-only long-form generation can take several minutes. Only one inference runs at a time by default.
- FFmpeg is a required free local dependency for the production podcast profile.
- Historical experiment folders occupy substantial disk; see `docs/PROJECT_CLEANUP_AUDIT.md` before manually deleting anything.
