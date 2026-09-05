# Phase 30Q.3 Report — Timeline UX and Between-Segment Transitions

## Audit

Audio Studio already had a compact collapsed state and one-expanded-item
accordion (`expandedSegmentId`). The principal workflow issue in the code was
that items were rendered as a flat list: insertion was append-only from the
toolbar, while move up/down lived inside each expanded card. The editor could
therefore not express an intended transition at the actual boundary between
two items. Audio Clip support also made the flat list harder to scan because
there was no explicit connector or transition item.

The existing project autosave writes metadata after item edits, ordering,
voice/speed/text changes, and valid audio import. It remains in place; the
manual save action is retained as an explicit confirmation. No long-job,
semaphore, prosody, or Podcast Brand implementation was changed.

## Timeline changes

- Added `type: "silence"` with `duration_ms`, default **2.5 seconds**.
- Legacy items without a type remain `tts`; current `audio` and `silence`
  items use explicit metadata.
- Added a compact insertion point before the first item, after the last item,
  and between every pair. Its menu inserts **Nghỉ**, **Âm thanh**, or **TTS**
  at the selected exact array index.
- Added a small Silence card with editable duration, 0.5–3s quick presets,
  and a validated 0.1–30s range.
- Kept TTS and Audio Clip cards compact by default. TTS remains the only
  expanded editor, preserving the existing one-editor accordion behaviour.
- The TTS compact summary now shows a short text preview; Audio keeps its
  filename; Silence is a distinct transition card rather than a content item.

## Rendering semantics

Prosody markers remain inside their TTS segment and are never converted into
timeline Silence. Silence does not use VieNeu, Smart Text, or the prosody
parser. `Play All` waits for actual Silence duration. Export allocates zero
PCM frames at the established TTS target sample rate and concatenates them in
the exact project order with TTS and imported clips.

Timeline duration, ready count, and estimated WAV size now include Silence.
Imported Audio Clip order and resampling behavior from Phase 30Q.2 are
unchanged.

## Verification

Focused suite:

`PYTHONPATH=. .venv/bin/pytest -q tests/test_phase30q3_timeline_transitions.py tests/test_phase30q2_audio_studio_timeline.py tests/test_phase30q1_long_audio.py tests/test_phase25_audio_studio.py tests/test_phase30o_prosody.py tests/test_phase30p2_context_planner.py tests/test_phase30q_podcast_beta.py`

Result: **27 passed**. JavaScript syntax, Python compilation, and
`git diff --check` passed.

## Manual validation

1. Restart the backend and hard-refresh Audio Studio.
2. Create or open a project with two TTS items.
3. At their visible boundary choose **＋ Thêm điểm chuyển → ⏸ Nghỉ**; confirm
   that a 2.5s transition appears exactly between them.
4. At a boundary choose **🎵 Âm thanh**, select a short WAV/MP3/M4A, then
   confirm its exact placement and Play All order.
5. Export WAV and verify the sequence: TTS → silence/clip → TTS.
