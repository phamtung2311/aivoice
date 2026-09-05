# PHASE 30G REPORT — Vietnamese Open Voice Source Audit

## Timestamp

2026-08-31 (Asia/Ho_Chi_Minh)

## Status

`OPEN_VOICE_CASTING_FEASIBLE_WITH_LICENSE_REVIEW`

## Objective

Identify legally defensible, open Vietnamese multi-speaker speech sources for a future podcast brand-voice casting pipeline, without downloading data, cloning a voice, or changing production.

## User Problem

Preset TTS voices remain generic. A future casting pool could yield a more distinctive Vietnamese podcast voice only where source rights and consent are as strong as the technical fit.

## Production Safety

Research only. No dataset, model, audio, reference clip, embedding, or voice clone was downloaded or generated. No production files, dependencies, runtime code, or model configuration changed.

## Research Method

Reviewed official dataset cards, project repositories, published papers, and license/terms signals. Evaluated provenance, speaker diversity, duration, format, audio conditions, license scope, non-commercial restrictions, and speaker-specific derivative-use risk. Dataset, audio, transcript, and code licenses were treated separately.

## Vietnamese Speech Source Landscape

Common Voice Vietnamese is the strongest open technical pool observed: its v23 card lists 361 speakers, 18,777 MP3 clips, 22 total hours / 6.3 validated hours, and 413.72 MB. ViSpeech reports 449 speakers and >14 hours but has no clear audio-license evidence. VIVOS is smaller/cleaner read speech but has conflicting license signals. VieNeu 500h and Dolly are non-commercial. Web, social, celebrity, YouTube, and podcast audio were excluded.

## Dataset Comparison

| Dataset | Diversity | Audio / style | Rights posture | Result |
|---|---|---|---|---|
| Common Voice vi | 361 stated speakers; optional metadata | variable crowd short MP3 | CC0 signal plus identity/privacy terms | Conditional primary |
| ViSpeech | 449 stated speakers; three dialect labels | unscripted MP3 | unclear audio grant | Reject pending evidence |
| VIVOS | ~65 volunteers | quiet-room read speech | conflicting license reports | Reject pending proof |
| VieNeu / Dolly | 193 / 152 stated speakers | TTS corpora | CC-BY-NC / CC-BY-NC-SA | Restricted |

## Licensing Audit

Common Voice has a CC0-1.0 dataset license signal, favorable for ordinary copyright use. Separately, its download condition prohibits attempts to determine contributor identity. Mozilla staff say robust privacy practice would bar uses requiring identification by matching and grouping a contributor’s clips. VIVOS and ViSpeech lack a single verified commercial audio grant in the reviewed materials. NC licenses are incompatible with monetized podcast work.

## Voice Cloning / Derivative Use Analysis

Common Voice `VOICE_CLONING_USE` is **UNCLEAR**, not clearly allowed: the reviewed material does not expressly grant a permanent public synthetic voice based on an individual contributor, and its privacy discussion directly affects speaker grouping. Written review is required. VieNeu/Dolly are **RESTRICTED** commercially; unlicensed/web-derived sources are **NOT_ALLOWED**.

## Consent / Provenance

Volunteer contribution and anonymous IDs do not prove consent for branded synthetic likeness. Preserve release/version, source URL, terms snapshot, pseudonymous ID, approved purpose, reviewer, retention, and deletion path. Do not seek real identities. Do not publish a recognizably derived voice without direct specific consent and a talent agreement.

## Audio Quality

Common Voice supports a technical audition but not guaranteed studio/podcast quality: it contains short crowd MP3 clips. Filter noise, clipping, silence, level, continuity, and decodability; blind listening decides delivery quality. VIVOS may be cleaner but is not usable until rights are resolved.

## Speaker Diversity

Common Voice is the broadest vetted candidate. A future pilot may start with 20–50 anonymous IDs, narrow technically to ~10, then audition. Age/gender/accent/dialect metadata is optional and incomplete. Do not exclude a speaker merely for Bắc/Nam/Trung labeling; listening determines neutrality.

## Podcast Casting Potential

Conditional only. Common Voice can yield contrasting voices for an anonymous technical audition, but short scripted prompts cannot establish long-form host stamina or a right to create a permanent brand voice. Directly consented Vietnamese talent remains the production-safe route.

## Automatic Prefiltering Potential

Feasible locally using duration, clipping, silence, RMS/loudness, noise/SNR proxy, decodability, and optional broad F0. These reject technical failures only; they must not infer warmth, trustworthiness, brand fit, gender, or regional suitability.

## Local Processing Feasibility

CPU-only batch work is feasible after authorization. Expected Common Voice v23 footprint: approximately 0.4–0.5 GB compressed and 1–2 GB working space after extraction/derivatives. No download occurred. No hosted service or GPU is required for inventory/filtering.

## Primary Source

**Mozilla Common Voice Vietnamese (conditional)** — technically the best free multi-speaker pool, pending written license/privacy review.

## Secondary Source

**NONE.** No fallback cleared commercial, provenance, and audio-rights thresholds.

## Brand Voice Risk

**High until rights review closes.** A recognizable contributor-derived branded voice can create privacy, consent, personality-right, and reputational risks even where dataset copyright licensing is permissive.

## Findings

1. A free Vietnamese multi-speaker technical casting pool exists: Common Voice.
2. It is not a no-review source for speaker-level brand cloning because its privacy commitment cautions against contributor matching/grouping.
3. Other discovered sources are non-commercial or lack sufficient authoritative audio-license/provenance evidence.
4. A short blind technical audition is feasible only after written approval; production brand deployment should use direct talent consent.

## Limitations

No files were downloaded or listened to, so per-speaker quality, duration, neutrality, and duplicate/mixed-client-ID behavior are unverified. Metadata changes by release. This is not legal advice and does not replace rights-holder/counsel confirmation.

## Decision

`OPEN_VOICE_CASTING_FEASIBLE_WITH_LICENSE_REVIEW` — do not acquire or process open audio until Common Voice speaker-level use is affirmatively cleared. If it is not cleared, abandon the open-data route for a directly consented source.

## Recommended Phase 30H

Obtain a written determination for the exact Common Voice Vietnamese release and the proposed anonymous speaker-casting / synthetic-output use; only then run a minimal casting pilot.

## Production Changes

None.

## Regression / Static Checks

`git diff --check` must pass. No tests were added: this is documentary research and no fake existence-only test was created.

## Primary references

- [Mozilla Common Voice catalogue](https://commonvoice.mozilla.org/data)
- [Mozilla Data Collective download terms example](https://mozilladatacollective.com/datasets/cmfzu8u8wa555eq8onrk334h4)
- [Mozilla staff discussion of identity condition](https://discourse.mozilla.org/t/speaker-ids-for-speaker-identification-model/114358)
- [ViSpeech repository](https://github.com/TranNguyenNB/ViSpeech)
- [Common Voice corpus paper](https://aclanthology.org/2020.lrec-1.520.pdf)

