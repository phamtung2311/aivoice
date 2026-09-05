# Phase 42B — Human Listening Review

Status: **HUMAN QUALITY FAIL — ZERO-SHOT DIRECTION CLOSED**

## Recorded owner result

The owner listened to the complete V-TTS/VieNeu comparison and concluded:
**“Tất cả đều chả ra gì.”**

Therefore Phase 42B is a technical CPU PoC pass but a human-quality failure.
Do not tune V-TTS, change the 3–10 second references, render Test 4, or use
these artifacts for production. Phase 42C investigates a separate trainable
voice-conversion architecture instead.

Listen to each pair at the same comfortable playback volume. These files are
research artifacts only; neither engine is being promoted. Do not infer quality
from sample rate, duration, or filename.

| Test | Focus | V-TTS raw CPU | VieNeu baseline |
| --- | --- | --- | --- |
| Test 1 — short sentence, REF-N | identity and word clarity | `outputs/vtts_raw_ref_n_test1_short.wav` | `../personal_voice_phase42a/outputs/vieneu_ref_202a40af97ff_test1_short_0570e460.wav` |
| Test 2 — long sentence, REF-R | pitch contour, semantic stress, comma rhythm, ending | `outputs/vtts_raw_ref_r_test2_long_sentence.wav` | `../personal_voice_phase42a/outputs/vieneu_ref_ec062a6e0b33_test2_long_sentence_9538ffcc.wav` |
| Test 3 — podcast paragraph, REF-E | identity, prosody, transitions, listening fatigue | `outputs/vtts_raw_ref_e_test3_podcast_paragraph.wav` | `outputs/vieneu_baseline_ref_e_test3_podcast_paragraph.wav` |

Please answer in plain language:

1. Which files, if any, sound recognizably like your own voice?
2. On Test 2 and Test 3, which delivery has more natural pacing, stress, and
   sentence endings?
3. Does V-TTS improve enough over VieNeu to justify further **research-only**
   work? If yes, specify the test/reference pair.
4. Does either engine introduce pronunciation, robotic rhythm, or identity
   failures that make it unusable?
5. Is Test 4 warranted for any one reference? If yes, name it; otherwise it
   will not be rendered.

No automated metric can choose a winner. V-TTS has no supported deterministic
seed in this PoC, so a single render is an exploratory sample, not a
deterministic A/B result. V-TTS is CC BY-NC 4.0 and remains ineligible for
commercial production unless licensing is separately resolved.
