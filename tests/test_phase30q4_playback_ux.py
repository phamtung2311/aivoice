"""Phase 30Q.4 Studio UX and one-controller playback contracts."""
from pathlib import Path


STUDIO = Path("frontend/audio-studio.js").read_text(encoding="utf-8")
HTML = Path("frontend/audio-studio.html").read_text(encoding="utf-8")


def test_insertion_is_a_quiet_plus_with_one_hidden_vietnamese_menu():
    assert "open.textContent='＋'" in STUDIO
    assert "＋ Thêm điểm chuyển" not in STUDIO
    assert "🎙 Đoạn đọc" in STUDIO
    assert "⏸ Khoảng nghỉ" in STUDIO
    assert "🎵 Âm thanh" in STUDIO
    assert "document.querySelectorAll('.studioInsertionMenu').forEach(candidate=>candidate.hidden=true)" in STUDIO
    assert "if(!event.target.closest('.studioInsertion'))" in STUDIO


def test_playback_has_pause_resume_stop_and_a_single_state_machine():
    assert "const playback = {state:'idle'" in STUDIO
    assert "function stopPlayback()" in STUDIO
    assert "function togglePlaybackPause()" in STUDIO
    assert "playback.audio.currentTime=0" in STUDIO
    assert "playback.queueToken++" in STUDIO
    assert "if(token!==playback.queueToken)return" in STUDIO
    assert 'id="studioPause"' in HTML and 'id="studioStop"' in HTML
    assert "■ Dừng phát" in HTML


def test_primary_project_actions_are_not_duplicated_in_status_panel():
    assert HTML.count('id="studioPlayAll"') == 1
    assert HTML.count('id="studioExport"') == 1
    assert "id=\"studioInspectorPlayAll\"" not in HTML
    assert "id=\"studioInspectorExport\"" not in HTML
