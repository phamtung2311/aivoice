# Phase 36L — V-TTS install/API/CPU audit

## Status

Audit only: no checkout, venv, dependency, model download, or synthesis was
performed. Candidate 03 and production are unchanged.

**RESEARCH ONLY — STOP BEFORE CHECKOUT / INSTALL / DOWNLOAD.**

The GitHub code is CC BY-NC 4.0 and excludes commercial use. In addition, the
inspected source hard-codes a Hugging Face Space ID whose owner/model-card/asset
terms could not be independently reconciled with the searchable similarly named
Spaces. The exact model release, per-file sizes, hashes, and weight terms are
therefore unresolved.

## Repository and licence

- Repository inspected: `https://github.com/tronghieuit/v-tts`.
- Proposed reproducible checkout: release `v1.0.5`, short commit `a5e77a1`,
  released 06 April 2026. The audited release page did not expose a full SHA.
- The public `dev` source was inspected for API details, but is not proven
  byte-identical to `v1.0.5`.
- `LICENSE` is Creative Commons Attribution-NonCommercial 4.0 International:
  attribution required and commercial use prohibited.
- No separate model-weight or generated-output terms were found. Absence is not
  a grant; all V-TTS output remains research-only.

## Verified zero-shot API

The public `v_tts/zeroshot.py` implements `ZeroShotTTS`:

```python
tts = ZeroShotTTS(checkpoint_path=None, config_path=None, device="cpu")
tts.clone_voice(text, reference_audio, output_path="output.wav",
                noise_scale=0.667, noise_scale_w=0.8, length_scale=1.0)
```

The lower-level `synthesize(text, reference_audio, ...)` returns audio and
sample rate. There is no reference-transcript argument. The source documents a
clean, single-speaker 3–10 second arbitrary-language reference.

Candidate 03 can be passed unchanged:

`experiments/brand_speaker_phase33c/baseline_anchor/BRAND_CANDIDATE_03_BASELINE/qwen_source.wav`

It is PCM16 WAV, 24 kHz mono and 6.960 seconds. The code uses original sample
rate for its speaker encoder and internally resamples for style mel extraction;
no conversion is required or authorized.

## Architecture and Vietnamese frontend

The clone path extracts a separate 512-d speaker embedding and 128-d
prosody/style embedding from the reference. It uses `ProsodyPredictor` in a
single `SynthesizerZeroShot.infer()` call with Vietnamese phone, tone, and
language IDs. Normal TTS is a separate fixed-speaker path.

For a supplied short text, the inspected clone method has no sentence splitting,
independent subcalls, silence concatenation, or crossfade. It normalizes Unicode
and Vietnamese numbers/dates/times/currency, then uses `viphoneme.vi2IPA` with
a character-IPA fallback. Punctuation becomes frontend tokens; comma/semicolon/
colon are marked short-pause punctuation and `. ! ? …` as stops. The source adds
no fixed silence; learned duration determines any pause. Long-text behavior is
not established and must not be assumed.

## CPU and compatibility

- Direct PyTorch FP32 path; not ONNX. CPU is explicitly supported and CUDA is
  optional. No BF16/FP16 requirement or documented Intel-specific acceleration.
- Published components: 74.8M parameters, approximately 285 MB FP32. The
  project claims CPU RTF 0.236–0.475 on i5-14500; this is unverified here.
- The short single-call PoC should be memory-safe in 16 GB by architecture, but
  exact peak RSS is unknown until a provenance-cleared install.
- Source declares Python >=3.8, classifiers only through 3.11. Existing
  Python 3.12.14 at `experiments/brand_voice_phase36d/python312/bin/python3.12`
  is the sensible isolated candidate, but compatibility is not yet proven.
- Locked requirements include torch/torchaudio 2.5.1, librosa 0.9.2,
  soundfile 0.13.1, viphoneme, underthesea, vinorm and huggingface_hub. ffmpeg
  is only shown for optional conversion; the code uses librosa/soundfile.

## Minimal model asset plan — unverified, not downloaded

The inspected source requests only these Space files for zero-shot clone:

| Path | Purpose | Size/hash |
| --- | --- | --- |
| `pretrained/zeroshot/G_175000.pth` | synthesizer/style/prosody checkpoint | Not published/verified |
| `pretrained/zeroshot/config.json` | architecture/sample-rate config | Not published/verified |
| `pretrained/hasp/pytorch_model.bin` | speaker encoder | Not published/verified |

No normal multi-speaker checkpoint, demo audio, dataset, training weights,
WebUI, or ONNX deployment is needed. The source calls the mutable Space ID
`v-tts/v-zeroshot-voice-cloning`; that exact owner/revision must be proven before
download. Published coarse figures conflict (~285 MB FP32, ~100 MB first-run
model claim), so total download cannot be reported reliably. Budget at least
285 MB model weights plus a CPU PyTorch environment, with exact disk/RAM measured
only after provenance approval.

## Future single diagnostic and gate

The only future target is:

> Giọng kể vững vàng dẫn người nghe đi qua những ý tưởng quan trọng.

It contains 14 Vietnamese words, no names/numbers/English, and one final stop.
Reject immediately unless listening passes all: correct pronunciation; clearly
better continuity than VieNeu/VietVoice; one coherent synthetic speaker;
character/authority; no robotic stop-start; and enough interest to continue.
No tuning or long-form work follows a failure.

## Next approved action only

Do not use auto-download or `pip install git+...`. If approved, first make only
this small pinned source checkout, then stop before dependency/model download:

```bash
mkdir -p 'experiments/brand_voice_phase36l/source' && \
git clone --depth 1 --branch v1.0.5 https://github.com/tronghieuit/v-tts.git \
  'experiments/brand_voice_phase36l/source/v-tts-v1.0.5'
```

Compare that tag's actual Space/model revision and licensing with a model card
and file manifest. If they are not unambiguous, reject V-TTS as unauditable.
Only an unambiguous result would justify asking separately to create a new
`.venv_py312` and download minimal clone assets.

**WAITING FOR USER APPROVAL OF PINNED V-TTS SOURCE CHECKOUT ONLY**
