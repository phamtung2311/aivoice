# Phase 24.1 — Date Normalization Fix

## Status

Complete.

## Change

The `DD/MM/YYYY` rule now delegates to `_normalize_ddmmyyyy()`, which explicitly emits exactly one literal `năm` between the month and the year value:

```text
ngày <day> tháng <month> năm <year>
```

No other NLP rule, API, Smart Text Processing control, or architecture changed.

## Regression coverage

- `10/05/2026` → `ngày mười tháng năm năm hai nghìn không trăm hai mươi sáu`
- `01/01/2004` → `ngày một tháng một năm hai nghìn không trăm lẻ bốn`
- `31/12/1999` → `ngày ba mươi mốt tháng mười hai năm một nghìn chín trăm chín mươi chín`

The month `05` naturally reads as `năm`; the explicit year introducer adds the required second, separate `năm` without altering any non-date format.

## Files modified

- `backend/app/tts/nlp.py`
- `tests/test_phase24_nlp.py`

## Files created

- `diagnostics/phase24_1_date_normalization_report.md`

## Validation

- `.venv/bin/python -m pytest -q tests/test_phase24_nlp.py` — **9 passed**
- `.venv/bin/python -m py_compile backend/app/tts/nlp.py` — PASS
- `node --check frontend/app.js` — PASS
- `git diff --check` — PASS
