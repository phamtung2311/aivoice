# Phase 38C — OpenVoice V2 CPU separation probe

## Execution status

`PASS` — the single pinned CPU conversion completed and passed container/sample
validation. This is technical execution status, not human identity acceptance.

## Source gate

`SOURCE QUALITY = PASS (QUALIFIED)`

Human feedback: no abnormal long pause; pronunciation correct; strength/focus
ordinary but improved over the prior failed Candidate 03 clone path; still
generic/industrial; Vietnamese reading quality acceptable.

## Exact environment

- OpenVoice isolated environment: `.venv/`, Python 3.12.14.
- OpenVoice commit: `74a1d147b17a8c3092dd5430504bd83ef6c7eb23`.
- OpenVoice V2 snapshot: `f36e7edfe1684461a8343844af60babc2efbb727`.
- Converter checkpoint SHA-256:
  `9652c27e92b6b2a91632590ac9962ef7ae2b712e5c5b7f4c34ec55ee2b37ab9e`.
- PyTorch 2.11.0+cpu; CUDA unavailable; device `cpu`.
- OpenVoice defaults used: `tau=0.3`, message `default`, watermark enabled.
- No VAD, denoiser, ASR, EQ, compression, or post-processing.

## Source

- preset: `Minh Đức` (`Nam · Bắc · Phong cách tin tức`), VieNeu 3.3.0;
- exact text: `Khi mọi thứ trở nên ồn ào, điều quan trọng nhất là giữ một nhịp suy nghĩ thật rõ ràng.`;
- file: `audio/source_vietnamese.wav`;
- 5.600 s, PCM16, 48 kHz, mono;
- peak 0.563660; RMS 0.104178; clipped samples 0;
- SHA-256: `65d122d285e4841bc687485efefb7d10fb13848d0e3d0f7d1ce2841aca309786`.

## Target identity

- canonical Candidate 03:
  `../brand_speaker_phase33c/baseline_anchor/BRAND_CANDIDATE_03_BASELINE/qwen_source.wav`;
- verified SHA-256:
  `3f3f5c6771ed437297ffdd89c5ea2aebd2d34dd531235ad5dd12e93bf18b5f06`.

## Conversion result

- model load: 3.463 s;
- source embedding: 8.998 s;
- Candidate 03 embedding: 0.048 s;
- tone-colour conversion: 2.288 s (RTF 0.409);
- measured pipeline stages total: 14.797 s;
- observed command wall time: 17.375 s;
- peak RSS: 1102.254 MiB;
- output: `audio/candidate03_openvoice.wav`;
- 5.596 s, PCM16, 22.05 kHz, mono;
- peak 0.709625; RMS 0.098107; clipped samples 0;
- SHA-256: `e4ff787c8b2e04dfbc6f57d496c219abeae6bb7b619c6df335b8bb8024a40a81`.

The output is non-empty, finite, frame-complete, and readable. The approved
source hash remained unchanged. Exactly the two intended primary WAV files
exist. The output was produced by the pinned OpenVoice tone-colour converter.

## Current gates

`OPENVOICE IDENTITY TRANSFER: PENDING HUMAN QA`

Downstream synthetic corpus rights remain `UNRESOLVED`. Production and the
canonical Candidate 03 asset remain untouched.
