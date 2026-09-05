# Phase 37A — OmniVoice provenance / API / Vietnamese audit

Audit date: 2026-09-02.  This is a metadata-and-source audit only.  No OmniVoice
repository was checked out, no dependency was installed, no model asset was
downloaded, and no audio was generated.

## Decision first

**Classification: RESEARCH-ONLY — rejected as a production candidate for the
potentially monetized channel.**

The official source code is Apache-2.0, but the official `k2-fsa/OmniVoice`
pretrained checkpoint is explicitly **CC-BY-NC** because of training-data
constraints.  CC-BY-NC does not authorize the stated commercial destination.
The model card gives no separate commercial output grant that cures that
restriction.  Therefore Phase 37A stops before installation or download.

This is a legal/provenance decision, not a judgment that Vietnamese quality is
bad.  Technically, OmniVoice is a credible *research* clone renderer, but it
cannot enter the production architecture under the project requirements.

## 1. Official project and unambiguous provenance

There are unrelated projects named OmniVoice/OmniVoice Studio and several
community C++/GGML/Rust ports.  They are not the subject of this audit.  The
only audited upstream is:

| Item | Verified value |
| --- | --- |
| Official code | [`k2-fsa/OmniVoice`](https://github.com/k2-fsa/OmniVoice) |
| Maintainer / author stated by package | k2-fsa; package author Han Zhu |
| Latest stable release | `0.2.1`, non-prerelease, published 2026-07-16 04:47:24 UTC |
| Release tag commit | `5ba967c4d5b0f08244ae856b033eea583d1e4517` |
| Package version at that tag | `0.2.1` |
| Code licence | Apache-2.0 (`LICENSE` and `pyproject.toml`) |
| Official model card / checkpoint | [`k2-fsa/OmniVoice`](https://huggingface.co/k2-fsa/OmniVoice) |
| Model revision inspected | `c5fdb5ccb189668d56333f77ba2629f4cd7535f4` (Hub `main` metadata at audit time) |

The release is independently visible on the official
[GitHub releases page](https://github.com/k2-fsa/OmniVoice/releases), including
the signed tag, and the package metadata declares Python `>=3.10` and version
`0.2.1` in [pyproject.toml](https://github.com/k2-fsa/OmniVoice/blob/master/pyproject.toml).

## 2. Licence and output-rights gate

| Surface | Evidence / result |
| --- | --- |
| Code | Apache-2.0. |
| Official pretrained weights | **CC-BY-NC**, explicitly stated by the official [model card](https://huggingface.co/k2-fsa/OmniVoice) due to training data including Emilia. |
| Commercial use | Not permitted by the checkpoint licence without separate permission from the rightsholder. |
| Generated outputs | The model card provides safety restrictions against unauthorized cloning, impersonation, fraud and illegal/unethical use, but does **not** publish a separate commercial-output licence that overrides CC-BY-NC.  Output rights are therefore **unresolved for commercial production**. |

Result: **RESEARCH-ONLY**.  Apache source does not make non-commercial weights
commercially usable.  No install/download is authorized after this gate.

## 3. Vietnamese evidence — explicit, but not a quality guarantee

Vietnamese is not inferred merely from the “646 languages” claim.  The official
[supported-languages table](https://github.com/k2-fsa/OmniVoice/blob/master/docs/languages.md)
lists:

| Language | OmniVoice language ID | ISO 639-3 | Listed training duration |
| --- | --- | --- | ---: |
| Vietnamese | `vi` | `vie` | 8,481.98 h |

The clone API accepts a language name or code.  A future technical call would
therefore explicitly set `language="vi"`, rather than relying on
language-agnostic inference.  The source uses the model's general text
tokenizer plus language ID; it does **not** document a dedicated Vietnamese G2P
or tone frontend.  `normalize_text=True` is opt-in: Chinese/English use
WeTextProcessing; other languages only have a `num2words` integer fallback.

No official Vietnamese audio example, Vietnamese regression test, or claim of
tone/diacritic validation was found in the upstream docs/model card.  Thus
Vietnamese is explicitly present in the training/language map, but natural
Vietnamese tone, diacritic handling and narration quality remain listening-test
questions—not facts established by this audit.

## 4. Exact clone path and Candidate 03 compatibility

The public API is `OmniVoice.from_pretrained(...)`, then:

```python
audio = model.generate(
    text=target_text,
    language="vi",
    ref_audio=reference_wav,
    ref_text=reference_transcript,
    # or: voice_clone_prompt=prompt
)
```

The official implementation is in
[`omnivoice/models/omnivoice.py`](https://github.com/k2-fsa/OmniVoice/blob/master/omnivoice/models/omnivoice.py)
and the supported single-item CLI is
[`omnivoice/cli/infer.py`](https://github.com/k2-fsa/OmniVoice/blob/master/omnivoice/cli/infer.py).

Facts from the API/source:

- `ref_audio` and `ref_text` select voice-clone mode.  The transcript can be
  omitted only by loading the optional Whisper ASR path; it is not needed here
  because the canonical transcript exists.
- `create_voice_clone_prompt(ref_audio, ref_text, preprocess_prompt=True)`
  encodes a reusable `VoiceClonePrompt`; version 0.2.1 adds `save()`/`load()`
  for reuse across sessions.  Its persisted contents are reference audio
  tokens, reference text and reference RMS—not an independent learned speaker
  account/token.
- A path or `(waveform, sample_rate)` tuple is accepted.  1-D input becomes
  mono; multi-channel input is averaged to mono; a nonmatching sample rate is
  resampled to the tokenizer rate.  Output is normally 24 kHz mono.
- The source recommends a 3–10 s clean reference.  It warns above 20 s;
  preprocessing removes reference silence and adds terminal punctuation.  The
  API supports one reference prompt per generated item; no documented
  multi-reference fusion interface was found.
- `duration` has precedence over `speed`.  `speed > 1` is faster, `< 1` is
  slower.

Candidate 03 is mechanically compatible without changes:

| Candidate 03 item | Status |
| --- | --- |
| `experiments/brand_speaker_phase33c/baseline_anchor/BRAND_CANDIDATE_03_BASELINE/qwen_source.wav` | 6.960 s, 24 kHz, mono; inside official 3–10 s recommendation. |
| Canonical transcript | Exact supplied English transcript can be passed as `ref_text`; no ASR needed. |
| Conversion / edit | Not required.  It must remain untouched. |

However, the official usage notes recommend matching reference and target
languages for standard pronunciation and warn that cross-lingual cloning carries
the reference language accent.  Candidate 03 is English while the target is
Vietnamese.  So it is **mechanically compatible but a high-risk identity and
Vietnamese-pronunciation test asset**, not proof that it is a good Vietnamese
reference for a future production system.

## 5. Synthetic identity mechanisms

| Mechanism | What upstream actually exposes | Brand-voice assessment |
| --- | --- | --- |
| Voice clone | Reference audio + exact transcript, or cached clone prompt | Best available means to preserve Candidate 03 across calls.  Identity is conditioned by the reference tokens, not a separately trained speaker embedding. |
| Cached clone prompt | `create_voice_clone_prompt`, `VoiceClonePrompt.save/load` | Reusable and persistent across sessions, but still inseparable from the original reference audio/text conditioning. |
| Voice design | `instruct="..."`, no reference required | Useful for exploratory synthetic design, but no documented persistent design seed/ID or guarantee two calls create the same person. |
| Auto voice | Neither reference nor instruction | Random voice; unsuitable for a fixed channel identity. |
| Speaker/style separation | An instruction may be combined with clone; source maintainers note conflicting instruction tends to lose to reference | No independently controlled speaker embedding + style embedding interface is documented. |
| Multi-reference corpus | No documented multi-reference aggregate API | Cannot yet use a corpus as one fused identity prompt without adapting/training a separate system. |

The model therefore has a genuine reusable clone-prompt mechanism, but not a
documented durable synthetic-person ID independent of a reference.  Candidate
03 could be tested, but a resilient future Brand Voice still needs a
legally-usable identity creation/corpus route.

## 6. Continuity and prosody architecture

`generate()` handles short text as one inference task.  Automatic chunking is
only activated when estimated duration exceeds the default
`audio_chunk_threshold=30.0` s; the default chunk target is 15 s.  For chunked
long text it splits at punctuation and processes chunks sequentially, then
decodes and crossfades them.  The official
[generation-parameters documentation](https://github.com/k2-fsa/OmniVoice/blob/master/docs/generation-parameters.md)
also confirms `duration > speed` priority and documents silence removal.

The planned 10–18-word diagnostic is safely below that threshold, therefore it
would be one coherent model generation—no caller-added split, join or crossfade.
This avoids directly repeating the VieNeu/VietVoice forced-segmentation
experiment.

Important limits / risks to preserve for a future legal renderer audit:

- Default `postprocess_output=True` removes long silences, applies reference
  RMS scaling, then adds 100 ms fade/padding.  That may alter intentional long
  pauses; it is not a general prosody-control system.
- Controls documented: `duration`, `speed`, iterative `num_step`, guidance,
  sampling temperatures and the long-form chunk thresholds.  No documented
  Vietnamese-specific emphasis or linguistic prosody control exists.
- There is an official issue report of clone-mode output sometimes reading
  reference text instead of target text.  It is a regression risk to test in a
  future isolated PoC, not a finding about Candidate 03 here.

## 7. Local CPU feasibility on this machine

| Requirement | Verified state / consequence |
| --- | --- |
| Main model | 0.6B parameters; official weights are 2.450 GB `safetensors`. |
| Audio tokenizer | 805.7 MB F32 `safetensors`; required for encode/decode. |
| Runtime | Official Python/PyTorch + Transformers implementation.  The standard examples target CUDA fp16; source accepts a device map and supports CPU execution paths, but upstream publishes no CPU benchmark or peak-RAM guarantee. |
| Accelerators | Official examples mention CUDA, MPS and Intel XPU.  Iris Xe is not Intel Arc XPU; no supported Iris Xe route is documented. |
| Quantization / C++ | No official GGUF, OpenVINO, Vulkan, OpenVINO or CPU-quantized runtime was released by k2-fsa.  Community ports exist but are separate, unproven for parity and cannot repair the non-commercial upstream-weight licence. |
| Output format | Model card/API: 24 kHz output. |

Classification on i9-13900H / 16 GB RAM / no CUDA: **SLOW BUT TESTABLE for a
research-only short clip**, not “practical CPU production” until a measured
isolated benchmark says otherwise.  The raw checkpoint is already 3.27 GB
decimal; loading the generator, tokenizer, framework and activations together
has no official peak-RAM number.  A conservative planning allowance would be
at least 8–10 GB free disk for model snapshot, a separate CPU runtime and cache;
there is not enough official evidence to promise a safe 16-GB peak-RAM figure.

## 8. Minimum clone-PoC assets — metadata only

Official Hub revision: `c5fdb5ccb189668d56333f77ba2629f4cd7535f4`.
No automatic Whisper download is needed when the canonical transcript is
provided.

| Remote path | Bytes | Published content SHA-256 | Purpose |
| --- | ---: | --- | --- |
| `model.safetensors` | 2,450,344,112 | `730839316de585f4c8298ec0e1712efc10fb19c6fa4e36eb741cb8d51ebcf6aa` | OmniVoice generator weights |
| `audio_tokenizer/model.safetensors` | 805,665,628 | `fe7c5e8785e0a05833e1bfc3e002ec7f55af21e306b2e7154a448c1f54ccfb0d` | Higgs Audio v2 encode/decode tokenizer |
| `tokenizer.json` | 11,423,986 | `408f669b7e2b045fdf54201d815bd364e6667dbd845115da81239c40bc6dcfd1` | text tokenizer |
| `config.json`, `tokenizer_config.json`, `chat_template.jinja` | 6,939 combined | Git blobs only; no published SHA-256 in metadata | generator config/template |
| `audio_tokenizer/config.json`, `preprocessor_config.json` | 2,737 combined | Git blobs only; no published SHA-256 in metadata | tokenizer/configuration |

Raw required snapshot total: **3,267,443,402 bytes** (about 3.27 GB decimal /
3.04 GiB), plus small text/config files.  This exact listing came from public
Hub file metadata; no binary was fetched.

## 9. Python and dependency compatibility

The official `pyproject.toml` requires Python `>=3.10`, `torch>=2.4`,
`torchaudio>=2.4`, `transformers>=5.3.0`, `accelerate`, `pydub`, `gradio`,
`numpy`, `soundfile`, `librosa`, TensorBoardX and WebDataset.  The optional
`tn` extra adds `num2words` for non-Chinese/non-English basic number
normalization.  Linux/Fedora has no source-level blocker established in this
audit, but the upstream `uv` source configuration selects CUDA PyTorch wheels on
Linux/Windows, so a future research environment would need an **explicit CPU
wheel plan** rather than the default accelerator-oriented resolution.

`experiments/brand_voice_phase36d/python312/bin/python3.12` exists and reports
Python 3.12.14, satisfying `>=3.10`.  It must not be reused as-is: a future
research-only test would create a new, dedicated OmniVoice environment, leaving
the VietVoice and production environments untouched.

## 10. Future single diagnostic (not synthesized)

If a separately licensed renderer is selected, use exactly one short sentence:

> **Giọng nói vững vàng dẫn câu chuyện đi xa, rõ ràng và đầy sức thuyết phục.**

It has 16 Vietnamese words, no name/number/English, minimal punctuation and
tests tones, continuous narration and authority.  The gate is listening only:

1. correct Vietnamese pronunciation;
2. acceptable continuity;
3. one coherent synthetic person;
4. recognizable authority/character;
5. no stop-start robotic phrasing; and
6. enough distinctiveness to plausibly become the Brand Voice.

## 11. Architecture relevance and exact stop point

Technically, the architecture “heavy multilingual synthetic identity renderer
→ clean Vietnamese synthetic corpus → smaller local production adaptation” is
plausible: cached clone prompts can preserve a reference through a renderer
session, and OmniVoice has public fine-tuning/data tooling.  But this does **not**
make an OmniVoice-generated corpus commercially clean: its checkpoint remains
CC-BY-NC, so using it as the creator stage would contaminate the proposed real
channel workflow absent a separate commercial licence.

**Exact next step:** do not install or download OmniVoice.  Return to the
architecture search and require the next candidate to clear, before any PoC,
all three gates: explicit Vietnamese evidence, reference/identity interface,
and commercially usable model/output terms.  Preserve Candidate 03 and all
production code unchanged.

**STOP: Phase 37A ends before installation/download.**
