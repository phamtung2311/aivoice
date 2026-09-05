# Phase 42E — Memory-Efficient Personal Voice Adaptation Audit

Status: **COMPLETE — NO PRACTICAL 16-GB LOCAL TRAINING PATH**

## Objective and prior blocker

Phase 42E asks a narrower question than Phase 42D: whether a trainable, local, commercially suitable personal-voice path is *materially safer and more reliable* on this i9-13900H / 16-GB RAM / Intel Iris Xe host. It does not ask whether RVC can execute on CPU.

Phase 42D already established that CPU RVC can execute: 16/16 update steps were recorded at 3.196 mean steady-state seconds/step. It also established the blocker: batch size was already one, host memory headroom narrowed to about 2.7 GiB, swap grew by about 0.9 GiB, and a clean post-epoch checkpoint save was not observed. That is the baseline used here; no unsupported Phase 42D resource figure is inferred.

No TTS, VC conversion, full training, UI/product change, cloud/API action, or external upload of owner material occurred in this phase.

## Preserved private data and prosody carrier

The local/private corpus is unchanged. It remains 24.6549 raw minutes and 18.2896 conservative AUTO_PASS minutes (321 parent segments; 524 slices with the complete F0 training intersection). Existing Phase 42D private source, segments, features, checkpoints, and outputs remain ignored by Git and were not copied or uploaded.

The frozen carrier was verified read-only and not overwritten:

- `experiments/brand_voice_phase41h/audio/v2_natural.wav`
- SHA256 `66a51b4ccedccec6016cc778ddafceaf4c0d42fad741ad36f711a7d25ef8dce5`
- duration 450.685375 s

It remains the preferred prosody carrier if a future, independently approved VC path becomes viable. Candidate 03 remains a candidate; no identity or production claim changes.

## Candidate shortlist and audit matrix

The audit was limited to the requested three directions. No fourth framework was explored or installed.

| Direction / candidate | Code and asset provenance | Memory-reduction evidence | Local CPU training and speech fit | Decision |
| --- | --- | --- | --- | --- |
| A — upstream-compatible RVC v1 32k | Existing pinned RVC source `81eed5e8f68b6bed1789f682fe78cdd324495afc`; code MIT. Existing HuBERT asset is pinned at public `lj1995/VoiceConversionWebUI` revision `e6d0c1a17da07c33557852f9dfa2bd44cc75737d`, SHA256 `cc8c20f4b90a520757260197a3ff2505705a7adbd20ad9eeaa4e1a9b38442ef5`. No new weight was downloaded. | Static, upstream-config count: v1-32k G+D = 91,262,624 parameters; v2-32k = 108,291,300. At FP32, weights + gradients + Adam moments differ by about **260 MiB** (1,392 MiB vs 1,652 MiB). Both upstream configs use `segment_size=12800`; v1 32k vs v1 40k differs only about 0.25 MiB of weights+moments. | CPU path exists, but the upstream trainer retains 4 workers and `prefetch_factor=8`; no documented CPU worker/prefetch switch, gradient checkpointing, LoRA/adapter, or memory-safe full-state checkpoint mode exists. `-l 1` retains only the latest checkpoint but still serializes G/D plus optimizer states. The 260-MiB static reduction is not material against the Phase 42D swap/reliability blocker. | **Rejected before benchmark:** no evidence of materially safer peak memory or a clean-save solution; v1 requires incompatible 256-dimension features and would need new compatible extraction. |
| B — parameter-efficient adaptation: PlayVoice `lora-svc` | Repository code is MIT, but the README explicitly says LoRA is **not fully implemented**. It requires external Whisper, a Google Drive speaker encoder, and a separate pretrained model; exact weights/licenses/provenance are not pinned here. | No implemented adapter/LoRA path to measure. Its stated target is singing voice conversion. | No supported CPU-training evidence; unsuitable speech/podcast target and unverified auxiliary-weight commercial provenance. | **Rejected:** implementation and provenance gates fail. |
| C — lightweight VC: ASLP-lab MeanVC2 | Code/model license is Apache-2.0. It advertises about 18M parameters and speaker-specific fine-tuning, but requires multiple auxiliary model families (WeNet/Fast-U2++, ECAPA-TDNN, WavLM, Vocos, FunASR/ModelScope assets). Their exact weight revisions/licenses would need a separate gate. | Project claims an approximately 60% *GPU* peak-memory reduction from its chunking design and 18M parameters. This is not CPU-training evidence. | Official quick start installs CUDA 12.1 PyTorch; official training scripts are single/multi-GPU shell commands. CPU evidence is inference-only (a Windows CPU executable); no Linux CPU adaptation benchmark/path is documented. | **Rejected:** CPU training is theoretical for this host, and required asset provenance is not fully pinned. |

Primary source evidence: [RVC CLI](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI/blob/main/docs/en/cli.md), [TinyVC README](https://github.com/uthree/tinyvc), [lora-svc README](https://github.com/PlayVoice/lora-svc), [MeanVC2 README](https://github.com/ASLP-lab/MeanVC2), and [Seed-VC fine-tuning documentation](https://github.com/pufferFish-sz/seed-vc-fine-tune). TinyVC was considered only as a static comparator and not added to the table because its own README requires a GPU environment and substantial data for scratch learning. Seed-VC is likewise not a PEFT escape hatch: its documented fine-tune is full 196M-parameter training on an RTX 3060 and the fork is GPL-3.0.

## RVC code/config evidence

The static parameter audit instantiated only existing upstream model/config pairs; it did not train them. Results:

| upstream-compatible config | G+D parameters | FP32 weights | Adam moments | weights + gradients + Adam moments |
| --- | ---: | ---: | ---: | ---: |
| v1 32k | 91,262,624 | 348.14 MiB | 696.28 MiB | 1,392.56 MiB |
| v1 40k | 91,328,800 | 348.39 MiB | 696.78 MiB | 1,393.56 MiB |
| v2 32k | 108,291,300 | 413.10 MiB | 826.20 MiB | 1,652.40 MiB |
| v2 48k | 109,049,060 | 415.99 MiB | 831.98 MiB | 1,663.96 MiB |

This isolates persistent model/optimizer-state scale, not activation/data-loader/checkpoint peak RSS. The best legitimate static reduction is about 260 MiB (about 16% of this counted state), while Phase 42D's failure mode included host-memory pressure, swapping, and checkpoint serialization. Since 32k retains the same 12,800-sample training segment and the trainer hard-codes four workers with prefetch eight, it does not provide the required evidence of a materially safer overall memory profile.

The local upstream code contains no gradient-checkpointing, LoRA, adapter, or CPU-worker/prefetch command-line control. TensorBoard is instantiated unconditionally. Both `save_checkpoint` functions serialize model state and optimizer state; `-l 1` changes retention only, not serialization peak. Disabling TensorBoard or retaining fewer old files would save disk/log overhead, not establish a clean checkpoint-save cycle under the observed memory pressure. Custom architectural reduction or an ad-hoc checkpoint format was not attempted because it would no longer test the supported upstream training/checkpoint path.

## Selection and benchmark decision

**Selected candidate/configuration: NONE.** This is an intentional early stop under the Phase 42E selection rule. No candidate supplied evidence of a materially better memory/reliability path, so installing an environment or running 20–100 training steps would spend private-data/compute budget without a justified route to a sustainable training run.

Consequently:

- Environment: no new `.venv-phase42e-*`; existing `.venv-phase42d-rvc` was reused only for static model construction because it already contains the pinned upstream code and CPU Torch.
- Dataset/subset: **not created**. No owner-audio subset, feature copy, or new extraction was needed.
- Benchmark: **not run**. No steps, peak RSS sample, checkpoint save, checkpoint reload, resume step, or converted output exists.
- No quality test: no model had first passed the required clean train/save/reload gate.

## Required comparison with Phase 42D

| Metric | Phase 42D RVC | Phase 42E candidate |
| --- | ---: | ---: |
| candidate | RVC v2 architecture CPU run | none selected |
| batch | 1 | not run |
| sec/step | 3.196 | not run |
| start MemAvailable | not recorded as a Phase 42D final metric | not run |
| lowest observed MemAvailable | about 2.7 GiB | not run |
| swap growth | about 0.9 GiB | not run |
| checkpoint save | not cleanly observed | not run |
| checkpoint reload | not tested | not run |
| checkpoint size | not obtained | not run |
| clean exit | incomplete/uncertain | not run |
| static training state | not a Phase 42D measured metric | RVC v1-32k would reduce counted FP32 weights+gradients+Adam by about 260 MiB vs v2-32k; insufficient evidence for a pass |

## Full-training estimate and sustained-run verdict

No Phase 42E full-training estimate is valid because no candidate completed the required benchmark/save/reload cycle. The Phase 42D 1k/3k/5k projections must not be repurposed for a hypothetical configuration. No safe checkpoint-overhead, disk-growth, or sustained-run likelihood can be calculated for an unbenchmarked path.

The primary answer is therefore **no**: on current evidence, there is no materially more memory-efficient, reliable, commercially defensible local personal-voice training path for this 16-GB host that should be allowed to run for hours.

## Risks and recommended next phase

RVC remains technically viable on better-resourced hardware; Phase 42E does not call it broken. Future work would require a separately approved plan on hardware with materially more memory or an accelerator, then a clean save/reload benchmark with revision-pinned and license-audited base/auxiliary weights. Do not resume personal adaptation training on this host merely by lowering sample rate or retaining fewer checkpoints.

Keep the private corpus for such a future path. For present production work, return to the frozen synthetic brand-voice direction: Candidate 03 + Phase 41E `v3_semantic_focus` + Phase 41F 0.98x + Phase 41H V2 natural podcast cadence.

## Commands executed and files changed

Read-only/audit commands executed:

- read Phase 42C/42D reports and checkpoint, local RVC code/configs, frozen-carrier SHA256/duration, Git ignore/status, and host memory snapshot;
- browser research limited to the three direction classes and primary project repositories/documentation;
- `experiments/personal_voice_phase42e/inspect_rvc_configs.py` using existing Phase 42D environment, which instantiated upstream configs to count parameters only.

Files created/changed by this phase:

- `experiments/personal_voice_phase42e/inspect_rvc_configs.py` — public static audit utility only;
- `experiments/personal_voice_phase42e/PHASE42E_REPORT.md`;
- `experiments/personal_voice_phase42e/PHASE42E_CHECKPOINT.md`.

The worktree was already dirty with unrelated product/history changes. No frontend, Studio, Voice Lab, API, default-model, production configuration, Phase 42D artifact, or frozen carrier was modified.

## Final decision

**FINAL DECISION: C — NO PRACTICAL 16-GB LOCAL TRAINING PATH.**
