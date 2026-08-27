from pathlib import Path
import json
import subprocess


APP = (Path("frontend") / "app.js").read_text(encoding="utf-8")
HTML = (Path("frontend") / "index.html").read_text(encoding="utf-8")
CSS = (Path("frontend") / "styles.css").read_text(encoding="utf-8")


def function_source(name: str, next_name: str) -> str:
    return APP[APP.index(f"function {name}"):APP.index(f"function {next_name}")]


def test_indexeddb_v3_declares_both_additive_stores():
    assert "const IDB_VERSION = 3" in APP
    assert "const IDB_STORE = 'history_audio'" in APP
    assert "const IDB_VOICE_LAB_STORE = 'voice_lab_audio'" in APP
    assert "db.createObjectStore(IDB_STORE)" in APP
    assert "db.createObjectStore(IDB_VOICE_LAB_STORE)" in APP


def test_history_marks_audio_only_after_put_and_get_verification():
    source = APP[APP.index("async function addHistoryEntryWithAudio"):APP.index("async function pruneHistoryAudio")]
    assert "hasAudio: false" in source
    assert source.index("await idbPutAudio(id, blob)") < source.index("await idbGetAudio(id)")
    assert source.index("await idbGetAudio(id)") < source.index("entry.hasAudio = true")
    assert "verified.size !== blob.size" in source


def test_history_replay_is_blob_only():
    source = APP[APP.index("async function playHistoryItem"):APP.index("function markHistoryAudioUnavailable")]
    assert "idbGetAudio(item.id)" in source
    assert "fetch(" not in source
    assert "/api/tts" not in source


def test_invalid_default_voice_is_never_inserted_as_fallback():
    assert '<option value="default">default</option>' not in APP
    assert "resolveValidVoice" in APP
    assert "validVoiceIds.has(candidate)" in APP
    assert "localStorage.getItem(SELECTED_VOICE_STORAGE_KEY)" in APP


def test_backend_detail_and_cache_busted_assets_are_wired():
    assert "readApiErrorDetail(res)" in APP
    assert "userMessageForHttpStatus(err.status, err.detail)" in APP
    assert 'styles.css?v=21.0' in HTML
    assert 'app.js?v=21.0' in HTML


def test_history_actions_have_explicit_active_and_disabled_contrast():
    assert ".historyActions button{" in CSS
    assert ".historyActions button:disabled{" in CSS
    assert "play.className = 'secondary small'" in APP
    assert "regenerate.className = 'secondary small'" in APP


def test_storage_diagnostics_exposes_counts_not_contents():
    source = APP[APP.index("async function aivoiceStorageDiagnostics"):APP.index("window.aivoiceStorageDiagnostics")]
    assert "historyMetadataCount" in source
    assert "historyAudioCount" in source
    assert "voiceLabAudioCount" in source
    assert "frontendBuild:AIVOICE_FRONTEND_BUILD" in source
    assert "origin:window.location.origin" in source
    assert "lastStorageError" in source
    assert "text:" not in source


def test_transaction_is_lexically_scoped_through_all_handlers():
    source = APP[APP.index("function idbRun"):APP.index("function idbPutAudio")]
    catch_index = source.index("}catch(e)")
    assert source.index("const tx = db.transaction") < source.index("tx.oncomplete") < catch_index
    assert source.index("tx.onerror") < catch_index
    assert source.index("tx.onabort") < catch_index
    assert "request.onsuccess" not in source
    assert source.index("const request = fn(store)") < source.index("tx.oncomplete")


def test_transaction_helper_completes_with_mocked_indexeddb_objects():
    source = APP[APP.index("function idbRun"):APP.index("function idbPutAudio")]
    script = f"""
    const recordStorageError = error => error;
    let closed = false;
    let tx;
    const request = {{result: undefined, onerror: null, error: null}};
    const store = {{put(value, key) {{ request.result = `${{key}}:${{value}}`; return request; }}}};
    const db = {{
      transaction(name, mode) {{
        tx = {{objectStore() {{ return store; }}, oncomplete:null, onerror:null, onabort:null, error:null}};
        queueMicrotask(() => tx.oncomplete());
        return tx;
      }},
      close() {{ closed = true; }},
    }};
    const idbOpen = async () => db;
    eval({json.dumps(source)});
    idbRun('readwrite', objectStore => objectStore.put('blob', 'id'), 'history_audio')
      .then(value => {{
        if(value !== 'id:blob' || !closed) process.exit(2);
      }})
      .catch(error => {{ console.error(error); process.exit(3); }});
    """
    completed = subprocess.run(["node", "-e", script], capture_output=True, text=True, timeout=10)
    assert completed.returncode == 0, completed.stderr


def test_voice_lab_persists_then_verifies_before_server_audio_flag():
    helper = APP[APP.index("async function persistVoiceLabAudio"):APP.index("async function pruneVoiceLabAudio")]
    generate = APP[APP.index("async function generateVoiceLabSample"):APP.index("function collectVoiceLabScores")]
    assert helper.index("await idbPutVoiceLabAudio(id, blob)") < helper.index("await idbGetVoiceLabAudio(id)")
    assert generate.index("await persistVoiceLabAudio(record.id, blob)") < generate.index("await syncVoiceLabAudioStatus(record.id, true)")


def test_generated_voice_lab_sample_survives_persistence_failure():
    source = APP[APP.index("async function generateVoiceLabSample"):APP.index("function collectVoiceLabScores")]
    assert source.index("voiceLabAudio.src = voiceLabCurrentAudioUrl") < source.index("await persistVoiceLabAudio(record.id, blob)")
    assert source.index("setVoiceLabCurrentSample({experimentId:null") < source.index("await persistVoiceLabAudio(record.id, blob)")
    assert "Mẫu hiện tại vẫn nghe được." in source


def test_save_voice_all_clone_formats_are_eligible_and_local():
    gate = APP[APP.index("function canSaveVoiceReference"):APP.index("async function handleCloneFile")]
    lab = APP[APP.index("function updateVoiceLabSaveState"):APP.index("function setVoiceLabCurrentSample")]
    assert "CLONE_ACCEPTED_EXTENSIONS.includes(extensionOf(file.name))" in gate
    assert "canSaveVoiceReference(current.reference.file)" in lab
    assert "Hỗ trợ lưu giọng từ WAV, MP3 và M4A" in APP
    assert "File sẽ được xử lý cục bộ trên máy" in APP
    assert "metadata.format !== 'wav'" not in APP


def test_frontend_build_marker_is_21_0():
    assert "const AIVOICE_FRONTEND_BUILD = '21.0'" in APP


def test_voice_lab_save_uses_exact_current_reference_and_refreshes_selection():
    source = APP[APP.index("async function saveVoiceLabVoice"):APP.index("function renderVoiceLabExperiments")]
    assert "current.reference.file" in source
    assert "form.append('ref_audio', current.reference.file, current.reference.file.name)" in source
    assert "loadHealthAndVoices(body.voice?.id || name)" in source
