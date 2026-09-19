"""Phase 30Q.2 contracts for mixed Audio Studio timelines."""
from pathlib import Path

from backend.app.tts.prosody import parse_prosody_script


STUDIO = Path("frontend/audio-studio.js").read_text(encoding="utf-8")
APP = Path("frontend/app.js").read_text(encoding="utf-8")


def test_legacy_items_migrate_to_explicit_tts_and_audio_is_explicit():
    assert "type:'tts'" in STUDIO
    assert "item?.type==='audio'?'audio':item?.type==='silence'?'silence':'tts'" in STUDIO
    assert "function audioClip()" in STUDIO


def test_studio_uses_shared_planner_and_preserves_editable_script():
    assert "/api/tts/prosody/suggest" in STUDIO
    assert "✨ Đề xuất nhịp đọc" in STUDIO
    assert "tts_script" in STUDIO
    assert "aivoice_audio_studio_handoff" in APP
    assert "tts_script:String(ttsScriptArea?.value || '')" in APP


def test_markers_strip_to_original_spoken_segments():
    script = "Đây là phần đầu. || Đây là phần sau. ||| Sang phần mới."
    assert " ".join(segment.text for segment in parse_prosody_script(script)) == "Đây là phần đầu. Đây là phần sau. Sang phần mới."


def test_audio_clip_storage_playback_and_export_are_timeline_safe():
    assert "accept=\"audio/wav,audio/mpeg,audio/mp4,audio/x-m4a,.wav,.mp3,.m4a\"" in Path("frontend/audio-studio.html").read_text(encoding="utf-8")
    assert "await putAudio(item.audioKey,file)" in STUDIO
    assert "getAudio(item.audioKey||item.id)" in STUDIO
    assert "OfflineAudioContext" in STUDIO
    assert "targetRate=decoded.find(entry=>entry.item.type==='tts')?.buffer.sampleRate" in "".join(STUDIO.split())
    assert "item.type==='audio'?Math.max" in "".join(STUDIO.split())
