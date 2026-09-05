# Phase 44A — Existing Vietnamese Podcast Voice Search & Casting

Status: **COMPLETE — HUMAN LISTENING PACKAGE READY**

The strategy is to use only released, existing Vietnamese voices with explicit commercial usability, local CPU feasibility, and no reference upload, cloning, blending, adaptation, or DSP. Six ecosystems were screened. Only installed VieNeu V3 Turbo passed the commercial-output, bundled-speaker-rights, existing-preset, and local ONNX CPU gates.

The targeted license gate resolved all eight released male presets as COMMERCIAL-SAFE: Phạm Tuyên, Minh Đức, Thanh Bình, Quang Sơn, Xuân Vĩnh, Thái Sơn, Minh Triết, Đức Trí. The official card covers code, shipped model/voice assets, commercial/monetized preset-generated audio, and disclosed speaker/rightsholder consent. They are legal candidates, not a quality ranking or final shortlist. No Phase 44A renders, normalization, blind package, or human QA have been created yet.

All 24 raw WAVs were rendered sequentially on installed VieNeu 3.3.0 ONNX CPU, one attempt per voice/text, with the same raw inference policy (no identity tuning, DSP, tempo or prosody rescue). `metadata/render_manifest.json` records hashes, duration, sample rate, channels and generation time. Eight PCM16/48-kHz mono combined ABC files use only 1.2 s silent joins and uniform per-combined-file peak normalization to -1 dBFS. Human QA is pending; no winner or web integration was selected.
