Phase 41A — Embedding Optimization Experiment (black-box)

Purpose
-------
This experiment tests whether the installed VieNeu ONNX CPU runtime (VieNeu v3.3.0)
can be used to surface a new, distinctive synthetic speaker by optimizing a
`speaker_emb` vector without training or target human recordings.

IMPORTANT constraints
- 0 VND (no paid datasets or cloud)
- CPU-only (Intel i9-13900H, 16 GB RAM, Intel Iris Xe)
- Candidate B (the canonical baseline) is never modified
- No model downloads or training occur automatically in these scripts
- Final acceptance is human listening in Vietnamese; the script only proposes candidates

Files created
- `experiments/brand_voice_phase41a/opt_embedding_search.py`  (main runner)
- `experiments/brand_voice_phase41a/config.json`  (default parameters)

Prerequisites (exact)
1) Python 3.10+ in project `.venv` (the workspace already provides one).
2) Installed package: `vieneu` with the ONNX/CPU runtime available in that environment. The script uses the same asset `voices_v3_turbo.json` shipped with `vieneu`.
3) `soundfile` (pysoundfile) available if you intend to actually run generation.

Exact command
-------------
To run the experiment (DO NOT RUN unless you accept local audio generation and CPU cost):

```bash
python experiments/brand_voice_phase41a/opt_embedding_search.py --config experiments/brand_voice_phase41a/config.json
```

To resume from an existing checkpoint:

```bash
python experiments/brand_voice_phase41a/opt_embedding_search.py --config experiments/brand_voice_phase41a/config.json --resume experiments/brand_voice_phase41a/runs/checkpoint.npz
```

Expected resources (approx)
- RAM: 8–16 GB peak depending on population / parallelism. Single-process usage typically fits within 16 GB.
- Disk: ~1 GB for temporary WAVs and checkpoints; grows with number of saved iterations.
- CPU: Intel i9-13900H recommended. Single-run evaluation per candidate currently matches prior VieNeu RTF (~0.5–0.7), so budget accordingly.
- Time: depends on `population` × `iterations`. Example: population=32, iterations=100, 3 texts → ~32*100*per-eval-time. If per-eval ~8s → ~7 hours. You can reduce population and iterations for quick tests.

Checkpoint / resume
-------------------
- Checkpoints are saved to `experiments/brand_voice_phase41a/runs/checkpoint.npz` and per-iteration JSON files.
- To resume, pass `--resume PATH_TO_CHECKPOINT` argument.
- Interrupt safely with `Ctrl+C` — the script traps SIGINT and writes a checkpoint.

Files produced when run
- `experiments/brand_voice_phase41a/runs/iter_XXXX.json` (iteration summary)
- `experiments/brand_voice_phase41a/runs/checkpoint.npz` (resume state)
- `experiments/brand_voice_phase41a/runs/best_embeds.npy`, `best_scores.npy` (final archive)
- `experiments/brand_voice_phase41a/runs/*.wav` (temporary/generated WAVs, if generated)

Stop / cleanup procedure
- To stop gracefully: press `Ctrl+C`. The script will checkpoint and exit.
- To fully remove artifacts: delete the `experiments/brand_voice_phase41a/runs/` directory.

Human acceptance gate
- The script outputs a short list of top candidate embeddings (npy files). For any candidate, produce a blind listening package of 3 texts (same texts used during optimization) and ask at least 5 Vietnamese listeners to rate:
  1. Distinctiveness (Is this a recognizable person?)
  2. Naturalness (Any artifacts? Natural Vietnamese?)
  3. Stability (Same person across texts?)
  4. Podcast fit (philosophy/reflective narration suitability)
  5. Long-form comfort (Would this be pleasant for 20–30 minute listening?)

Acceptance rule (manual):
- A candidate must be clearly preferred over Candidate B by a majority on distinctiveness while preserving naturalness and long-form comfort. No automated metric overrides human listening.

Documented method vs experimental hypothesis
-------------------------------------------
- Documented methods used: evolutionary search (ES) over embeddings; use of speaker encoders for embedding comparisons; embedding-space OOD penalties.
- Our experimental hypothesis: optimizing `speaker_emb` in the VieNeu generator space (with strong stability and OOD penalties) can surface perceptually novel, stable synthetic persons without retraining. This is a hypothesis to test — not an established method guaranteeing success.

If the optimization has no meaningful objective space (fails repeatedly by producing artifacts or near-baseline-only candidates), do NOT promote the candidates — report the limitation and consider the heavier routes (StyleTTS prior training or VITS multi-speaker training) as described in Phase 41A audit.

Support
-------
If you want me to produce a ready-to-run invocation script tuned to a smaller quick-test budget (e.g., population=8, iterations=10), tell me and I will create it.

"""
