# Phase 36J — Vietnamese-to-Vietnamese bridge PoC

The immutable Phase 36I bridge is valid: 4.960000 s, 48 kHz mono, peak
0.84436035, RMS 0.09135528, zero clipped samples. It remains untouched.

The installed VietVoice formula, using its current `pause_punctuation` regex,
computes a weighted reference length of 105 and target length of 97. Therefore
the Vietnamese bridge yields a speaking rate of 21.169354839 weighted bytes/s
and a requested target duration of 4.582095238 s at `speed=1.0`.

The prepared script uses exactly one public clone inference with:

- reference transcript: `Hôm nay chúng ta cùng đi qua một câu chuyện ngắn với giọng kể rõ ràng và tự nhiên.`
- target: `Một câu chuyện rõ ràng cần được kể liền mạch, có điểm nhấn đúng chỗ.`
- `speed=1.0`, `random_seed=9527`, `nfe_step=32`, `fuse_nfe=1`, CPUExecutionProvider, and all remaining installed defaults.

Run manually from a real terminal (not a Codex sandbox):

```bash
cd '/home/tung/ai voice' && experiments/brand_voice_phase36d/.venv_py312/bin/python experiments/brand_voice_phase36i/run_vietvoice_vietnamese_bridge_speed1.py
```

The script refuses to overwrite the sole Phase 36J output. It writes only:

- `output/vietvoice_candidate03_vietnamese_bridge_speed1.wav`
- `output/vietvoice_candidate03_vietnamese_bridge_speed1_metrics.json`

It does no waveform post-processing. The metrics JSON uses the same Phase
36F/36G/36H low-energy method: mono, 20 ms RMS frames, 10 ms hop, -40 dBFS,
minimum region 80 ms, with major gaps at least 250 ms.
