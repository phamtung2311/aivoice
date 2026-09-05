# Phase 30O Report

## Timestamp

2026-08-31 (Asia/Ho_Chi_Minh).

## Status

`PHASE30O_CONTROLLABLE_PROSODY_READY`

## Objective

Provide optional, deterministic, user-editable pause control for TTS without an
AI/LLM, a new model, Qwen, or any change to the experimental M-A identity.

## Architecture

The workflow has three distinct layers: immutable-in-use Original Text, a
visible Editable TTS Script, and Generated Audio. The frontend sends the
effective script only when the user has supplied one. The backend owns parsing
and audio assembly; no frontend interpretation is authoritative.

## Markup Syntax

`|` is light, `||` is medium, and `|||` is long. The syntax had no conflict
with the audited application text behavior and is safe for Vietnamese Unicode.
Malformed runs, leading/trailing markers, and adjacent markers are rejected
rather than guessed.

## Pause Semantics

`podcast_prosody_v1` centralizes light/medium/long targets at 70/140/260 ms.
These are target effective boundary pauses, not unconditional zero insertions.

## Parser

`backend.app.tts.prosody.parse_prosody_script(text)` returns immutable
`ProsodySegment(text, pause_after_ms)` values. It has no model, network, or LLM
dependency and preserves punctuation in the clean spoken text.

## Audio Assembly

Each parsed spoken segment uses the established clean-text engine path. Markers
are therefore never passed to VieNeu. At an explicit boundary, the assembler
measures generated trailing/leading silence and inserts only the deficit to the
explicit target. The ordinary punctuation target is not also applied there, so
punctuation plus a marker cannot stack two independent automatic gaps.

## Original vs TTS Script

The original textarea is never replaced automatically. A separate editable TTS
Script is the synthesis source when supplied; the user can reset it explicitly
from Original Text. An empty TTS Script retains the ordinary existing text path.

## Frontend Controls

The TTS Script offers cursor-position controls for `+ Nghỉ nhẹ`, `+ Nghỉ vừa`,
and `+ Nghỉ dài`, plus `Đặt lại từ văn bản gốc`. Plain direct editing remains
the source of truth.

## API Compatibility

`/api/tts` accepts optional `tts_script` and `prosody_markup`. Requests with
ordinary `text` and no script retain the existing generation call unchanged.
A script without markers is still a user-edited clean synthesis script; only a
true marker request takes the prosody assembly path.

## History / Reproducibility

New browser history metadata records `originalText`, `effectiveTtsScript`,
`prosodyMarkupEnabled`, `prosodyVersion`, `pausePresetVersion`, voice, and
speed. Legacy history records normalize safely using their existing `text`.
IndexedDB audio storage is unchanged.

## Prosody Version

`podcast_prosody_v1` identifies the deterministic parser and 70/140/260 ms
preset set for marked generations.

## Tests

New focused tests: 6 passed, 0 failed.

- parser: no marker, all three marker levels, multiple markers, Vietnamese
  Unicode, adjacent punctuation, spaces, and newlines;
- malformed-marker rejection;
- target semantics and no period-plus-marker double insertion;
- markers stripped before the model call;
- API ordinary-text compatibility and editable-script behavior.

JavaScript syntax validation, Python compilation, and `git diff --check` passed.

## Regression Results

The Phase 30O targeted suite is green: 6 passed / 0 failed. The existing
`tests/test_api.py` suite could not complete in this environment because its
first pre-existing `TestClient` health request hangs before any test assertion;
this is reported rather than treated as a pass. A broad collection also reaches
an unrelated experiment load-test collection error outside `tests/` (178 tests
collected before that error). No model inference was run.

## Production Changes

Generic optional prosody-control infrastructure only. M-A production
integration: **NO**.

## User Control Principle

1. Original user text is preserved.
2. TTS Script is visible.
3. Explicit pause instructions are editable.
4. Future automatic suggestions are suggestions only.
5. User edits take precedence.
6. Generation works without an AI suggestion system.
7. The effective synthesis script is stored for reproducibility.

## Limitations

This phase does not suggest phrasing, alter M-A, optimize cadence, or use a
speaker identity. Existing generated silence already longer than a requested
target is preserved to avoid destructive audio trimming.

## Decision

`PHASE30O_CONTROLLABLE_PROSODY_READY`

## Next Step

Plan only: Phase 30P — Auto Prosody Suggestion. It may propose markers, but the
Phase 30O parser and user edits remain independent and authoritative.
