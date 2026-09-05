# Phase 43B — Experimental Podcast Voice Integration

Status: **INCOMPLETE — HUMAN QA NOT READY**

The frozen experimental identities are `podcast_deep_warm` (Phase 43A Voice 01), `podcast_warm_storyteller` (Voice 06), and `podcast_soft_baritone` (Voice 07). `backend/app/tts/podcast_voices.py` reconstructs each exact 192-d embedding from the audited VieNeu 3.3.0 V3 Turbo asset, checks its Phase 43A embedding SHA256, and uses the shared Thanh Bình reference-code anchor. The API exposes them as Experimental Podcast Voices and `/api/tts` passes the verified profile directly to `TTSEngine`; an unknown ID remains an explicit error.

The frontend places the three additive choices in **Giọng Podcast thử nghiệm**. Stable IDs remain usable through the existing selection persistence.

No DSP, tempo, semantic planner, Candidate 03, or default-voice behavior was changed. Python compilation passed.

Smoke renders are incomplete because the local command runner terminated each CPU inference process at its 30-second limit. Present: Voice 01 unseen A/B and Voice 06 unseen A. Missing: Voice 06 unseen B and Voice 07 unseen A/B. Do not claim human QA until all six are valid.
