# Phase 36G — combined continuity probe

## Exact test

This is one interaction test, not a grid.

- target: `Một câu chuyện rõ ràng cần được kể liền mạch có điểm nhấn đúng chỗ.`
- reference WAV: frozen Phase 33C Candidate 03 canonical WAV
- reference transcript: frozen canonical English transcript
- speed: `1.2933333333333332`
- seed: 9527
- NFE / fuse: 32 / 1
- provider: CPUExecutionProvider
- model cache, sample rate, preprocessing, `pause_punctuation`, max chunk duration and crossfade: unchanged

The only difference from Phase 36F is removal of the comma. The only differences from Phase 36E are the pre-established duration-correction speed and its resulting duration.

## Expected duration

The installed implementation produces zero `pause_punctuation` regex matches for both strings. The no-comma text is 96 UTF-8 bytes; the frozen reference is 87 bytes / 6.96 s = 12.5 weighted bytes/s.

```text
96 / 12.5 / 1.2933333333333332 = 5.938144329896907 s
```

Expected target duration is therefore **5.938144 s**, slightly below the Phase 36F 6.000000-second request.

## Output / metrics

- output: `experiments/brand_voice_phase36d/output/vietvoice_candidate03_phase36g_combined_continuity.wav`
- metrics: `experiments/brand_voice_phase36d/output/vietvoice_candidate03_phase36g_combined_continuity_metrics.json`

The one-shot script refuses to overwrite output. Metrics record audio/runtime/RSS plus the exact Phase 36F low-energy method: mono waveform; 20 ms RMS frames; 10 ms hop; -40 dBFS; 80 ms minimum region; major gap >=250 ms. It embeds the direct 36D vs 36F vs 36G comparison.

## Execution

CPU render is about 100 seconds and must run in a real terminal, not the coding-agent sandbox:

```bash
cd '/home/tung/ai voice' && experiments/brand_voice_phase36d/.venv_py312/bin/python experiments/brand_voice_phase36d/run_vietvoice_combined_continuity_probe.py
```

No VieNeu generation, source patch, post-processing, model download, or production modification occurs.
