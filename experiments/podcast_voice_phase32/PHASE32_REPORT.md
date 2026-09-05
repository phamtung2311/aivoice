# PHASE 32 — DISTINCTIVE BRAND VOICE R&D REPORT

## 1. Why current Podcast voice feels generic

The current Podcast voice is technically stable and pleasant, but its identity is
anchored by one short, broadly natural M-A reference. Phase 31/31B changed
segmentation and pauses; these control phrasing but do not create a new timbre,
resonance, vocal weight, or persistent speaker character. Small sampling changes
also operate after identity conditioning is fixed. A recognizable brand voice
therefore needs a deliberately distinctive source identity, a model with stronger
identity control, or both.

## 2. Where identity comes from in VieNeu

Installed package: VieNeu 3.3.0, V3 Turbo, CPU ONNX production path.

The source encodes an enrolled reference through two paths:

```
reference waveform
  ├─ frozen ONNX speaker encoder → 192-d global speaker_emb
  └─ MOSS Audio Tokenizer → time-varying ref_codes [T, 16]
```

`speaker_emb` is projected by learned `xvec_proj` and added to every prompt and
generation row. It is the persistent global speaker anchor. `ref_codes` are
inserted as in-context audio-code rows when `use_ref_codes=True`; they carry
acoustic context, but the source does not disentangle their timbre, prosody,
linguistic content or transient delivery. The `style` argument is explicitly
deprecated and ignored: V3 Turbo fixes the natural-style token and expects style
to be implied by the reference.

Built-in preset records are a registry of pre-encoded `speaker_emb` + `codes`,
not runtime speaker-token training.

## 3. Reference-conditioning limits

The installed public API has no supported speaker interpolation, latent editing,
embedding averaging, reference-code mixing, reference ensemble, custom
speaker-token creation, LoRA/adapter loading, or fine-tuning API. Combining
vectors/codes manually would be an unvalidated architecture change and can mix
identity, content and prosody unpredictably.

Reference transcript is not passed into the V3 prompt builder for cloning. The
prompt consists of new-text phonemes followed by optional acoustic-code rows; the
`ref_phonemes` argument is unused. Thus reference waveform content can influence
through audio codes, but there is no transcript-aligned control of its content or
prosody.

## 4. Does longer reference actually help?

**Not with the installed enrollment path.** Both PyTorch and CPU ONNX engines set
`_MAX_REF_SECONDS = 8.0`; `prepare_reference()` takes only the first eight
seconds *before* speaker embedding extraction and MOSS-code encoding. The app also
introspects that default to limit reference upload. The speaker encoder could pool
up to 30 seconds, but never receives more than the 8-second truncated waveform.

Consequently a submitted 20–40 second V2 file currently adds neither identity
evidence nor prosody after second eight. An 8-second clip produces roughly 400
codec frames at the tokenizer's 50 Hz rate, each with 16 codebooks; all encoded
rows are used as prompt context. Longer code sequences would increase prompt
length and memory/runtime, but that path is not exposed or validated. Do not modify
the limit for this phase.

The serious V2 experiment is therefore re-scoped: a purpose-performed **clean,
complete 8-second** reference with the intended personality vs the current first
8 seconds. A 30–40 second script remains useful for casting/rehearsal and choosing
a take, not as a single enrollment upload.

## 5. Three proposed Brand Voice directions

| Direction | Designed character | Recognizable cue | Guardrail |
| --- | --- | --- | --- |
| Deep Intimate | Dark-warm, close mic, calm, medium-low energy, controlled falling endings | Quiet entry and gently resolved sentence ends create a close, reflective signature | No forced low pitch, whisper or breathy affectation |
| Warm Conversational | Warm mid-register, light vocal weight, fluid medium pace, friendly articulation | Slight lift on invitations/questions, then relaxed landing gives a repeatable “speaking with you” cadence | No presenter brightness or sales energy |
| Signature Storyteller | Warm-darker core, deliberate setup-to-conclusion contrast, restrained emphasis | Small pause before reveal and a firm but unprojected final word form a narrative pattern | No theatrical acting or exaggerated pauses |

All three are believable variants of the desired male Vietnamese storyteller. They
are design hypotheses only; no new audio was generated in Phase 32.

## 6. Brand Voice recording script

The complete 30–40 second rehearsal/casting script and delivery direction are in
`brand_voice_recording_script.md`. It contains short and long sentences, a low
reflective thought, conversational question, transition, varied Vietnamese sounds,
and several ending shapes. It also provides one self-contained 8-second enrollment
line. Record three takes of that line, then select one only after consent and
quality review.

## 7. Multiple-reference feasibility

Unsupported by the installed architecture. It accepts one `speaker_emb` and one
reference-code sequence per call. There is no select-per-content, reference list,
documented concatenation, or safe averaging operation. Multiple recordings may be
used **outside** the engine for human selection of the single best 8-second take;
they must not be combined as model conditioning.

## 8. Speaker-token/custom-speaker feasibility

Built-in voice names load records from `voices_v3_turbo.json`; each contains a
192-d embedding and reference codes. The `add_voice()` API merely encodes a
user-provided reference once and saves those values. There is no code path that
learns a persistent speaker token, optimizes an embedding, or trains a speaker-only
representation.

## 9. Fine-tuning / adaptation feasibility

VieNeu's installed distribution provides inference code and frozen ONNX graphs; it
exposes no training dataset pipeline, checkpoint training, LoRA/adapter hooks, or
speaker-only adaptation mechanism. Fine-tuning V3 Turbo is **not a supported path**
in this project. A research fork would require an upstream trainable checkpoint,
verified licence/data provenance, and substantial GPU work.

For a recognizable voice, the practical levels are:

1. **Reference engineering:** viable now, but limited to the first 8 seconds.
2. **Speaker adaptation/token learning:** not supported by installed VieNeu.
3. **Fine-tuning/custom speaker model:** potentially necessary for stronger durable identity, but needs another supported training stack and consented data.

## 10. Alternative models

Research is an architecture/availability screen only—no model was downloaded.

| Model | Vietnamese evidence | Identity / control | Fine-tune path | Local CPU / 16 GB | Licence / risk | Assessment |
| --- | --- | --- | --- | --- | --- | --- |
| VieNeu V3 Turbo | Native Vietnamese; current measured local quality | Reference embedding + codes only | No installed supported path | **Yes**, current ONNX | Apache-2.0 package; verify weights for release | Best current local production, weak design control |
| Gwen-TTS 0.6B | Vietnamese-primary community model, stated ~1,000 h Vietnamese fine-tune | Zero-shot clone; Qwen base surface | No reviewed speaker-adaptation documentation | **No validated CPU path**; documented CUDA ≥4 GB + FlashAttention | MIT code claim; training-data/provenance review required | Highest-value alternative *GPU PoC*, not production-ready |
| Qwen3-TTS | Officially lists 10 languages; **Vietnamese absent** | Clone, voice design, instruction control | Official Base supports fine-tuning | 0.6B/1.7B; CPU not validated for long form | Apache-2.0 | Strong design platform, Vietnamese blocker |
| IndexTTS2 / VN community adaptation | Community adaptation claims Vietnamese primary | Zero-shot clone + emotion/duration | Community GPT fine-tuning recipe, not official stable path | Heavy PyTorch; CPU practicality unproven | Bilibili model licence; commercial review | GPU PoC only |
| CosyVoice 3 | Official language list excludes Vietnamese | Zero-shot clone + instruct | Full-stack training | GPU-oriented; CPU/16GB unvalidated | Weight terms must be checked | Not Vietnamese-first |
| F5-TTS | Vietnamese only via community models | Reference clone; finetuning code | Yes technically | GPU-oriented | Official released base is CC-BY-NC | Reject for commercial route |

Sources: [Qwen3-TTS README](https://github.com/QwenLM/Qwen3-TTS/blob/main/README.md), [Gwen-TTS README](https://github.com/ggroup-ai-lab/gwen-tts), [IndexTTS2 upstream](https://github.com/index-tts/index-tts), [IndexTTS Vietnamese adaptation](https://github.com/iamdinhthuan/index-tts-finetune-vietnamese), [CosyVoice upstream](https://github.com/FunAudioLLM/CosyVoice), and [F5-TTS licensing clarification](https://github.com/SWivid/F5-TTS/discussions/997).

## 11. Hardware feasibility

This host is an i9-13900H with 16 GB RAM and no dedicated GPU indicated. Current
VieNeu ONNX CPU inference is feasible. The viable alternatives document CUDA,
FlashAttention or heavy PyTorch usage; they are not safe local production
candidates without a dedicated benchmark. A temporary cloud GPU is reasonable for
a tightly scoped alternative-model or fine-tuning evaluation only if final local
inference and licence are independently validated.

## 12. Recommended path

**Choose one next experiment: Intentional 8-second Reference A/B for Deep
Intimate.** Obtain explicit consent, record three clean takes of the provided
enrollment line, select the best take, and render the same 30–45 second podcast
text against the current reference under unchanged sampling. Blind-listen for
identity recall after 5–15 seconds, Vietnamese quality, fatigue and robotic
artifacts.

```
intentional 8-second A/B clearly strengthens identity?
├─ yes → polish prosody around that approved reference; production only after approval
└─ no → GPU PoC of Gwen-TTS (consent/licence/provenance review first)
         ├─ materially stronger Vietnamese identity → assess local-inference feasibility
         └─ not stronger / not locally feasible → accept VieNeu zero-shot ceiling;
                                               stop micro-parameter search
```

## 13. Risks / model ceiling

The 8-second cap may not provide enough evidence to carry a subtle long-form
personality across arbitrary content. Reference codes blend acoustic factors rather
than exposing a safe identity dial. Even a well-recorded reference cannot guarantee
recognizability; if A/B fails, that is positive evidence of the model ceiling.
Never use recordings without explicit speaker consent, and review model/data
licences before public or commercial deployment.

## 14. Files changed

- `experiments/podcast_voice_phase32/README.md`
- `experiments/podcast_voice_phase32/brand_voice_recording_script.md`
- `experiments/podcast_voice_phase32/PHASE32_REPORT.md`

## 15. Production status

**No production voice was changed.** No audio was generated, no model was
downloaded, no training ran, and no API/UI/Review Film configuration was altered.

`WAITING FOR USER APPROVAL OF NEXT BRAND-VOICE EXPERIMENT`

