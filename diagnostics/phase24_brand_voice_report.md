# Phase 24 — Brand Voice Studio (NLP Foundation)

## Status

Complete. This phase adds an optional deterministic local text-normalization layer before ordinary `/api/tts` generation. It does not change VieNeu, training, cloning, Voice Lab, embeddings, speaker codes, chunking, or sampling.

## Architecture

`backend/app/tts/nlp.py` provides `normalize_text()`: ordered regex transforms for recognized speech patterns plus a local pronunciation dictionary. `TTSRequest.smart_text_processing` defaults to `true`; when false, the submitted text reaches the existing engine unchanged by this new layer.

`POST /api/nlp/preview` calls the same function and powers the expandable Advanced-panel preview. The browser sends the explicit flag only on the main TTS request. No network or AI service is involved.

## Files modified

- `backend/main.py`
- `frontend/app.js`
- `frontend/index.html`
- `frontend/styles.css`

## Files created

- `backend/app/tts/nlp.py`
- `data/nlp/custom_dictionary.json`
- `tests/test_phase24_nlp.py`
- `diagnostics/phase24_brand_voice_report.md`
- `diagnostics/phase24_work_report.md`

## Examples

| Input | Processed |
| --- | --- |
| `10/05/2026` | `ngày mười tháng năm năm hai nghìn không trăm hai mươi sáu` |
| `1.250.000đ` | `một triệu hai trăm năm mươi nghìn đồng` |
| `15%` | `mười lăm phần trăm` |
| `20:45` | `hai mươi giờ bốn mươi lăm phút` |
| `3/5` | `ba phần năm` |
| `72,5` | `bảy mươi hai phẩy năm` |
| `OpenAI API` | `Ô-pần AI ây pi ai` |

## Performance

The processor uses only compiled regular expressions, integer-to-word helpers, and a small cached local JSON dictionary. It has no model load, network request, cloud service, or heavy dependency. Preview calls are debounced while Advanced is open.

## Regression

The existing engine hygiene pass remains unchanged. The NLP layer preserves ordinary Vietnamese text, punctuation, line breaks, quotation characters, inline/fenced code, and URLs except for explicit recognized patterns outside protected text. The clone endpoint and Voice Lab flow are untouched.

## Tests

- `.venv/bin/python -m pytest -q tests/test_phase24_nlp.py tests/test_phase22_2_preset_regression.py` — **12 passed**
- Python compile, Node syntax check, and `git diff --check` — PASS

## Manual verification

1. Open **Cài đặt nâng cao** and confirm **Smart Text Processing** is enabled by default.
2. Enter `10/05/2026, giá 1.250.000đ lúc 20:45` and expand the preview; inspect the processed text.
3. Disable the checkbox and confirm the preview equals the original text; generate and confirm the request is still accepted.
4. Add a pronunciation entry to `data/nlp/custom_dictionary.json`, save it, then refresh preview to confirm it is applied.

## Remaining issues

The initial rule set intentionally covers only the requested, unambiguous patterns. More organization-specific pronunciations should be added to the editable custom dictionary rather than hardcoded.
