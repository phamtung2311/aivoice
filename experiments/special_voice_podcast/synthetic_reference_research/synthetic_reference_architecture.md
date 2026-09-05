# Synthetic-reference architecture assessment

| Option | Pipeline | Assessment |
|---|---|---|
| A — Direct Vietnamese voice design | Vietnamese VoiceDesign → VieNeu | Unavailable: none verified |
| B — Voice design plus Vietnamese bridge | VoiceDesign → external Vietnamese bridge → VieNeu | Unsupported: no qualifying bridge; three stages amplify drift |
| C — Virtual speaker plus multilingual TTS | Virtual speaker generator → Vietnamese TTS → VieNeu | Unsupported: Spark has no Vietnamese bridge |
| D — Synthetic reference from another TTS | Qwen VoiceDesign English → 6–8 sec WAV → VieNeu → Vietnamese | Primary experimental path |
| E — Direct human reference | Permissioned Vietnamese talent → VieNeu | Production-safe fallback |

## Primary architecture

description plus recorded reproducibility settings
→ Qwen3-TTS-12Hz-1.7B-VoiceDesign, English, new synthetic voice
→ select one clean synthetic 6–8 second English WAV
→ VieNeu encode_reference, producing speaker embedding plus MOSS codes
→ VieNeu V3Turbo CPU, Vietnamese production TTS

The identity originates in Qwen VoiceDesign description/sampling, not a human target, public corpus speaker, celebrity, or preset manipulation. VieNeu remains the proposed daily engine only if the audition passes.

## Risks

Qwen-generated artifacts can become conditioning artifacts. VieNeu uses both an x-vector and time-varying codec codes without documented disentanglement, so cross-language prompting can drift. Archive the synthetic WAV, Qwen version, description, English text, generation settings, hash, and licensing record.

