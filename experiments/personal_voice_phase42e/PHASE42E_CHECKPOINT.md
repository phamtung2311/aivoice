# Phase 42E checkpoint / final decision record

Status: **COMPLETE — C: NO PRACTICAL 16-GB LOCAL TRAINING PATH**

## Audited directions; do not repeat

- **A: RVC reduced configuration.** Existing RVC commit `81eed5e8f68b6bed1789f682fe78cdd324495afc`, existing HuBERT public asset revision `e6d0c1a17da07c33557852f9dfa2bd44cc75737d`, asset SHA256 `cc8c20f4b90a520757260197a3ff2505705a7adbd20ad9eeaa4e1a9b38442ef5`. Static upstream configuration count shows v1-32k reduces counted FP32 weights+gradients+Adam by about 260 MiB vs v2-32k, but keeps segment size 12,800 and upstream's hard-coded four workers/prefetch eight. No supported gradient checkpointing, PEFT, CPU-loader knob, or memory-safe full-checkpoint path was found. Reject: not materially safer than Phase 42D.
- **B: parameter-efficient adaptation.** PlayVoice `lora-svc` code is MIT, but its own README says LoRA is not fully implemented; it targets singing and depends on external pretrained assets whose exact commercial provenance was not pinned. Reject.
- **C: lightweight VC.** MeanVC2 has Apache-2.0 code and 18M parameters, but official installation/training requires CUDA 12.1 and GPU scripts; its multiple auxiliary weights are not yet fully provenance-pinned. Reject: CPU training remains theoretical.

## What did and did not run

- Used existing `.venv-phase42d-rvc` only for static parameter construction; no new environment, download, install, private-audio subset, feature extraction, train step, checkpoint save/reload, or conversion audio.
- No selected benchmark candidate exists. This is an intentional early stop because no path met the material-improvement gate.
- Candidate 03 and `experiments/brand_voice_phase41h/audio/v2_natural.wav` remain unchanged; carrier SHA256 remains `66a51b4ccedccec6016cc778ddafceaf4c0d42fad741ad36f711a7d25ef8dce5`.

## Exact next action

Do not resume local personal-voice training on this 16-GB host. Preserve the local ignored corpus for future hardware or an independently validated/reproducible method. Continue the frozen synthetic brand-voice route for production.
