# Phase 36H — continuity/pronunciation balance probe

## Single permitted change

Phase 36H keeps the Phase 36G no-comma target exactly:

`Một câu chuyện rõ ràng cần được kể liền mạch có điểm nhấn đúng chỗ.`

Only the documented public `speed` setting changes, from Phase 36G `1.2933333333333332` to:

```text
7.68 / 6.50 = 1.1815384615384614
```

The installed formula is `target_duration = 96 / 12.5 / speed`, giving exactly 6.50 requested seconds. Candidate 03 reference WAV/transcript, seed 9527, NFE 32, fuse 1, CPU provider, model, sample rate and all preprocessing settings are unchanged.

## Output / analysis

- WAV: `experiments/brand_voice_phase36d/output/vietvoice_candidate03_phase36h_balance_probe.wav`
- metrics: `experiments/brand_voice_phase36d/output/vietvoice_candidate03_phase36h_balance_probe_metrics.json`

The one-shot script will measure actual duration, synthesis time/RTF/RSS, peak/RMS/clipping and the same 20 ms RMS / 10 ms hop / -40 dBFS / >=80 ms low-energy analysis used in Phase 36F/36G. The metrics include the direct Phase 36D vs 36G vs 36H comparison.

## Manual execution

Run only once in a real terminal:

```bash
cd '/home/tung/ai voice' && experiments/brand_voice_phase36d/.venv_py312/bin/python experiments/brand_voice_phase36d/run_vietvoice_balance_probe.py
```

The script refuses overwrite and does not download models, generate VieNeu, modify source, post-process output, or change production.
