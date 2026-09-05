# Phase 30E Report

## Timestamp

2026-08-31 (Asia/Ho_Chi_Minh)

## Status

HUMAN_REFERENCE_REQUIRED

## Objective

Determine whether the installed local VieNeu ecosystem can create genuinely new
Podcast Brand Voice identities without human reference audio.

## Runtime Environment

`/home/tung/ai voice/.venv/bin/python`; Python 3.14.7; VieNeu 3.3.0; NumPy;
pytest; V3Turbo ONNX CPU.

## Production Safety

Git state was inspected first. Only isolated research files were added. No
production endpoint, frontend, profile, sampling default, or model-loader changed.

## VieNeu Speaker Representation

The 20 live presets use float32 `speaker_emb` `[192]` and int64 `codes` `[T,16]`.
A frozen ONNX speaker encoder produces the x-vector; a learned projection adds
it to every model-input row. Presets are pre-enrolled conditioning pairs.

## encode_reference Trace

WAV → mono / trim to eight seconds / optional denoise → ONNX speaker encoder →
`speaker_emb`; the same audio → 48-kHz MOSS codec encoder → `ref_codes`.

## Speaker Embedding Analysis

The read-only analysis covers all 20 live preset anchors. Norms range 10.814 to
18.823; off-diagonal cosine similarity ranges 0.037 to 0.657; Euclidean distance
ranges 11.163 to 20.985. Results are stored in
`custom_voice_research/speaker_embedding_analysis.json`; geometry measures
numeric separation only and does not validate a synthetic speaker.

## Reference Codes Analysis

Codes are variable-length, 16-codebook MOSS acoustic tokens from the reference.
Source does not prove an independent identity/prosody/style separation, so they
must not be mixed between speakers.

## Native Speaker Generation Audit

No speaker prior, latent sampler, random/new-speaker API, voice seed, or native
generation mechanism was found in the installed VieNeu package/assets. Random
operations in source sample output audio codes during normal inference only.

## Interpolation / Latent Feasibility

UNSAFE/MEANINGLESS. A nonzero input passes minimal anchor sanitation, but that
is not support for a valid identity. Normal fidelity also needs companion codes
from the same reference. No custom latent PoC was performed.

## VieNeu Capability Classification

`C. NEW_IDENTITY_REQUIRES_REFERENCE_AUDIO`.

## Custom Candidate PoC

Not performed: random/interpolated anchors or mismatched codes would be
unsupported and would not demonstrate a usable brand identity.

## Local Free Alternative Research

Qwen3-TTS VoiceDesign is the strongest conceptual factory because it supports
text-described voice design, but its official release excludes Vietnamese.
Spark-TTS offers virtual-speaker controls but officially supports Chinese/English.
Fish Speech and Chatterbox do not meet the reviewed licensing or
Vietnamese/identity-control requirements.

## Technology Comparison

See `custom_voice_research/technology_comparison.md`.

## CPU Feasibility

VieNeu cloning is GOOD on the current CPU-only system. The reviewed factory
alternatives are UNKNOWN or likely slow/heavy on 16 GB; none was downloaded,
installed, or benchmarked.

## Vietnamese Support

VieNeu remains the project’s verified Vietnamese engine. No reviewed
reference-free factory offered official Vietnamese support sufficient to recommend.

## Licensing

Weight terms must be checked independently from source-code licenses. Fish Speech
requires a commercial agreement; F5-TTS pretrained weights are non-commercial.
Qwen/Spark repository licenses do not overcome their language/hardware gap.

## Voice Factory Architecture

Concept only, not currently recommended:

```text
Synthetic Voice Factory → candidate references → user audition
  → VieNeu encode_reference → Podcast Brand Voice → local AIVoice
```

## Findings

VieNeu is reference-conditioned for new identities. Existing presets were too
generic, while sampling changes do not create a new speaker identity.

## Limitations

No alternative model was installed or downloaded. No claim of legal/perceptual
uniqueness is made from embedding geometry or synthetic-generation research.

## Decision

Use a permissioned, purpose-recorded custom Vietnamese reference as the sole
currently viable local path.

## Recommended Phase 30F

Acquire and validate one purpose-recorded, permissioned 6–8 second custom
Vietnamese Podcast reference through the Phase 30B contract.

## Production Changes

None.

## Regression Tests

Using `/home/tung/ai voice/.venv/bin/python`:

- `python experiments/special_voice_podcast/custom_voice_research/speaker_embedding_analysis.py` — passed; read-only, no inference
- `python -m py_compile experiments/special_voice_podcast/custom_voice_research/speaker_embedding_analysis.py` — passed
- `python -m pytest tests/test_phase30b_podcast_voice.py tests/test_phase30c_podcast_candidates.py tests/test_phase30d_podcast_recast.py tests/test_phase30e_custom_voice_research.py -q` — 13 passed
- `git diff --check` — passed
