# Phase 42D — Personal Voice Corpus QA + RVC CPU Feasibility

Status: **COMPLETE — CORPUS GATE PASS; CPU TRAINING IMPRACTICAL ON THIS HOST**

## Scope and privacy

This phase audited a user-supplied private source locally and measured the pinned upstream RVC CPU training path. It did not run TTS, produce conversion audio, alter Synthetic Candidate 03, alter the Phase 41E/41F/41H podcast stack, or claim voice quality. Private source audio and every private derivative remain gitignored; no upload, API, or telemetry was used.

## Source and corpus QA

The supplied AAC M4A was copied byte-identically to `source/thuam24.m4a`: 12,699,445 bytes, mono 48 kHz AAC LC, 1479.296 seconds / **24.6549 minutes**, SHA256 `fbeb837f392fa283860e037c27befa08f23631ae09136900eed59d00cbd1d4ba`.

Local decoding produced 40-kHz mono PCM. Conservative energy-based QA/segmentation created manifests and a review playlist, only auto-rejecting clear technical failures.

| category | count | duration | minutes |
| --- | ---: | ---: | ---: |
| raw | — | 1479.296 s | 24.6549 |
| AUTO_PASS | 321 | 1097.376 s | **18.2896** |
| REVIEW | 78 | 213.460 s | 3.5577 |
| REJECT_TECHNICAL | 33 | 8.600 s | 0.1433 |

The conservative usable estimate is AUTO_PASS only: **18.2896 minutes**. Global PCM measurements: peak 1.0, RMS -17.77 dBFS, DC offset 0.0000221, clipped-sample ratio 0.000000676, silence ratio 30.97%, and long-silence ratio 17.78%. The corpus gate passes; REVIEW material was not silently added to the conservative estimate.

## Reproducible RVC preparation

The upstream RVC source is pinned at commit `81eed5e8f68b6bed1789f682fe78cdd324495afc` (MIT). The isolated `.venv-phase42d-rvc` uses Python 3.12 and Torch `2.4.1+cpu`; CUDA is false. The verified official CPU Torch wheel is 194,846,757 bytes, SHA256 `8800deef0026011d502c0c256cc4b67d002347f63c3a38cd8e45f1f445c61364`.

Single-process preprocessing converted 432 parent segments into 576 40-kHz and 16-kHz slices. CPU Parselmouth F0 (`pm`) created matching F0/F0NSF arrays for 524 slices. The remaining 52 were all-zero/failed F0 cases recorded by upstream logs and were excluded rather than fabricated.

HuBERT/content extraction used the public `lj1995/VoiceConversionWebUI` HuBERT asset, pinned to repository revision `e6d0c1a17da07c33557852f9dfa2bd44cc75737d`. `assets/hubert_base/pytorch_model.bin` is 189,206,711 bytes, SHA256 `cc8c20f4b90a520757260197a3ff2505705a7adbd20ad9eeaa4e1a9b38442ef5`. The exact local upstream command was:

```sh
/home/tung/ai\ voice/.venv-phase42d-rvc/bin/python -m train.dataset.extract_hubert_feature cpu 1 0 /home/tung/ai\ voice/experiments/personal_voice_phase42d/features/rvc_prep v2 false
```

It completed successfully: **576/576** 768-dimensional content features, zero failures. The intersection used for training is therefore 524 slices with WAV + HuBERT + F0 + F0NSF artifacts. The feature directory occupies 514 MiB.

## Tiny CPU training measurement

`prepare_cpu_benchmark.py` made a reproducible 16-slice, batch-1, one-epoch filelist and config under upstream `rvc_source/logs/phase42d_cpu_benchmark`. It used no pretrained G/D checkpoint, intentionally: this was an initialization/compute feasibility benchmark only, not a quality-training run.

The exact train command was:

```sh
/usr/bin/time -v /home/tung/ai\ voice/.venv-phase42d-rvc/bin/python -m train.train -e phase42d_cpu_benchmark -sr 40k -f0 1 -bs 1 -g '' -te 1 -se 1 -pg '' -pd '' -l 1 -c 0 -sw 0 -v v2
```

The sandbox initially blocked the local `torch.distributed` rendezvous socket; the same CPU-only command was then allowed outside that sandbox. The upstream trainer initialized successfully and TensorBoard scalar events prove **16/16 update steps** (steps 0–15). The intervals between successive completed scalar events were mean **3.196 s/step**, median 3.207 s/step (range 2.771–3.468 s). This excludes model startup and therefore is an optimistic steady-state estimate.

The terminal/time wrapper did not yield its final resource summary and no post-epoch G/D checkpoint appeared. This happened after the 16 updates, while host availability had fallen to about 2.7 GiB and swap usage had risen from about 2.5 GiB to about 3.4 GiB. Consequently, exact process peak RSS is unavailable; it must not be inferred from host-wide memory. The lack of a saved checkpoint means this was a successful step-level feasibility measurement, not a clean, reproducible training completion.

| projection from 3.196 s/step | estimated elapsed time |
| --- | ---: |
| 1,000 steps | 3,196 s / **53 min 16 s** |
| 5,000 steps | 15,980 s / **4 h 26 min 20 s** |

These figures exclude startup, checkpoint serialization, and recurrent memory/swap pressure, so they are lower bounds rather than production schedules.

## Decision

The CPU RVC stack is not a technical import/model blocker: it extracted content features and executed all 16 measured training updates. It is nevertheless **impractical for safe, repeatable training on this host**: batch size was already one, memory headroom narrowed materially, swap increased, and the benchmark did not finish a clean checkpoint-save cycle. Do not start a multi-thousand-step CPU run here without materially more memory/headroom or an appropriate accelerator.

No conversion WAV or quality result exists. Candidate 03 stays unchanged and remains a candidate; no identity or production-voice claim is made from this phase.

## Final machine-readable summary

PHASE 42D STATUS: COMPLETE — CORPUS GATE PASS; CPU TRAINING IMPRACTICAL ON THIS HOST

RAW MINUTES: 24.6549

CONSERVATIVE USABLE MINUTES: 18.2896

HUBERT/CONTENT EXTRACTION: PASS — 576/576 v2 768-dimensional content features; zero failures

TINY CPU TRAINING: PARTIAL PASS — 16/16 update steps recorded; post-epoch checkpoint/save completion not observed

MEASURED SECONDS/STEP: 3.196 mean steady-state seconds/step (median 3.207; 15 inter-step intervals)

ESTIMATED 1K TRAINING TIME: 53 min 16 s lower-bound compute estimate

ESTIMATED 5K TRAINING TIME: 4 h 26 min 20 s lower-bound compute estimate

CPU/RAM/SWAP VERDICT: CPU kernel path works, but batch-1 training materially reduces memory headroom and increases swap; clean checkpoint completion was not observed. Peak RSS unavailable because the timing wrapper did not return a final summary.

FINAL DECISION: CPU TRAINING IMPRACTICAL

REPORT PATH:
experiments/personal_voice_phase42d/PHASE42D_REPORT.md

CHECKPOINT PATH:
experiments/personal_voice_phase42d/PHASE42D_CHECKPOINT.md
