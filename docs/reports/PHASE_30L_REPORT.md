# Phase 30L Report

## Timestamp

2026-08-31 (Asia/Ho_Chi_Minh).

## Status

`PHASE30L_LONGFORM_BASELINE_SELECTED`

## Objective

Compare the two preserved finalists under Vietnamese podcast material without
tuning either identity or modifying production.

## Finalists

The internal finalists were CONTROL (original G2-06 / G2-B) and K-A (slightly
deeper refinement). The comparison remained blind until the user’s verdict was
locked.

## Keeper Integrity

All seven keeper entries and all 43 protected artifacts passed SHA-256 and byte
size revalidation. No audio, conditioning, or production artifact was altered.

## Test Material

Phase 30L prepared the fixed conversational, reflective, informational, and
long-form Vietnamese test material. No new Qwen identity was generated.

## Generation Conditions

The planned comparison used preserved conditioning and identical VieNeu settings:
speed 1.0, denoise false, and deterministic NumPy seed 30109. No per-voice tuning
or post-processing was authorized.

## Chunking

The validation runner uses the existing production text preprocessing, sentence
splitting, 240-character outer chunking, inference, gap calculation, and joining
logic. No production code was changed.

## Blind Mapping

The locked mapping is Voice A → K-A and Voice B → CONTROL (original G2-06 / G2-B).

## Technical Measurements

Technical measurements remain diagnostic only and are not used to select a
winner.

## Long-Form Stability Test

The user found Voice A listenable for long-form material but too familiar/generic
for the intended brand identity. Voice B was rejected. This does not approve a
final production voice.

## User Listening Protocol

The user’s perceptual judgment is authoritative; no automatic vote-count or
metric-based winner was applied.

## User Blind Verdict

- Test 1: Voice B selected.
- Test 2: rejected; neither finalist demonstrated an acceptable advantage.
- Test 3: both voices acceptable.
- Test 4 long-form: Voice A was listenable but perceived as too familiar/generic;
  Voice B was rejected.

Voice B is not a final winner despite Test 1. Voice A is the only finalist that
survived the long-form listening-comfort test, but is not approved as the final
brand identity because its identity is insufficiently distinctive.

## Revealed Mapping

Voice A resolves to K-A, the slightly deeper refinement. Voice B resolves to
CONTROL, original G2-06 / G2-B.

## Long-Form Baseline

K-A is explicitly marked `LONG_FORM_BASELINE_KEEPER`: natural enough and
listenable for long-form use, useful as the baseline for the next refinement,
and not the final brand voice.

## Brand Distinctiveness Finding

The remaining problem is no longer basic human-likeness alone. The surviving
baseline is sufficiently listenable for long-form use but lacks enough distinctive
identity for the intended brand voice.

## Keeper Status

K-A remains active as `LONG_FORM_BASELINE_KEEPER`. CONTROL remains preserved as
historical experimental evidence but is not an active finalist. Neither keeper is
deleted or altered in its audio or conditioning.

## Final Decision

`PHASE30L_LONGFORM_BASELINE_SELECTED`. No final production voice is selected.

## Phase 30M Direction

Plan only: Phase 30M — Distinctiveness Refinement. Starting from K-A, investigate
the smallest controlled changes in subtle texture, recognizable resonance,
mid/low-register character, and a believable timbral signature, without losing
long-form comfort, naturalness, Vietnamese human-likeness, warmth/depth, or
conversation. Avoid deeper-only changes, broad random search, extreme bass, rasp,
announcer/trailer/theatrical delivery, aggression, artificial character voices,
real-person imitation, breathiness, feminine drift, and slow cadence. The work
remains isolated from production.

## Production Changes

None.

## Decision

Wait for explicit authorization before beginning Phase 30M.
