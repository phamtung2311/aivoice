# Phase 38A — Candidate 03 short-source corpus viability pilot

## Status

**PARTIAL — experiment execution successful; corpus-quality gate is pending
human QA.**  This status does not judge naturalness, pronunciation, speaker
identity, or suitability for training.

Production, saved voices, frontend, default TTS settings and the frozen
Candidate 03 canonical package were not modified. No model was downloaded: an
offline (`HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`) dry model load succeeded
before generation.

## Repository audit

- Candidate 03 anchor:
  `experiments/brand_speaker_phase33c/baseline_anchor/BRAND_CANDIDATE_03_BASELINE/`
- Canonical source: `qwen_source.wav`, SHA-256
  `3f3f5c6771ed437297ffdd89c5ea2aebd2d34dd531235ad5dd12e93bf18b5f06`.
- Reused entrypoint: `backend.app.tts.engine.TTSEngine(backend="onnx")`.
- Frozen conditioning: `speaker_emb.npy` shape `[192]` and
  `reference_codes.npy` shape `[87,16]`; directly passed as the voice profile.
- VieNeu package: 3.3.0; observed runtime is local CPU ONNX and reports 48 kHz.
- Fixed parameters for every clip: temperature 0.82, top-k 25, top-p 0.97,
  repetition penalty 1.15, speed 1.0, max outer chunk 240, denoise false,
  reference codes true, NumPy seed 34001.

The backend wrapper retains the historical identifier `pnnbao-ump/VieNeu-TTS-v2`
while the installed 3.3.0 package selected its local v3 ONNX runtime. This is
recorded in each manifest entry; it is not a new model installation or a
parameter substitution.

## Exact utterance set and outputs

| ID | Category | Original / normalized text | WAV | Duration | Generation | RTF |
| --- | --- | --- | --- | ---: | ---: | ---: |
| 01 | Calm introduction | Chào bạn, hôm nay chúng ta cùng bắt đầu bằng một câu chuyện nhỏ. | `audio/01_calm_introduction.wav` | 4.080 s | 5.437 s | 1.333 |
| 02 | Calm introduction | Cảm ơn bạn đã dành ít phút để lắng nghe chương trình. | `audio/02_calm_introduction.wav` | 3.200 s | 2.358 s | 0.737 |
| 03 | Neutral explanation | Một ý tưởng rõ ràng thường bắt đầu từ những điều rất đơn giản. | `audio/03_neutral_explanation.wav` | 3.440 s | 1.876 s | 0.545 |
| 04 | Neutral explanation | Khi hiểu đúng vấn đề, chúng ta sẽ chọn được bước đi phù hợp. | `audio/04_neutral_explanation.wav` | 4.560 s | 1.737 s | 0.381 |
| 05 | Reflective narration | Có những lúc chậm lại một chút lại giúp ta nhìn thấy điều quan trọng. | `audio/05_reflective_narration.wav` | 3.680 s | 2.471 s | 0.671 |
| 06 | Reflective narration | Sau một ngày bận rộn, ai cũng cần một khoảng yên để suy nghĩ. | `audio/06_reflective_narration.wav` | 3.680 s | 1.856 s | 0.504 |
| 07 | Storytelling / conversation | Anh ấy đặt cuốn sách xuống rồi kể về cuộc gặp gỡ buổi sáng. | `audio/07_storytelling_conversation.wav` | 4.320 s | 2.916 s | 0.675 |
| 08 | Storytelling / conversation | Trong căn phòng nhỏ, mọi người lặng im nghe câu chuyện tiếp tục. | `audio/08_storytelling_conversation.wav` | 3.840 s | 2.591 s | 0.675 |
| 09 | Firm / authoritative | Điều cần làm trước tiên là giữ lời hứa với chính mình. | `audio/09_firm_authoritative.wav` | 2.960 s | 1.319 s | 0.446 |
| 10 | Firm / authoritative | Một quyết định tốt cần được đưa ra bằng sự bình tĩnh. | `audio/10_firm_authoritative.wav` | 3.200 s | 1.411 s | 0.441 |
| 11 | Mixed podcast speech | Mỗi tuần, chúng ta chọn một chủ đề gần gũi để cùng trò chuyện. | `audio/11_mixed_podcast_speech.wav` | 3.920 s | 1.977 s | 0.504 |
| 12 | Mixed podcast speech | Dù cuộc sống thay đổi, những điều tử tế vẫn luôn có giá trị. | `audio/12_mixed_podcast_speech.wav` | 4.000 s | 1.727 s | 0.432 |

Original text equals normalized text in every row. The pilot intentionally
contains no numbers, dates, units, abbreviations, symbols, URLs or English
expressions.

## Technical and resource results

**FACT**

- 12/12 intended WAVs generated successfully in sequence.
- 0 technical retries; `technical_attempts/` is empty.
- Every output opens as 48 kHz mono, is longer than zero, and has zero samples
  at or above absolute amplitude 0.999.
- Total audio duration: 44.880 s; summed generation time: 27.677 s; total run
  wall time: 29.389 s; audio disk use: 4,309,008 bytes.
- Peak process RSS: 852.457 MiB. CPU utilisation was not separately sampled;
  the process used the engine's normal local CPU ONNX execution and ran
  sequentially.
- No swap/thermal intervention or concurrent generation was requested.

**INFERENCE**

The observed resource use is well below the prior 3–5 GB conservative estimate
and does not create a RAM-risk concern for this twelve-clip pilot. It does not
predict resource use for a future trainer.

## Provenance and review package

- Machine-readable clip evidence: `manifest.json` and `manifest.csv`.
- Canonical identity, engine, fixed configuration, offline guard, Python/OS,
  repository commit and working-tree snapshot: `provenance.json`.
- Human review order and template: `HUMAN_REVIEW.md`.
- The outputs are **research corpus candidates only**. They are not commercial
  corpus assets and no legal conclusion is made here.

## Listening decision

Listen in the numbered order 01 through 12. For each clip decide PASS only when
pronunciation/tones, Candidate 03 identity, timing/prosody and audio integrity
are clean enough that you would teach the permanent Brand Voice from it.

Do not ask for variants or regeneration during this gate. The architecture gate
is PASS only if at least 10 of 12 pass and there is no systematic speaker drift.
Otherwise it stops before Piper/VITS installation or training.

## Current gate

STAGE 0 CORPUS QUALITY:
PENDING HUMAN QA
