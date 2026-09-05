# Phase 30H — Synthetic Reference Creation

Research only. No package, environment, model, checkpoint, dataset, or synthetic audio was installed, downloaded, or generated.

Status: SYNTHETIC_REFERENCE_PATH_EXPERIMENTAL.

The sole primary path is Qwen3-TTS VoiceDesign (English) → clean synthetic WAV → VieNeu reference encoder → Vietnamese VieNeu output. Qwen creates a described synthetic voice and documents VoiceDesign-to-reusable-clone-prompt. VieNeu accepts waveform reference audio without a reference-language field. Cross-language conditioning has not been validated; that is the Phase 30I test.

See voice_design_landscape.md, vietnamese_bridge_options.md, synthetic_reference_architecture.md, technology_comparison.md, and phase30h_decision.md.

