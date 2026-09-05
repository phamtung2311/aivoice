# Phase 30F Report

## Timestamp

2026-08-31 (Asia/Ho_Chi_Minh)

## Status

NO_GOOD_LOCAL_VC_PATH

## Objective

Assess whether free/local Voice Conversion can create useful new Vietnamese
Podcast Brand identities without an ideal human target reference.

## User Problem

Native presets were generic; the user's cloned voice is flat/sharp; an ideal
external human target is impractical.

## Production Safety

Git state was inspected. Only isolated research documents were added. No
production endpoint, frontend, profile, dependency, or model setting changed.

## Runtime Environment

The verified runtime is `.venv/bin/python` (Python 3.14.7). It has no Torch,
Seed-VC, OpenVoice, RVC, SpeechBrain, or other VC package installed.

## What Counts as Real Voice Conversion

Valid VC uses learned speaker/content/decoder conditioning. Pitch/EQ/formant,
speed, and reverb alone are excluded.

## Voice Conversion Landscape

Seed-VC/OpenVoice are target-reference systems; RVC requires a trained target;
VoicePrivacy anonymization is the only reviewed pseudo-speaker branch.

## New Identity Capability

Known-target conversion is supported by mainstream VC. New stable identity
without a target is not supported by them. VoicePrivacy pseudo-speakers are
experimental and not established as reusable Vietnamese identities.

## Speaker Anonymization Research

VoicePrivacy B1 derives a pseudo-speaker x-vector from an external pool while
retaining source bottleneck/F0. Its 2024 baseline is utterance-level and its
official evaluation is English-oriented; it is privacy research, not Podcast
voice design.

## Vietnamese / Tonal Language Considerations

No reviewed system has official Vietnamese VC validation. Tone/F0, vowels,
consonants, prosody, and vocoder artifacts are high risks. A bad converted WAV
would contaminate the eventual VieNeu reference.

## Source Voice Character Preservation

VC generally preserves content and substantial F0, rhythm, energy, emotion, and
prosody; it changes timbre. A flat/sharp source cannot be assumed to become a
warm/deep expressive Podcast performance.

## Podcast Voice Design Potential

No candidate has verified warm/deep/intimate Vietnamese identity control without
a target reference, target training, or unsupported manipulation.

## CPU-Only Feasibility

On i9-13900H/16 GB/CPU-only, Seed-VC/OpenVoice are possible but unbenchmarked
and do not solve identity sourcing. RVC training and VoicePrivacy are complexity
and RAM risks.

## Intel GPU Possibility

No verified Fedora Iris Xe/OpenVINO/XPU acceleration path was found for a
recommended candidate; CPU fallback would be necessary.

## Python Compatibility

Python 3.14 compatibility is unverified. Any future experiment needs an isolated
Python 3.10/3.11 environment, never the production `.venv`.

## Licensing / Commercial Risk

OpenVoice and RVC repository code are MIT, but weights/data require separate
review. VoicePrivacy pool/assets and generated-reference provenance also need
review. No legal guarantee is made.

## VieNeu-as-Source Architecture

`VieNeu preset → VC → new identity → VieNeu clone` is HIGH_RISK: it may create
clean source audio but compounds generic TTS and codec/VC artifacts.

## Voice Factory Architecture

Conceptually possible but unsupported now:

```text
Vietnamese source → content encoder → stable pseudo identity → VC WAV
  → audition → VieNeu encode_reference → Podcast Brand Voice
```

## Technology Comparison

See `voice_conversion_research/vc_comparison.md`.

## Primary Candidate

None for installation. VoicePrivacy B1-style anonymization is the most relevant
research concept but fails the current Vietnamese, stability, provenance, and
hardware evidence threshold.

## Findings

VOICE_CONVERSION_DOES_NOT_SOLVE_THE_IDENTITY_SOURCE_PROBLEM under the current
constraints. Speaker anonymization remains research-only.

## Limitations

No VC model was installed, downloaded, or run. No Vietnamese VC benchmark,
listening test, or legal opinion was performed.

## Decision

Do not pursue a local VC installation now.

## Recommended Phase 30G

Acquire one purpose-recorded, permissioned Vietnamese reference with desired
Podcast delivery and validate it using Phase 30B.

## Production Changes

None.

## Regression / Static Checks

`git diff --check` — passed. No Python research scripts were created and no
heavy model inference was run.
