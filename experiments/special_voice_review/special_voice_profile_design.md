# Minimal special voice profile design

## Existing fit

VieNeu already represents a voice as native profile data: `speaker_emb` plus optional reference `codes`, with descriptive metadata. AIVoice persists saved profiles in `data/voices/voices.json` through `voice_store.serialize_profile()` / `deserialize_profile()`.

The future safe extension is a small metadata/profile layer **alongside** an existing voice, not a separate engine:

```text
SpecialVoiceProfile
  id, display name, category
  base voice/profile reference
  allowed native generation overrides
  optional text-processing selection (off/default; never silent rewriting)
  chunk/pause profile chosen from existing safe policies
  reference-quality recommendations and metadata
```

The underlying `speaker_emb` and `codes` serialization must remain unchanged. A profile should identify a voice and choose bounded request settings; it must not duplicate audio, embeddings, speaker codes, or another TTS pipeline.

## Future categories

- Product Review: clearer commercial cadence and moderate energy.
- Meme / Breath: a deliberately chosen humorous/breathy **identity**, not automated breaths.
- Sarcastic / Edgy Comedy: dry/teasing identity and bounded generation profile; never inject profanity.
- Horror Story: low-energy atmospheric narrator identity with natural pauses.

All are GREEN only when they use existing CPU ONNX inference and bounded configuration. Any second model, external inference, or unverified post-processing is outside this design.
