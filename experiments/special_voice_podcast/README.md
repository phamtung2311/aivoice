# Podcast Brand Voice — Phase 30B

This is isolated local R&D for a potential Vietnamese podcast brand voice. It
does not provision a voice, change the UI, or alter `/api/tts` or `/api/voices`.
Phase 30B is reference-led: evaluate a permissioned speaker reference with
native VieNeu production defaults before considering any parameter changes.

## Start only with a permissioned reference

Place one WAV at:

`reference_audio/podcast_reference.wav`

Alternatively, provide a separately permissioned candidate such as
`reference_audio/candidate_01.wav`. Each candidate is an independent possible
voice identity; never combine speakers or average their embeddings.

Read `reference_contract.md` and `podcast_voice_spec.md`, then validate first:

```bash
python experiments/special_voice_podcast/runner.py --validate-only
```

When the reference is suitable, generate the six blind short-test samples with
an existing normal VieNeu control voice:

```bash
python experiments/special_voice_podcast/runner.py --control-voice default
```

The runner uses speed `1.0`, native production sampling defaults, the same local
engine/output format for both conditions, and no post-processing. It renders
only three representative sentences. Do not run the long-form script until the
blind listening review is STRONG or PROMISING and the user approves it.
