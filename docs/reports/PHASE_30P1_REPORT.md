# Phase 30P.1 Report

## Timestamp

2026-09-01 (Asia/Ho_Chi_Minh).

## Status

`PHASE30P1_REFINED_PROSODY_READY_FOR_MANUAL_VALIDATION`

## User-Observed Problem

The real long-form test found V1 mechanical: it proposed explicit pauses at
enumeration commas and ordinary subordinate clauses where written punctuation
was already likely sufficient.

## Root Cause

V1 treated a long sentence plus a comma and substantial neighboring text as a
positive boundary. It did not distinguish lists, connector strength, sentence
position, subordinate clauses, or punctuation sufficiency before selection.

## Previous V1 Behavior

The exact five-paragraph regression passage produced 19 markers. Its output
included unwanted examples after `những công việc quen thuộc`, `một thói quen
nhỏ`, `một người mà chúng ta tình cờ gặp`, and before `khi` after an ordinary
comma.

## Refined Architecture

The local deterministic engine is now explicitly two-stage:

1. **Candidate Analysis** emits `BoundaryCandidate` objects with position,
   punctuation/context, features, reason, and score.
2. **Selection / Suppression** applies score thresholds, explicit suppression
   rules, manual-marker protection, and density spacing before inserting a
   marker.

## Candidate Analysis

Candidates cover blank-line paragraphs, classified Vietnamese connectors, and
punctuation. Punctuation candidates remain in debug output even though they are
normally suppression-only, so their non-selection is inspectable.

## Selection / Scoring

Paragraph boundaries score 10. A strong internal contrast receives +3 plus +1
for each sufficiently long side, then −1 if an existing comma already supplies
a natural cue; it must still reach the centralized threshold of 4. Soft
connectors never qualify by themselves. Low scores and close candidates are
suppressed with a recorded reason.

## Enumeration Detection

Comma candidates are suppressed for repeated determiner patterns (`một …, một
…`; `những …, những …`) and conservative parallel/coordinator signals (`và`,
`hoặc`, `hay`, `cũng như`). This fixes the observed list false positives while
preferring a false negative to an artificial interruption.

## Connector Classification

Strong: `nhưng`, `tuy nhiên`, `ngược lại`, `mặt khác`, `trong khi đó`.
Reasoning: `vì vậy`, `do đó`, `bởi vậy`. Soft: `có lẽ`, `thực tế`, `đặc biệt`,
`và đôi khi`, `quan trọng hơn`, `nói cách khác`. Sentence-initial connectors
are suppressed; a strong connector must divide two substantial internal clauses
to become an explicit intervention.

## Punctuation Sufficiency

Comma defaults to no marker. Semicolon and colon are explicitly
`punctuation_sufficient`; they do not create an automatic marker. Subordinate
starts (`khi`, `nếu`, `vì`, `để`, `mà`, `dù`) after a comma are also suppressed.
This is a deterministic linguistic heuristic, not a model prediction.

## Anti-Overpause Strategy

Selected boundaries require 12 words and 68 characters of separation. Existing
manual markers remain locked occupied boundaries. Enumeration, subordinate,
soft, initial-connector, punctuation-sufficient, low-score, and proximity
suppression reasons are retained in debug metadata.

## Canonical Marker Formatting

Automatic markers are rendered readably as `..., | nhưng ...` or
`... |||` before a paragraph break. Manual markers are neither moved nor
reformatted. For automatic output, metadata records each inserted formatting
token; removing those tokens in reverse insertion order reconstructs Original
Text exactly. No user punctuation or wording is changed.

## Real Regression Passage

The required five-paragraph passage is preserved as
`tests/fixtures/phase30p1_real_passage.txt`. V1.1 has 509 words, 36 candidates,
7 selected, and 29 suppressed: 1.38 markers per 100 words. Selected reasons are
four `paragraph_boundary` controls and three `contextual_connector` controls.
Suppression totals: 20 enumeration, 4 punctuation-sufficient, 3 sentence
initial connectors, and 2 weak soft connectors.

## V1 vs V1.1

| Policy | Selected markers | Evidence |
| --- | ---: | --- |
| `vi_prosody_suggest_v1` | 19 | long comma rule admitted list/subordinate false positives |
| `vi_prosody_suggest_v1_1` | 7 | preserves only four predictable paragraph controls and three substantial contrasts |

The reduced count is not the quality claim by itself: the important change is
that enumeration and punctuation-sufficient cases now receive explicit,
inspectable suppression reasons.

## Explainability

Selected output includes candidate features, reason, score, and insertion
formatting. `debug` includes candidate count and each suppressed candidate with
its suppression reason. The normal frontend remains simple.

## Tests

Phase 30P.1: 8 passed. Phase 30P: 8 passed. Phase 30O prosody: 7 passed.
Combined focused result: 23 passed, 0 failed. Coverage includes enumerations,
coordinated lists, contrast, initial/soft connectors, subordinate clauses,
semicolon/colon sufficiency, canonical spacing, manual-marker preservation,
reconstruction, parser compatibility, determinism, and the real passage.

## Regression Results

JavaScript syntax validation, Python compilation, and `git diff --check`
passed. The known pre-existing FastAPI TestClient health-request hang was not
repeated and is not reported as a pass. No audio/model inference was run.

## Production Changes

Generic optional suggestion infrastructure only:

- `backend/app/tts/prosody_suggest.py`
- `frontend/app.js` (store/restore suggestion-policy version in history)
- `tests/fixtures/phase30p1_real_passage.txt`
- `tests/test_phase30p1_prosody_refinement.py`

M-A PRODUCTION INTEGRATION: **NO**.

## Limitations

This is still a conservative surface-rule system. It cannot prove listener
preference or deep semantic phrasing; the user must inspect the proposed script
before audio generation. Paragraph controls remain intentional: current text
preprocessing preserves blank lines but sentence splitting discards empty lines,
so `|||` provides a predictable explicit structural boundary rather than relying
on an implicit blank-line pause.

## Decision

`PHASE30P1_REFINED_PROSODY_READY_FOR_MANUAL_VALIDATION`

## Manual Validation

1. Restart the backend and hard-refresh the frontend if they are running.
2. Paste the exact contents of `tests/fixtures/phase30p1_real_passage.txt` into
   **Văn bản**.
3. Click **✨ Đề xuất nhịp đọc**.
4. Do not edit it or generate audio yet.
5. Copy the complete proposed TTS Script and send it back for human review.

## Next Step

Wait for user manual validation. Phase 30Q remains blocked. If the script is
still mechanical, evaluate Phase 30P.2 rather than changing voice identity.
