# Phase 30Q.2 Report — Audio Studio Prosody and Interlude Timeline

## Scope

This phase extends the existing Audio Studio and preserves the Phase 30Q.1
long-job pipeline unchanged. No Podcast Brand Beta, M-A keeper artifact,
speaker embedding, reference codes, sampling defaults, or prosody-planner
decision rules were changed.

## Audit and handoff finding

Phase 30Q.1's main-page handoff already wrote `original text`, `voice`,
`speed`, and `tts_script` to session storage. Audio Studio did restore the
script, including markers. The practical gap was presentation: the Studio
editor made the script look like an unlabeled optional field, and it had no
segment-level planner action. It now visibly presents **Văn bản gốc** and
**TTS Script (có thể chỉnh)**, and exposes **✨ Đề xuất nhịp đọc**.

The action calls the existing `/api/tts/prosody/suggest` endpoint. It asks
before replacing a non-empty edited script. The script is then sent to the
unchanged long-job pipeline, whose `podcast_prosody_v1` parser removes all
control markers before VieNeu receives clean text.

## Timeline model and migration

Every current timeline item has explicit `type: "tts"` or `type: "audio"`.
The project migration treats missing legacy type as `tts`, preserving old
projects and their existing metadata. Audio Clip metadata holds filename,
duration, local `audioKey`, ready state, and volume. Binary data remains in
the existing IndexedDB store, not localStorage.

## Audio Clip workflow

Audio Studio now has **＋ Audio Clip** and accepts WAV, MP3, and M4A. The
browser decodes the file before adding it; a decode failure shows `Không đọc
được tệp âm thanh này.` and leaves the project unchanged. Clips are ready
immediately and never call TTSEngine, VieNeu, Smart Text, or prosody parsing.

Timeline ordering, play-all, move up/down, duplication, and export all include
both item types. Duplicated clips share the local blob key instead of copying
the audio. Deleting metadata deliberately does not aggressively delete blobs,
because the blob can be shared by a duplicate/project copy.

Export decodes all timeline items, uses the first TTS item's sample rate as
the production target when available, resamples imported clips with
`OfflineAudioContext`, applies Audio Clip-only volume, then writes one PCM WAV
in exact timeline order. This avoids concatenating incompatible WAV files; a
44.1 kHz clip is conformed to the TTS timeline rate without changing the TTS
audio. Fade and trim remain intentionally deferred rather than adding a DAW
surface.

## Pause guidance

Explicit `|||` remains untouched when followed by an Audio Clip. It can make a
longer transition together with the clip; the user retains editorial control.

## Verification

Focused checks passed:

`PYTHONPATH=. .venv/bin/pytest -q tests/test_phase30q2_audio_studio_timeline.py tests/test_phase30q1_long_audio.py tests/test_phase25_audio_studio.py tests/test_phase30o_prosody.py tests/test_phase30p2_context_planner.py tests/test_phase30q_podcast_beta.py`

Result: **24 passed**. JavaScript syntax, Python compilation, and
`git diff --check` also passed.

## Manual validation

1. Restart the backend and hard-refresh both pages.
2. On main TTS, make a suggested script, then choose **🎬 Tạo Audio dài**.
3. Confirm Studio shows the original text and the exact `|`, `||`, `|||` TTS
   Script; generate and listen to the pauses.
4. Add a 2–3 second WAV/MP3/M4A clip between two ready TTS items, then use
   Play All and Export WAV to verify the order and transition.
