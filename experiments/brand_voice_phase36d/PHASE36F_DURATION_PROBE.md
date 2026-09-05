# Phase 36F — VietVoice target duration correction PoC

## Verified public control

`speed` is a public `ModelConfig` field and the documented CLI exposes it as `--speed`. `TTSEngine._prepare_inputs()` computes:

```text
target_audio_duration = target_text_length / speaking_rate / config.speed
```

No public explicit target-duration parameter exists in the installed API. `speed` is therefore the only supported non-source-edit control that directly changes this inference input.

## Exact one-variable setting

The frozen original baseline target, including comma, is retained exactly:

`Một câu chuyện rõ ràng cần được kể liền mạch, có điểm nhấn đúng chỗ.`

All Candidate 03 assets, reference transcript, seed 9527, NFE 32, fuse 1, CPU provider, sample rate, model archive, and preprocessing remain unchanged.

The sole changed public parameter is:

| Parameter | Phase 36D baseline | Phase 36F probe |
|---|---:|---:|
| `speed` | 1.0 | `1.2933333333333332` |

Installed source gives a baseline requested duration of:

```text
reference rate = 87 / 6.96 = 12.5 weighted bytes/s
baseline target duration = 97 / 12.5 / 1.0 = 7.76 s
```

To request exactly 6.0 seconds:

```text
speed = 7.76 / 6.0 = 1.2933333333333332
probe target duration = 97 / 12.5 / 1.2933333333333332 = 6.0 s
```

This is a meaningful but bounded 22.7% duration reduction, based only on the installed implementation rather than an arbitrary speed selection.

## Output and analysis

The no-overwrite one-shot script writes:

- raw output: `experiments/brand_voice_phase36d/output/vietvoice_candidate03_phase36f_duration_probe.wav`
- metrics: `experiments/brand_voice_phase36d/output/vietvoice_candidate03_phase36f_duration_probe_metrics.json`

The metrics JSON includes the required runtime/audio figures and a same-method Phase 36E low-energy comparison against the immutable Phase 36D baseline: 20 ms RMS frames, 10 ms hop, -40 dBFS threshold, and 80 ms minimum region. It reports leading silence, total internal low-energy duration, longest internal gap, and count of major (>=250 ms) internal gaps.

## Manual execution

The agent environment is not reliable for a 140-second CPU inference. Run exactly once in a real terminal:

```bash
cd '/home/tung/ai voice' && experiments/brand_voice_phase36d/.venv_py312/bin/python experiments/brand_voice_phase36d/run_vietvoice_duration_probe.py
```

No model download, VieNeu generation, retry, post-processing, or production change is performed by this command.
