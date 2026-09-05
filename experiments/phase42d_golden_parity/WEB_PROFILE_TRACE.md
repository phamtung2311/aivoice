# Phase 42D — Web profile trace

## Actual Audio Studio route

Audio Studio `Generate`
→ `generate(index)` submits `item.text` plus the selected ID and generic UI state
→ `POST /api/long-audio/jobs`
→ brand handler selects original text and ignores edited TTS Script/markers
→ local `normalize_text` before planning
→ `plan_podcast_text` / `semantic_chunk_to_tts_text`
→ verified canonical Candidate 03 `speaker_emb.npy` and `reference_codes.npy`
→ `TTSEngine.generate(preplanned_text=True, speed=1.0, model_max_chars=800, …)`
→ `ModelLoader.infer` / VieNeu 3.3.0 v3turbo ONNX
→ disk-backed ordered chunk assembly plus boundary-owned V2 pauses
→ exactly one full-waveform `atempo=0.98`
→ Audio Studio fetches and stores the result.

## UI lock

When `podcast_brand_voice_v1` is selected, Audio Studio now:

- disables the ordinary speed field;
- disables TTS Script editing, manual pause buttons, and automatic prosody suggestion;
- replaces generic advanced-value text with “Đang dùng thiết lập tối ưu của Podcast Brand Voice.”

The payload remains backward compatible, and the backend still enforces the profile independently of the UI. Other voices keep adjustable speed, sampling parameters, TTS Script, and manual prosody behavior.

## Internal diagnostic manifest

Every Podcast Brand Voice job writes `data/jobs/<job-id>/podcast_pipeline_manifest.json` before inference. It contains:

- profile and pipeline IDs;
- source-text SHA256;
- verified Candidate 03 array/file/reference-code hashes;
- full effective inference configuration and its SHA256;
- semantic planner version;
- chunk count;
- each exact TTS-text SHA256;
- each boundary type and explicit pause;
- final tempo;
- explicit declaration that generic UI parameters were ignored.

The legacy `plan.json` name remains as a compatibility view of the same data. Neither file is shown in the normal UI.

