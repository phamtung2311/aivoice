"""Phase 25 regression contracts for the browser-local Audio Studio."""

from pathlib import Path


APP = Path("frontend/app.js").read_text(encoding="utf-8")
HTML = Path("frontend/index.html").read_text(encoding="utf-8")
STUDIO_HTML = Path("frontend/audio-studio.html").read_text(encoding="utf-8")
STUDIO_APP = Path("frontend/audio-studio.js").read_text(encoding="utf-8")


def source(name, next_name):
    return APP[APP.index(f"function {name}"):APP.index(f"function {next_name}")]


def test_audio_studio_is_an_additive_workspace_with_local_project_shape():
    assert 'href="audio-studio.html"' in HTML
    assert 'id="audioStudio"' in STUDIO_HTML
    assert "PROJECT_KEY = 'aivoice_audio_studio_project'" in STUDIO_APP
    assert "created_at" in STUDIO_APP and "updated_at" in STUDIO_APP and "segments:" in STUDIO_APP


def test_segment_editor_has_targeted_generate_and_local_blob_storage():
    assert "function addStudioSegment" in APP
    assert "function deleteStudioSegment" in APP
    assert "function duplicateStudioSegment" in APP
    assert "function moveStudioSegment" in APP
    generate = source("generateStudioSegment", "playStudioSegment")
    assert "studioGenerating" in generate
    assert "fetch(API+'/api/tts'" in generate
    assert "idbPutStudioAudio(segment.id,blob)" in generate
    assert "/api/tts/clone" not in generate
    render = source("renderAudioStudio", "addStudioSegment")
    assert "!segment.voice || !validVoiceIds.has(segment.voice)" in render
    assert "segment.voice = resolveValidVoice" in render
    assert "generate.dataset.studioAction='generate'" in render
    assert "function handleStudioSegmentAction" in APP
    assert "studioSegments?.addEventListener('click', handleStudioSegmentAction)" in APP
    assert "segmentsEl.addEventListener('click'" in STUDIO_APP
    assert "function generate(index)" in STUDIO_APP
    assert "studioSaveProject" in STUDIO_HTML
    assert "studioNewProject" in STUDIO_HTML
    assert "item.text=text.value;generate.disabled=generating||!item.text.trim();save()" in STUDIO_APP
    assert "item.text=text.value;save();render()" not in STUDIO_APP
    assert "PROJECTS_KEY = 'aivoice_audio_studio_projects'" in STUDIO_APP
    assert "function openProject" in STUDIO_APP
    assert "async function deleteProject" in STUDIO_APP
    assert "Project cũ vẫn được lưu" in STUDIO_APP
    assert 'id="studioProjectsList"' in STUDIO_HTML
    assert "generate.disabled=generating||!item.text.trim()" in STUDIO_APP
    assert "if(!item.voice&&voices.length){item.voice=voices[0];save()}" in STUDIO_APP
    assert 'audio-studio.js?v=1.0.2' in STUDIO_HTML


def test_play_all_is_sequential_and_export_is_browser_only_wav_merge():
    play_all = source("playAllStudioSegments", "encodeStudioWav")
    assert "await playStudioSegmentAndWait(segment)" in play_all
    export = source("exportAudioStudioWav", "setWorkspaceTab")
    assert "decodeAudioData" in export
    assert "encodeStudioWav" in export
    assert "fetch(" not in export
    assert "buffer.sampleRate!==sampleRate" in export


def test_existing_indexeddb_schema_is_reused_without_history_cleanup_overlap():
    assert "AUDIO_STUDIO_AUDIO_PREFIX = 'studio:'" in APP
    assert "idbPutVoiceLabAudio(studioAudioKey(id), blob)" in APP
    assert "idbClearAllAudio" in APP
