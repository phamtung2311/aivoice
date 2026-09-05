# Phase 42C — Actual Audio Studio web pipeline trace

This document follows the code that is currently executed. It does not describe the intended architecture. The audit was static and ran no TTS inference.

## Concrete call chain

Audio Studio `Generate` click
→ `segmentsEl` delegated click handler calls `generate(index)` (`frontend/audio-studio.js:197`)
→ `generate(index)` constructs the request (`frontend/audio-studio.js:204`)
→ `POST /api/long-audio/jobs`
→ `create_long_audio_job` (`backend/main.py:702`)
→ `normalize_text(original_text)` when smart processing is enabled (`backend/main.py:720-721`)
→ `LongAudioJobs.create` starts a worker
→ `LongAudioJobs._segments` calls `plan_podcast_text(job.text)` for the logical brand ID (`backend/app/tts/long_audio.py:139-150`)
→ one `RenderSegment` is created per production-plan chunk
→ `TTSEngine.generate` is called with source voice `podcast_synthetic_candidate_03` and `speed=1.0` (`backend/app/tts/long_audio.py:253-260`)
→ the generic engine preprocesses/splits/chunks that one semantic chunk with `max_chunk_chars=350` (`backend/app/tts/engine.py:135-137`)
→ `ModelLoader.infer` resolves the persisted source-voice profile and forwards supported inference arguments
→ each chunk WAV is written
→ `_assemble_podcast_to_disk` concatenates chunk WAVs and inserts explicit zero PCM (`backend/app/tts/long_audio.py:166-192`)
→ `_apply_podcast_tempo` runs one final `ffmpeg -af atempo=0.98` over the complete assembly (`backend/app/tts/long_audio.py:194-202`)
→ `GET /api/long-audio/jobs/{job_id}/audio` returns `result.wav`
→ Audio Studio stores the returned blob in IndexedDB and plays it.

## Exact frontend fields and payload

- “Văn bản gốc” edits `item.text`. This is the source that the Podcast Brand Voice backend ultimately uses.
- “TTS Script (có thể chỉnh)” edits `item.settings.tts_script` and may contain `|`, `||`, or `|||`.
- The “Đề xuất nhịp đọc” button is optional. It calls `POST /api/tts/prosody/suggest` and only populates the editable TTS Script field.
- The request payload is formed as:

  `{text:item.text, voice:item.voice, speed:item.speed, ...item.settings, idempotency_key:...}`

- Default advanced values in Audio Studio are `temperature=0.8`, `top_k=25`, `top_p=0.95`, `repetition_penalty=1.2`, `smart_text_processing=true`, an empty `tts_script`, and `prosody_markup=false`.
- If TTS Script is nonempty, it is also sent as `tts_script`; `prosody_markup` is set according to whether a pipe marker is present.
- The frontend does not normalize or chunk the text.
- The selected logical voice ID is `podcast_brand_voice_v1`.

## Brand-specific backend behavior

For `podcast_brand_voice_v1`, the backend deliberately chooses `original_text` even when the payload includes an edited TTS Script. It forces `prosody_markup=false` and does not parse pipe markers. Therefore:

- The original textarea is the actual production input.
- Clicking “Đề xuất nhịp đọc” is not required and its result does not influence brand audio.
- Manual `| / || / |||` markers are not sent to VieNeu and do not change brand lexical or chunk structure.
- Podcast planning is automatic after the request enters the backend.
- The browser-provided advanced sampling values are validated but discarded for the brand job; the server-side frozen values are used.

## The value “1” near the selector

It is `item.speed`, the ordinary Audio Studio speed input. It is sent in the payload, but the brand handler replaces the job speed with `0.98`. Chunk inference is explicitly called with `speed=1.0`, and one final `atempo=0.98` is applied after complete assembly. The visible “1” therefore does not stack another speed transform on this route.

## Normalization passes

On this exact Phase 41G source:

- `normalize_text(source) == source`: true.
- production `preprocess_text(source) == source`: true.
- `TTSEngine.generate` calls `preprocess_text` again for each production chunk.
- VieNeu performs its own text normalization/chunk preparation internally.

The first two local passes are no-ops for this fixture. The important text difference is created by the production planner: it retains terminal periods while the validated Phase 41G plan intentionally removed terminal sentence punctuation from TTS chunk strings.

## Double-chunking finding

There are multiple splitter layers in the call graph, but they do not create additional subchunks for this exact fixture:

- production semantic plan: 54 chunks;
- generic `TTSEngine` recheck with `max_chunk_chars=350`: 54 total chunks;
- every planned chunk stayed exactly one chunk: 54/54;
- maximum production planned length: 219 characters;
- VieNeu `max_chars` is not explicitly forwarded by `TTSEngine`, so its runtime default is 256; a static call to the installed VieNeu 3.3.0 chunk normalizer also returned exactly 54 inner chunks, one for every production chunk, with no split indexes.

Classification E, DOUBLE CHUNKING: **NO for this source**. The redundant generic splitting stage exists and is an equivalence risk for other inputs, but it did not alter these 54 chunk boundaries.
