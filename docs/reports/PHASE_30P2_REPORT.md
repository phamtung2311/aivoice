# Phase 30P.2 Report

## Timestamp

2026-09-01 (Asia/Ho_Chi_Minh).

## Status

`PHASE30P2_CONTEXT_AWARE_PROSODY_READY_FOR_MANUAL_VALIDATION`

## User-Observed Limitation

Phase30P.1 safely removed mechanical comma pauses, but on realistic podcast
text it mostly emitted structural paragraph markers and missed rhetorical flow.

## Root Cause

P.1 deliberately scores local punctuation candidates. It has no representation
of a title, a neighboring answer/reveal sentence, or the difference between a
section and an ordinary paragraph.

## Architecture Audit

Three options were assessed. A richer deterministic planner directly covers the
observed, bounded structures (titles and adjacent sentences) with transparent
tests. A lightweight local classifier would add training/model maintenance with
uncertain Vietnamese discourse benefit. A local language model has materially
higher RAM/disk/cold-start/dependency risk on the 16 GiB CPU-only production
machine, without evidence it is needed for these structured cases.

## Chosen Architecture

**DETERMINISTIC CONTEXT PLANNER.** It is local, CPU-fast, zero-download,
offline, deterministic, and has no new dependency or model memory/disk cost.
It is not claimed to perform open-ended semantic understanding.

## Planner Design

`Context Planner → Phase30P.1 Safety Selection → visible editable TTS Script`.
The planner creates structured semantic candidates; the existing P.1 selection
logic supplies manual-marker protection, density/spacing guards, canonical
rendering, and fallback. Failure falls back to `vi_prosody_suggest_v1_1` with
`planner_mode: v1_1_fallback` metadata.

## Phase30P.1 Safety Reuse

No enumeration, punctuation, or manual-marker logic was duplicated. P.1 remains
available unchanged as both the shared safety layer and the fallback policy.

## Section Detection

Recognized title forms include `Phần N:`, `Chương N:`, `Mở đầu:`, and `Kết
luận:`. A section-title-to-body boundary proposes `|||`; ordinary paragraphs
only receive a medium candidate when an explicit transition starter is present.
Blank lines no longer mechanically mean a long marker.

## Discourse Features

The planner currently recognizes: section title/transition, ordinary paragraph
transition, question type, answer/reveal lexical starts, and sentence adjacency.
Its proposal metadata contains role before/after, reason, planner score, and
safety decision.

## Question / Answer Planning

A question alone is low confidence and disappears. A question followed by a
meaningful answer/reveal starter (`Với tôi`, `Có lẽ`, `Đây chính là`, `Đó là`,
`Thực ra`, `Câu trả lời`) proposes `||` and must still pass P.1 safety.

## Paragraph Policy

Section transitions use `|||`. Continuing paragraphs generally receive no
marker; only explicit discourse-transition paragraphs can propose `||`. This
keeps natural punctuation and VieNeu timing primary.

## Enumeration Safety

Preserved through P.1: repeated determiners, coordinated lists, ordinary comma
lists, and protected numeric tokens remain non-intervention cases. The real
fixture’s horn/sun/sigh list and `không vấp váp, không hụt chữ, và...` list do
not gain markers.

## Manual Marker Safety

Existing `|`, `||`, and `|||` remain locked. The planner neither changes nor
duplicates them; shared P.1 proximity checks suppress conflicting proposals.

## Explainability

Selected semantic entries expose marker, source position, role before/after,
reason, planner score, and `safety_decision: accepted`. Rejections retain their
P.1 suppression reason in debug metadata.

## Fallback

If the context planner raises an internal error, the endpoint returns valid V1.1
output with `planner_mode: v1_1_fallback`. TTS and prosody suggestion therefore
remain available without any optional component.

## Versioning

Parser: `podcast_prosody_v1` unchanged. Safety policy: `vi_prosody_suggest_v1_1`
unchanged. New planner response version: `vi_prosody_planner_v2`.

## Real Podcast Fixture

The exact user-tested 1,038-word script is at
`tests/fixtures/phase30p2_real_podcast.txt`. It contains 4 sections and 16
paragraphs. No content was rewritten before analysis.

## P.1 vs P.2

| Policy | `|` | `||` | `|||` | Total |
| --- | ---: | ---: | ---: | ---: |
| P.1 | 0 | 0 | 12 | 12 |
| P.2 | 0 | 7 | 4 | 11 |

P.2 created 14 semantic proposals, accepted 11, and rejected 3 by shared
safety/density logic. The meaningful difference is role variation, not count.

## Required Example Analysis

- **A — listener question → personal answer:** the question is followed by
  `Với tôi`, a configured answer/reveal start; P.2 proposes `||`.
- **B — rhetorical question → answer:** the question is followed by `Có lẽ`,
  which in answer position is an answer/reveal start; P.2 proposes `||`.
- **C — setup question → reveal:** the question is followed by `Đây chính là`;
  P.2 proposes `||` as a question/reveal transition.

These are generalized adjacency features, not fixture-specific string rules.

## Performance

Text-only regular-expression/scanner analysis is effectively immediate for the
fixture; no artificial delay is added.

## Model / Dependency Impact

New model: none. New download: none. RAM/disk increase: negligible source code
only. Offline: yes. Expected suggestion latency: sub-second on this CPU.

## Tests

Phase30P.2: 5 focused tests. Together with P.1, P, O, Q, and Special Voice
focused suites: 32 passed, 0 failed. Tests cover section/paragraph distinction,
question/answer, setup/reveal, manual markers, enumeration safety, formatting,
determinism, fallback, parser compatibility, and the real fixture.

## Regression Results

Frontend JavaScript syntax, Python compilation, and `git diff --check` passed.
The known unrelated TestClient health-request hang was not rerun. No audio,
VieNeu, Qwen, or network inference was used.

## Production Changes

- `backend/app/tts/prosody_suggest.py`
- `backend/main.py` (existing suggestion endpoint invokes the planner)
- `tests/fixtures/phase30p2_real_podcast.txt`
- `tests/test_phase30p2_context_planner.py`

## M-A / Phase30Q Safety

Podcast Brand Beta: unchanged. M-A/M-C keepers: unchanged. Qwen: unused.
Phase30Q remains Beta and awaits long-form listening only after text review.

## Limitations

The planner recognizes a deliberately narrow set of surface discourse patterns.
It cannot prove that a proposed pause will sound better; the user remains the
final editor and listener.

## Decision

`PHASE30P2_CONTEXT_AWARE_PROSODY_READY_FOR_MANUAL_VALIDATION`

## Manual Validation

1. Restart the backend and hard-refresh the frontend.
2. Paste the exact fixture into **Văn bản**.
3. Click **✨ Đề xuất nhịp đọc**.
4. Do not edit markers and do not generate long-form audio yet.
5. Copy the complete proposed TTS Script and return it for review.

## Next Step

Wait for manual text validation. If accepted, resume the Phase30Q long-form
listening test with Podcast Brand Beta at speed 1.0. Phase30R is not implemented.
