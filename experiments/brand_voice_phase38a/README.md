# Phase 38A — Candidate 03 short-source corpus viability pilot

This isolated experiment generates exactly twelve short Vietnamese research
corpus candidates with frozen Candidate 03 conditioning through the already
installed local VieNeu CPU/ONNX path. It is not a production renderer test,
parameter search, long-form test, model download or training run.

`run_candidate03_short_source_pilot.py` runs sequentially with the established
Candidate 03 parameters: temperature 0.82, top-k 25, top-p 0.97, repetition
penalty 1.15, speed 1.0, 240 outer characters, denoise false, reference codes
enabled, and NumPy seed 34001. It forces Hugging Face/Transformers offline
mode: incomplete local model assets cause a failure instead of a download.

The script produces only `audio/*.wav`, `manifest.json`, `manifest.csv`,
`provenance.json`, and `HUMAN_REVIEW.md`. Human QA, not objective metrics,
determines the Stage 0 gate.
