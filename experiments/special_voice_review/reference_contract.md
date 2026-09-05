# Review Film reference contract

The reference should already sound like the desired stable Vietnamese narrator/reviewer—not an exaggerated emotion performance.

## Recommended recording

- Duration: **8 seconds maximum** for the current AIVoice clone endpoint/ONNX engine; aim for about **6–8 seconds** of usable speech.
- Format: clean mono WAV is preferred. The engine can downmix/re-sample internally, but a clean source avoids unnecessary conversion ambiguity.
- Delivery: medium to medium-fast pace, clear consonants, moderate energy, natural phrase grouping, controlled sentence endings, and one or two short natural pauses.
- Content: two or three complete sentences with an introduction, a descriptive phrase, and a restrained emphasis point.
- Microphone: stable distance, no hard plosives, low room reverb.

## Avoid

- Background music, soundtrack, crowd noise, double voices, heavy compression, clipping, or strong echo.
- Long silence at either edge, whispers, shouting, caricature performance, and extremely fast delivery.
- Movie dialogue, celebrity clips, or recordings without permission.

## Existing local checks

Use AIVoice Reference Quality analysis before a future integration. It already checks duration, sample rate/channels, peak/RMS, noise, silence, clipping and recommendations. For Review Film use, treat a short clip, noise, clipping, excessive silence, or music/reverb heard by the reviewer as a warning. Lightweight DSP cannot reliably detect background music, so this remains a human check.
