# AIVoice experiment index

`production_voice_phase45/` is the current frozen production record. Other phase folders are historical research; Phase 46 hides them in VS Code Explorer without relocating or deleting evidence.

Use `docs/AIVOICE_PROJECT_STATE.md` for the current production handoff and `docs/PROJECT_CLEANUP_AUDIT.md` before deleting or moving artifacts.

## Active / canonical

- `brand_voice_phase40b/` — Candidate B golden baseline and identity evidence.
- `brand_voice_phase41b/` — Synthetic Candidate 03 canonical baseline; never mutate its `.npy` assets.
- `brand_voice_phase41d/` — long-form explanatory control and final report.
- `brand_voice_phase41e/` — semantic-focus comparison; `v3_semantic_focus` won human QA.
- `brand_voice_phase41f/` — pitch-preserving tempo comparison; 0.98x won human QA.
- `brand_voice_phase41g/` — 55-chunk long-form source and integrity manifest.
- `brand_voice_phase41h/` — semantic pause comparison; V2 Natural Podcast Cadence won human QA.
- `phase42_production_integration/` — production integration and cleanup report.
- `special_voice_review/` — evidence for the existing Review Film special voice.
- `special_voice_podcast/keepers/` — older podcast keepers still referenced by compatibility profiles.

## Historical / reference

- `brand_speaker_phase33a/` through `brand_speaker_phase33c/` — early speaker search.
- `brand_voice_phase34/` through `brand_voice_phase39a/` — historical speaker, model, and conversion exploration.
- `brand_voice_phase40a/` — Candidate B lineage.
- `brand_voice_phase40c/` — post-Candidate-B historical experiment.
- `brand_voice_phase41a/` — Candidate 03 blind-audition lineage.
- `podcast_voice_phase31b/`, `podcast_voice_phase32/`, `podcast_voice_phase33/` — early podcast evaluations.
- `special_voice_podcast/` outside canonical keepers — broad Phase 30–31 research and generated evidence.
- `emotion/`, `index_emotion_kaggle/`, `special_voice_meme/` — separate emotion/meme research tracks.

## Archived

- No experiment directory was newly moved during Phase 42. Existing `diagnostics/archive/` remains unchanged.
- Large historical runtimes and rejected audio are listed for manual review in `docs/PROJECT_CLEANUP_AUDIT.md`; they were not deleted automatically.

## Preservation rule

Never delete a folder solely because it is old or untracked. Keep canonical baselines, winner WAVs, manifests, reports, blind mappings, and enough lineage to reconstruct the current stack. Delete only known recreatable caches unless a human explicitly approves a larger archive/delete plan.
