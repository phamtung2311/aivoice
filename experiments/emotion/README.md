# Phase 28A — Emotion / Expression feasibility experiment

This is a developer-only, local experiment. It reuses `backend.app.tts.engine.TTSEngine`; it does not call FastAPI or touch user history, saved voices, Voice Lab, Audio Studio, or production UI.

Run from repository root with the project virtual environment:

```bash
.venv/bin/python experiments/emotion/run.py --only thoughtful_neutral --only thoughtful_ellipsis
```

To generate the small fixed comparison set, omit `--only`. To use an existing voice, add `--voice "VOICE_NAME"`. Outputs are written to `experiments/emotion/output/` and are intentionally Git-ignored. Every run writes `manifest.json` and `LISTENING_INDEX.md`, including the original sentence, transformed text, API-normalized text, exact wrapper input/chunks, parameters, WAV filename, and supporting audio metrics.

The experiment uses only documented installed V3 Turbo inline cues: `[cười]`, `[thở dài]`, and `[hắng giọng]` (and their documented English equivalents). It does **not** assert support for arbitrary tags such as `[warm]` or `[happy]`.
