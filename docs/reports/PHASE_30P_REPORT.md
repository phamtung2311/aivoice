# Phase 30P Report

## Timestamp

2026-08-31 (Asia/Ho_Chi_Minh).

## Status

`PHASE30P_AUTO_PROSODY_SUGGESTION_READY`

## Objective

Add local, deterministic Vietnamese pause proposals to the existing editable
Phase 30O TTS Script workflow. The system suggests; the user decides.

## Locked Phase 30O Foundation

Phase 30O marker syntax and parser semantics are unchanged: `|`, `||`, and
`|||` remain 70/140/260 ms target effective pauses under
`podcast_prosody_v1`. The Phase 30O parser remains the sole authoritative
interpreter before VieNeu synthesis.

## Suggestion Architecture

`backend.app.tts.prosody_suggest.suggest_prosody(text)` is a separate,
text-only rule engine. It returns an insert-only proposed TTS Script,
`vi_prosody_suggest_v1`, and explainable candidate metadata. The frontend calls
`POST /api/tts/prosody/suggest` only when the user presses `✨ Đề xuất nhịp đọc`.
It writes the result into the existing editable TTS Script; it never generates
audio or changes Original Text.

## Vietnamese Rules

- A real blank-line paragraph boundary gets `|||`, except at script end.
- A connector can receive `|` only when both surrounding sentence portions
  meet conservative word thresholds. Centralized signals include `nhưng`,
  `tuy nhiên`, `vì vậy`, `do đó`, `trong khi đó`, `mặt khác`, `thực tế`,
  `đặc biệt`, `quan trọng hơn`, `ngược lại`, `nói cách khác`, `và đôi khi`,
  and `có lẽ`.
- A comma, semicolon, or colon is considered only in an already long sentence
  with sufficiently substantial clauses on both sides. A comma alone is not a
  rule.

## Anti-Overpause Strategy

The centralized configuration requires at least 7 words before and 5 after a
candidate boundary, 18 words for long-sentence punctuation candidates, and at
least 8 words / 42 characters between retained suggestions. Strong paragraph
boundaries are selected first; lower-priority candidates too near a retained or
manual boundary are discarded. Existing markers are treated as occupied locked
user decisions.

## Marker Density

The validation corpus confirms minimum useful intervention:

| Case | Chars / words | Markers | Reasons |
| --- | ---: | ---: | --- |
| Conversational | 75 / 17 | 0 | — |
| Reflective | 164 / 37 | 1 | contextual connector |
| Informational (date/time/money) | 143 / 32 | 0 | — |
| Comma-heavy | 97 / 21 | 1 of 4 commas | long clause |
| Long sentence | 185 / 42 | 1 | contextual connector |
| Short sentence | 16 / 4 | 0 | — |
| Existing manual marker | 114 / 25 | 1 preserved | user decision |

## Explainability

Each automatic suggestion includes its character position, marker, reason, and
priority. Current reasons are `paragraph_boundary`, `contextual_connector`,
`long_sentence_clause`, and `long_sentence_structural_punctuation`.

## Manual Marker Precedence

Existing `|` / `||` / `|||` text is retained verbatim. The proposal engine does
not add a candidate within the protected neighborhood of a user marker; it does
not merge, strengthen, or overwrite manual markup.

## Smart Text Processing Interaction

Order is: Original Text → suggestion (raw original) → visible/editable TTS
Script → Phase 30O parser → Smart Text Processing on each clean parsed segment
→ VieNeu. Markers never enter the normalizer, so normalization cannot split or
move a requested boundary. Date, time, decimal, and money-like tokens are also
protected from suggestion punctuation candidates.

## Frontend Workflow

The new action appears beside the existing pause controls. If the TTS Script is
non-empty and differs from Original Text, the user must confirm before it is
replaced. They can then edit/remove every marker, use the unchanged reset
control, or generate only when ready.

## API

`POST /api/tts/prosody/suggest` accepts `{ "text": "..." }` and returns
`suggested_script`, `prosody_version`, `suggestion_version`, and developer
explainability metadata. It has no model, network, or synthesis dependency.

## Versioning

Parser semantics remain `podcast_prosody_v1`; suggestion policy is separately
versioned as `vi_prosody_suggest_v1`.

## Validation Corpus

The seven text-only cases above cover conversational, reflective,
informational, punctuation-heavy, long, short, and existing-manual-markup
scripts. The focused tests also verify source reconstruction after marker
removal and parser acceptance of the proposed script.

## Tests

New Phase 30P tests: 8 passed, 0 failed. They cover short/no-marker behavior,
comma density, long contextual clauses, paragraph boundaries, protected dates /
times / money, manual markers, determinism, insert-only reconstruction, parser
acceptance, and endpoint version/explainability. Phase 30O regression tests:
7 passed, 0 failed. Combined focused result: 15 passed, 0 failed.

## Regression Results

JavaScript syntax validation, backend Python compilation, and `git diff --check`
passed. The known pre-existing `tests/test_api.py` TestClient health-request hang
was not rerun repeatedly and is not reported as a pass. No model inference was
run.

## Production Changes

Generic optional prosody suggestion infrastructure:

- `backend/app/tts/prosody_suggest.py`
- `backend/app/tts/prosody.py`
- `backend/main.py`
- `frontend/index.html`
- `frontend/app.js`

M-A PRODUCTION INTEGRATION: **NO**.

## Limitations

These are deliberately conservative surface rules, not semantic understanding.
The engine does not rewrite content, model listener preferences, or decide what
the user must synthesize. It does not make a listening-quality claim; manual
review and audition remain required.

## User Control Principle

Original text is preserved; the TTS Script is visible and editable; every
marker can be deleted or changed; future suggestions remain optional; user edits
take precedence; generation works without AI; and the effective editable script
remains stored by Phase 30O history metadata.

## Manual Smoke Test

1. Paste the paragraph below into **Văn bản**.
2. Click **✨ Đề xuất nhịp đọc**.
3. Confirm that the suggested TTS Script contains one light pause before
   `nhưng` and one major pause at the blank-line boundary.
4. Remove or change one marker, then click **Tạo giọng nói**.

```text
Chúng ta đã đi qua một ngày rất dài với nhiều cuộc họp và nhiều suy nghĩ chưa kịp gọi tên, nhưng điều quan trọng là vẫn còn thời gian để ngồi lại và lắng nghe nhau.

Sau đó, chúng ta có thể bắt đầu lại một cách bình tĩnh hơn.
```

## Decision

`PHASE30P_AUTO_PROSODY_SUGGESTION_READY`

## Next Step

Plan only: Phase 30Q — Podcast Long-Form Brand Voice Stress Test, combining
M-A with the approved controllable prosody workflow after manual validation.
