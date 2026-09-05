# Phase 30Q.4 Report — Simplified Timeline UX and Playback Controls

## Audit

The existing Studio used independent `Audio()` instances for individual play
and Play All. They had no shared state, no pause/stop UI, and no way for Stop
to prevent the remaining project queue from continuing. The visual insertion
control also exposed the implementation concept “Thêm điểm chuyển” at every
boundary, despite its menu already being hidden by default.

The toolbar duplicated Play All and Export in the right status panel, and
exposed multiple technical creation controls. This left the compact timeline
without a clear primary interaction model.

## UX changes

- Boundary insertion is now only a subtle **＋**. Its hidden contextual menu
  uses **Đoạn đọc**, **Khoảng nghỉ**, and **Âm thanh**. Opening one closes all
  other insertion menus; clicking elsewhere closes it.
- The top toolbar uses one authoritative set of project controls: save, append
  a spoken segment, Play All, playback pause/stop when active, generation
  cancellation only during generation, and Export WAV.
- The right panel is status-only; duplicated playback/export buttons are gone.
- Timeline summaries retain a short original-text preview for speech and keep
  audio/silence compact. Silence remains a small transition line.
- Save feedback is a quiet `✓ Đã lưu` rather than a timestamp-heavy status.

## Playback controller

Audio Studio now has one `playback` controller state for individual and project
playback. It tracks mode, idle/playing/paused state, active item/audio, current
object URL, queue token, and Silence timer.

- **Tạm dừng** pauses the active browser audio; **Tiếp tục** resumes it.
- **Dừng phát** pauses, resets the audio to zero, clears timers/object URLs,
  invalidates the queue token, and returns controls to idle.
- A stopped Play All queue cannot start a later TTS/Audio item.
- The compact active card changes its Listen control to a pause/resume affordance.
- The active card is highlighted and displays compact elapsed/total playback
  progress while browser audio is playing.

Generation cancellation remains a separate `✕ Hủy tạo` control and only appears
while the long-form job is active.

## Verification

`PYTHONPATH=. .venv/bin/pytest -q tests/test_phase30q4_playback_ux.py tests/test_phase30q3_timeline_transitions.py tests/test_phase30q2_audio_studio_timeline.py tests/test_phase30q1_long_audio.py tests/test_phase25_audio_studio.py tests/test_phase30o_prosody.py tests/test_phase30p2_context_planner.py tests/test_phase30q_podcast_beta.py`

Result: **30 passed**. JavaScript syntax, Python compilation, and
`git diff --check` passed.

## Manual validation

1. Open a project with two ready items; confirm each boundary shows only `＋`.
2. Click it and confirm the Vietnamese menu; click outside and confirm it closes.
3. Start **Phát tất cả**, pause, resume, then press **Dừng phát** while an item
   is playing. Confirm no later item begins.
4. Start an individual item, then use its compact control to pause/resume and
   the top-level **Dừng phát** to reset it.
