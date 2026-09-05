# Phase 30Q Report

## Timestamp

2026-09-01 (Asia/Ho_Chi_Minh).

## Status

`PHASE30Q_PODCAST_BETA_READY_FOR_USER_VALIDATION`

## Goal

Expose the selected frozen M-A identity as a production-accessible **Beta**
Special Voice and prepare one real-web-path 10–15 minute long-form validation.

## Input State

Phase 30P.1 manual validation passed. The approved unchanged prosody system is
`podcast_prosody_v1` plus `vi_prosody_suggest_v1_1`. M-A remains the selected
primary experimental identity; this phase does not make it final.

## M-A Canonical Keeper

The unambiguous canonical source is
`experiments/special_voice_podcast/keepers/phase30m_04/`, identity `M-A`,
blind number `04`, status `PRIMARY_DISTINCTIVENESS_FINALIST`.

The production profile reuses exactly these protected native Phase 30M artifacts:

- `qwen_source.wav` (canonical reference source, untouched)
- `speaker_emb.npy` — SHA-256 `35fb11f3ecf65a27fa2a4f89b8a427016620b067cf8e33858cdbf017eff8f692`
- `reference_codes.npy` — SHA-256 `c9ce56716157e68c757ca2fb13d72bb07ee01e8cdf81e855e7dc30b014658d4b`

## Keeper Integrity

All 59 manifest-protected files passed size and SHA-256 verification: Phase30I,
G2 / Phase30J, Phase30K finalists including K-A, and Phase30M M-A/M-C.

## Review Film Architecture Reuse

Podcast Brand Beta is a second entry in the existing `SPECIAL_VOICES` registry,
persisted in the same local `data/voices/voices.json` store and surfaced through
the existing `/api/voices` `type: special` metadata flow. No second API or voice
loading architecture was introduced; Review Film remains unchanged.

## Production Integration

`scripts/install_podcast_brand_beta.py` validates canonical M-A hashes and
provisions the native profile once from its already encoded `speaker_emb` and
`reference_codes`. It completed successfully. It does not re-encode the WAV,
load VieNeu/Qwen, or alter keeper files. On backend restart, the normal local
voice-store restoration registers it as a standard selectable VieNeu voice.

## Podcast Brand Beta Profile

- Internal ID: `podcast_brand_beta`
- Display: `🎙️ Podcast Brand (Beta)`
- Category: `Special Voice`
- `is_special`: true
- `special_type`: `podcast`
- Recommended use: podcast, narration, long-form conversational content

The Beta label is retained deliberately pending human long-form listening.

## Runtime Reference Handling

The profile contains the exact existing M-A native speaker embedding (192
values) and reference code array (101 rows). Normal requests reuse that loaded
profile; no per-request M-A WAV encoding is added.

## Qwen Runtime Dependency

Qwen is not required by the production web app or this profile. It was only the
historical one-time experimental source creator.

## Offline / Network Safety

No network or model download occurred during Phase 30Q: provisioning, keeper
verification, long-form suggestion, and tests were text/local-data operations.
The integration did not change existing production model resolution or add cloud
dependencies; normal generation continues to require the existing local VieNeu
runtime/cache.

## Prosody Compatibility

Podcast Brand Beta uses the ordinary `POST /api/tts` path both with empty TTS
Script and with Phase30O markup. Its path remains Original Text → Phase30P.1
suggestion → editable TTS Script → parser → Smart Text Processing on clean
segments → VieNeu → loaded M-A profile. No candidate-specific prosody or sampling
tuning is introduced.

## Phase30P.1 Regression

Suggestion rules were not modified. Focused Phase30P.1 tests remain green.

## Long-Form Script

Prepared a neutral evergreen episode, *Những lựa chọn nhỏ và hướng đi dài hạn*,
with opening, explanation, reflection, information, examples, transitions, and
closing. It includes normal punctuation, lists, dates, time, money, percentages,
and short/long conversational phrasing.

- Original: `experiments/special_voice_podcast/phase30q/original_text.txt`
- Suggested editable script: `experiments/special_voice_podcast/phase30q/suggested_tts_script.txt`
- Analysis: `experiments/special_voice_podcast/phase30q/suggestion_analysis.json`
- 1,773 words; estimated 11.8–13.6 minutes at a conversational 130–150 words
  per minute, before model-specific pauses.

## Long-Form Prosody Analysis

The frozen V1.1 engine found 119 candidates, selected 13, and suppressed 106:
0.73 markers per 100 words. Selected reasons: 12 predictable paragraph controls
and 1 substantial contextual contrast. The proposed script is visible and
editable; no hidden instruction or post-suggestion rewriting occurs.

## Tests

Focused result: 27 passed, 0 failed.

- Phase30Q beta registry/API/prosody tests: 2
- Phase30P.1: 8
- Phase30P: 8
- Phase30O: 7
- Existing Special Voice: 2

## Regression Results

Frontend JavaScript syntax, Python compilation, and `git diff --check` passed.
The known pre-existing TestClient health-request hang was not repeatedly run and
is not reported as passing. No synthesis or model inference was run.

## Manual Web Smoke Test

1. Restart the backend:
   `cd "/home/tung/ai voice" && .venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8000`
2. Hard-refresh the frontend.
3. Confirm **SPECIAL VOICES** contains `🎬 Review Film` and
   `🎙️ Podcast Brand (Beta)`.
4. Select Podcast Brand Beta and generate:
   `Đây là một đoạn thử ngắn cho giọng podcast mới. Mục tiêu là kiểm tra xem giọng đã được tích hợp đúng vào hệ thống hay chưa.`
5. Confirm it is the selected M-A identity before proceeding.

## Long-Form Listening Criteria

Use Voice `🎙️ Podcast Brand (Beta)` at speed `1.0`. Review identity stability,
naturalness, Vietnamese pronunciation and number/date/money normalization,
prosody (especially list and paragraph rhythm), long-term listening comfort, and
distinctiveness. Human listening is authoritative.

## Production Changes

- `backend/app/tts/special_voices.py`
- `scripts/install_podcast_brand_beta.py`
- local ignored `data/voices/voices.json` provisioned with exact M-A profile
- generic history suggestion-version persistence from Phase30P.1

No M-A/M-C keeper, embedding, code, Qwen factory, sampling default, or Voice Lab
behavior was modified.

## Limitations

No long WAV has been generated by the coding agent. This is intentional to avoid
orphaned heavy synthesis. The production-accessible voice remains Beta until the
user completes the realistic web-path listening test.

## Decision

`WAITING_FOR_USER_LONG_FORM_LISTENING_VERDICT`

## User Validation Required

After the short smoke succeeds, paste the prepared Original Text into the real
web UI, click `✨ Đề xuất nhịp đọc`, inspect or correct markers, generate once,
and listen through the complete result at speed 1.0.

## Next Step

Wait for the user’s long-form verdict. Phase 30R is not implemented.
