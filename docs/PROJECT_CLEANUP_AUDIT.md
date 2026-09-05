# AIVoice project cleanup audit — Phase 42

Inventory captured before cleanup on 2026-09-03. Repository size was dominated by `experiments/` at approximately 17 GB. The audit uses directory-level rows for generated experiment families and file-level rows for canonical assets and requested reports; no untracked file is assumed disposable merely because it is untracked.

## Categories and actions

- **A — Production / active:** preserve in place.
- **B — Golden baseline:** immutable; preserve and hash-check.
- **C — Important R&D evidence:** preserve decision reports, manifests, winners, and needed provenance.
- **D — Superseded / archive:** historical; leave in place in Phase 42 unless provenance is unambiguous and moving it has clear value.
- **E — Cache / temp / safe to delete:** delete only named recreatable caches.
- **F — Unknown:** do not touch.

## Pre-cleanup Git state

The worktree already contained tracked edits in `backend/app/tts/model.py`, `backend/app/tts/special_voices.py`, `backend/app/tts/voice_store.py`, and `backend/main.py`; tracked deletions of diagnostics Phase 15–19 files; and many untracked diagnostics, datasets, scripts, tests, and experiment directories. These pre-existing changes are preserved. No reset, restore, checkout, or Git clean operation is authorized or used.

## Production, data, and top-level inventory

| Path | Category | Approx. size | Reason | Phase 42 action |
|---|---|---:|---|---|
| `backend/` | A | 524 KB | FastAPI, TTS engine, voice store, long jobs | Preserve; integrate profile |
| `frontend/` | A | 232 KB | Main web UI and Audio Studio | Preserve; minimal selector hint |
| `tests/` | A | 1.2 MB | Regression suite | Preserve; add Phase 42 tests |
| `data/voices/voices.json` | A | 166 KB | Live local voice library with biometric-like arrays | Preserve unchanged; no duplicate production arrays |
| `data/jobs/` | A/F | variable | Live/recovery job artifacts | Preserve; never bulk-delete |
| `data/nlp/`, `data/voice_lab/` | A | part of 16 MB data | Runtime NLP and Voice Lab state | Preserve |
| `models/` | A | large | Local VieNeu runtime/model | Preserve |
| `scripts/` | A/C | small | Operator and provisioning tools | Preserve |
| `docs/`, `diagnostics/` | C | ~2.5 MB | Handoff and historical evidence | Preserve existing changes |
| `output/` | F | variable | User/runtime output with uncertain ownership | Leave untouched |
| `.venv/` | A | local environment | Current development runtime | Leave untouched |
| `:memory:.ses`, `hdsd.txt` | F | small | Ownership/purpose not proven | Leave untouched |
| `.pytest_cache/` | E | 40 KB | Recreated by pytest | Delete |
| source-tree `__pycache__/`, `*.pyc` | E | ~2.2 MB across 155 files in selected shallow caches | Recreated by Python | Delete named shallow caches only |

## Canonical and winning stack inventory

| Path | Category | Reason | Action |
|---|---|---|---|
| `experiments/brand_voice_phase40b/baseline/PODCAST_CANDIDATE_B_BASELINE/` | B | Candidate B golden baseline | Preserve and hash-check |
| `experiments/brand_voice_phase41b/baseline/PODCAST_SYNTHETIC_CANDIDATE_03/` | B | Candidate 03 canonical speaker arrays/codes | Preserve and hash-check |
| `experiments/brand_voice_phase41d/` | C | Final explanatory baseline and report evidence | Preserve |
| `experiments/brand_voice_phase41e/` | C | Winning `v3_semantic_focus` evidence | Preserve |
| `experiments/brand_voice_phase41f/` | C | Winning 0.98x evidence | Preserve |
| `experiments/brand_voice_phase41g/` | C | 55-chunk long-form source and integrity manifest | Preserve |
| `experiments/brand_voice_phase41h/` | C | Winning V2 cadence WAV/report, 490 MB | Preserve |
| `experiments/phase42_production_integration/` | A/C | Production integration report | Create |

## Experiment directory inventory

| Path | Approx. size | Category | Reason / action |
|---|---:|---|---|
| `brand_speaker_phase33a` | 43 MB | D | Early speaker search; leave in place |
| `brand_speaker_phase33b` | 12 MB | D | Early speaker search; leave in place |
| `brand_speaker_phase33c` | 61 MB | D | Early speaker search; leave in place |
| `brand_voice_phase34` | 32 MB | D | Historical audition; leave in place |
| `brand_voice_phase35` | 14 MB | D | Historical audition; leave in place |
| `brand_voice_phase35b` | 19 MB | D | Historical audition; leave in place |
| `brand_voice_phase36`, `36c`, `36k`, `36l`, `37`, `37a`, `37b`, `37c`, `37d` | <150 KB combined | D | Historical reports/configs; preserve |
| `brand_voice_phase36b` | 2.4 GB | D | Superseded runtime/research payload; recommend manual archive/delete review |
| `brand_voice_phase36d` | 3.6 GB | D | Superseded embedded Python/runtime research payload; recommend manual archive/delete review |
| `brand_voice_phase36i` | 728 KB | D | Historical evidence; preserve |
| `brand_voice_phase36m` | 348 MB | D | Historical model research; recommend manual archive review |
| `brand_voice_phase38a` | 4.3 MB | D | Historical experiment; preserve |
| `brand_voice_phase38b` | 36 KB | D | Historical report/config; preserve |
| `brand_voice_phase38c` | 1.6 GB | D | OpenVoice research checkout/runtime; recommend manual archive/delete review |
| `brand_voice_phase39a` | 2.0 MB | D | Historical candidate research; preserve |
| `brand_voice_phase40a` | 3.2 MB | C | Candidate B lineage | Preserve |
| `brand_voice_phase40b` | 3.0 MB | B/C | Candidate B baseline and evidence | Preserve |
| `brand_voice_phase40c` | 14 MB | D | Post-candidate experiment; preserve pending manual review |
| `brand_voice_phase41a` | 69 MB | C | Candidate 03 selection lineage | Preserve |
| `brand_voice_phase41b` | 5.5 MB | B/C | Candidate 03 canonical baseline | Preserve |
| `brand_voice_phase41d` | 145 MB | C | Required winner/evidence | Preserve |
| `brand_voice_phase41e` | 75 MB | C | Required winner/evidence | Preserve |
| `brand_voice_phase41f` | 53 MB | C | Required winner/evidence | Preserve |
| `brand_voice_phase41g` | 121 MB | C | Required long-form chunks/provenance | Preserve |
| `brand_voice_phase41h` | 490 MB | C | Required V2 winner/evidence | Preserve |
| `emotion/` | 3.8 MB | C/D | Separate emotion research | Preserve |
| `index_emotion_kaggle/` and ZIP | 124 KB | C/D | Reproducible notebook package | Preserve |
| `podcast_voice_phase31b` | 16 MB | D | Early podcast lineage | Preserve |
| `podcast_voice_phase32` | 20 KB | D | Early podcast lineage | Preserve |
| `podcast_voice_phase33` | 44 KB | D | Early podcast lineage | Preserve |
| `special_voice_meme` | 32 KB | C/D | Separate feature evidence | Preserve |
| `special_voice_review` | 19 MB | C | Existing production special voice evidence | Preserve |
| `special_voice_podcast` | 8.0 GB | C/D | Broad podcast lineage plus large local runtimes/models | Preserve now; manual size review |

## Large audio/runtime recommendations

No large audio or experiment directory is automatically deleted or moved in Phase 42. Recommended for manual review:

- `experiments/special_voice_podcast/` (~8.0 GB), especially embedded runtimes/model generations while retaining `keepers/`, reports, manifests, and canonical references.
- `experiments/brand_voice_phase36d/` (~3.6 GB), especially `.venv*`, `python312/`, and downloaded source/runtime payloads.
- `experiments/brand_voice_phase36b/` (~2.4 GB).
- `experiments/brand_voice_phase38c/` (~1.6 GB).
- Phase 41H duplicates: `blind/` ~172 MB, `audio/` ~172 MB, and `audio/pretempo/` ~169 MB. Keep the V2 winner, its pretempo source if provenance is desired, manifest/report, and mapping; rejected/duplicated files can be removed only after explicit manual confirmation.
- Phase 41D `superseded/` ~49 MB and 31-output audio directory ~76 MB: review against the final report before removal.

## Cleanup action log

- Archived paths: none. The existing `diagnostics/archive/` and all experiment locations are left as found because bulk moves would add risk without reducing disk use.
- Safe deletion scope: `.pytest_cache/` plus shallow source/experiment `__pycache__` directories identified above; embedded virtual environments and downloaded runtimes are excluded.
- Unknown files: preserved without modification.
