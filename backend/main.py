from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, Request, Body
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.background import BackgroundTask
from typing import Optional
from pathlib import Path
import tempfile
import os
import secrets

from backend.app.schemas import (
    TEXT_MAX_LENGTH, CloneForm, LongAudioRequest, NLPPreviewRequest,
    PersonalVoiceCandidateRequest, PersonalVoiceSegmentRequest,
    ProsodySuggestionRequest, TTSRequest,
)
from backend.app.reference_audio import _prepare_reference_wav
from backend.app.validation import validate_sampling_param as _validate_sampling_param
from backend.app.tts.engine import TTSEngine
from backend.app.tts.prosody import parse_prosody_script, transform_prosody_script
from backend.app.tts.prosody_suggest import plan_context_aware_prosody
from backend.app.tts.long_audio import LongAudioJobs
from backend.app.tts import voice_store
from backend.app.tts.reference_quality import analyze_clip
from backend.app.tts.nlp import normalize_text
from backend.app.tts.podcast_brand import (
    PODCAST_BRAND_VOICE_ID,
    PODCAST_FINAL_TEMPO,
    load_canonical_candidate_03,
)
from backend.app.tts.special_voices import SPECIAL_VOICES
from backend.app.tts.podcast_voices import PODCAST_VOICES, resolve_podcast_voice
from backend.app.runtime_metadata import get_runtime_metadata
from backend.app import voice_lab
from backend.app.personal_voice_lab import (
    ACCEPTED_EXTENSIONS as PERSONAL_VOICE_EXTENSIONS,
    SOURCE_MAX_BYTES as PERSONAL_VOICE_MAX_BYTES,
    PersonalVoiceStore,
    engine_catalog as personal_voice_engine_catalog,
)
import threading
import time
import asyncio
import logging

logger = logging.getLogger(__name__)

APP_VERSION = "1.0.0"
BUILD_DATE = "2026-08-27"

# global bounded semaphore to limit concurrent inferences
# default from env or 1
try:
    _max_concurrency = int(os.environ.get("TTS_MAX_CONCURRENCY", "1"))
    if _max_concurrency < 1:
        _max_concurrency = 1
except Exception:
    _max_concurrency = 1

# Bounded semaphore shared across requests in this process
_TTS_SEMAPHORE = threading.BoundedSemaphore(value=_max_concurrency)

# Guards serialization of the local voice-profile store (small, personal data).
_LOCK = threading.Lock()

# maximum allowed bytes for reference audio upload (≈5MB)
REF_MAX_BYTES = int(os.environ.get("REF_MAX_BYTES", str(5 * 1024 * 1024)))
REF_MAX_SECONDS = 8.0

# Reference audio formats accepted by the clone pipeline.
CLONE_AUDIO_EXTENSIONS = ('.wav', '.mp3', '.m4a')


# create app
app = FastAPI(title="Local TTS API")

# CORS - allow only local frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# singleton engine
_ENGINE = TTSEngine()
_LONG_AUDIO_JOBS = LongAudioJobs(_ENGINE, _TTS_SEMAPHORE)
_LONG_AUDIO_IDEMPOTENCY: dict[str, str] = {}
_PERSONAL_VOICE_ROOT = Path(os.environ.get(
    "PERSONAL_VOICE_ROOT", "experiments/personal_voice_phase42a"
))
_PERSONAL_VOICE_STORE = PersonalVoiceStore(_PERSONAL_VOICE_ROOT)


def get_engine() -> TTSEngine:
    return _ENGINE


def _podcast_brand_available(engine: TTSEngine) -> bool:
    """Expose the logical profile only when canonical Candidate 03 verifies."""
    try:
        load_canonical_candidate_03()
        return True
    except RuntimeError:
        return False


def _valid_voice_ids(engine: TTSEngine) -> set[str]:
    result = set(engine.get_voices() or ["default"])
    if _podcast_brand_available(engine):
        result.add(PODCAST_BRAND_VOICE_ID)
    result.update(PODCAST_VOICES)
    return result


@app.get("/api/health")
def health(engine: TTSEngine = Depends(get_engine)):
    # prefer the actual loaded model name if available
    model = getattr(getattr(engine, "_model", None), "model_name", None) or engine.model_name or "unknown"
    runtime = get_runtime_metadata(engine)
    return {
        "status": "ok",
        "version": APP_VERSION,
        "build_date": BUILD_DATE,
        "engine": "local",
        "model": model,
        "max_text_length": TEXT_MAX_LENGTH,
        **runtime,
    }


@app.get("/api/voices")
def voices(engine: TTSEngine = Depends(get_engine)):
    # Defensive: some engines/tests expose only get_voices(); use fallbacks.
    preset_names = list(getattr(engine, "get_preset_names", lambda: None)() or []) or list(engine.get_voices() or ["default"])
    saved_names = list(getattr(engine, "get_user_voice_names", lambda: [])() or [])
    special_names = list(getattr(engine, "get_special_voice_names", lambda: [])() or [])

    # try to enrich with local voices.json metadata if available
    out = []
    try:
        import json
        import pathlib
        local_path = pathlib.Path("models") / next(p for p in pathlib.Path("models").glob("**/snapshots/*/voices.json"))
        data = json.loads(local_path.read_text(encoding="utf-8"))
        presets = data.get("presets", {})
    except Exception:
        presets = {}

    for v in preset_names:
        meta = presets.get(v, {}) if isinstance(presets, dict) else {}
        item = {"id": v, "name": v, "type": "preset"}
        if meta:
            if meta.get("description"):
                item["description"] = meta.get("description")
            if "podcast" in meta:
                try:
                    item["podcast"] = bool(str(meta.get("podcast")).lower() == "true")
                except Exception:
                    pass
        out.append(item)

    for name in saved_names:
        out.append({"id": name, "name": name, "type": "saved"})

    for name in special_names:
        meta = dict(getattr(engine, "get_voice_metadata", lambda _name: {})(name) or {})
        out.append({
            "id": name,
            "name": meta.get("display_name") or name,
            "type": "special",
            "category": meta.get("category") or "Special Voice",
            "status": meta.get("status", ""),
            "is_final_brand_voice": bool(meta.get("is_final_brand_voice", False)),
            "description": meta.get("description", ""),
            "special_type": meta.get("special_type", ""),
            "recommended_use": meta.get("recommended_use", ""),
        })
    for voice_id, meta in PODCAST_VOICES.items():
        out.append({"id": voice_id, "name": meta["display_name"], "type": "special", "category": "Giọng Podcast", "status": "PRODUCTION PODCAST VOICE", "is_final_brand_voice": False, "description": f"AIVoice Podcast Voice Set v1; frozen Phase 43A Voice {meta['phase43a_voice']} identity."})

    # The production profile is a logical rendering stack, not a duplicated
    # speaker record. Expose it when frozen Candidate 03 is available locally.
    if _podcast_brand_available(engine) and not any(item["id"] == PODCAST_BRAND_VOICE_ID for item in out):
        meta = SPECIAL_VOICES[PODCAST_BRAND_VOICE_ID]
        out.append({
            "id": PODCAST_BRAND_VOICE_ID,
            "name": meta["display_name"],
            "type": "special",
            "category": meta["category"],
            "status": meta["status"],
            "is_final_brand_voice": False,
            "description": meta["description"],
            "special_type": meta["special_type"],
            "recommended_use": meta["recommended_use"],
            "speaker": meta["speaker"],
            "prosody_profile": meta["prosody_profile"],
            "tempo": meta["tempo"],
            "pause_profile": meta["pause_profile"],
            "pipeline_version": meta["pipeline_version"],
        })

    return {"voices": out}


@app.post("/api/nlp/preview")
def nlp_preview(req: NLPPreviewRequest):
    """Local, deterministic preview of the optional TTS text processing."""
    return {"original": req.text, "processed": normalize_text(req.text, enabled=req.smart_text_processing)}


@app.get("/api/voice-lab/corpus")
def voice_lab_corpus():
    return voice_lab.load_corpus()


@app.get("/api/voice-lab/quality-corpus")
def voice_lab_quality_corpus():
    return voice_lab.load_quality_corpus()


def _personal_voice_test_set() -> dict:
    path = _PERSONAL_VOICE_ROOT / "test_set.json"
    if not path.exists():
        raise HTTPException(status_code=500, detail="Phase42A controlled test set is missing")
    import json
    return json.loads(path.read_text(encoding="utf-8"))


@app.get("/api/personal-voice/config")
def personal_voice_config():
    return {
        "accepted_extensions": sorted(PERSONAL_VOICE_EXTENSIONS),
        "source_duration_seconds": {"recommended_min": 30, "maximum": 180},
        "source_max_bytes": PERSONAL_VOICE_MAX_BYTES,
        "reference_duration_seconds": {"minimum": 3, "maximum": 8},
        "engines": personal_voice_engine_catalog(),
        "tests": _personal_voice_test_set()["tests"],
        "privacy": "All recordings and derived files stay on this machine.",
    }


@app.post("/api/personal-voice/sources", status_code=201)
async def upload_personal_voice_source(recording: UploadFile = File(...)):
    filename = os.path.basename(recording.filename or "recording")
    extension = os.path.splitext(filename)[1].lower()
    if extension not in PERSONAL_VOICE_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Chỉ nhận M4A, WAV, MP3 hoặc AAC")
    payload = await recording.read(PERSONAL_VOICE_MAX_BYTES + 1)
    try:
        return _PERSONAL_VOICE_STORE.save_source(filename, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@app.get("/api/personal-voice/sources/{source_id}")
def get_personal_voice_source(source_id: str):
    try:
        return _PERSONAL_VOICE_STORE.source_metadata(source_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Không tìm thấy bản thu")


@app.get("/api/personal-voice/sources/{source_id}/audio")
def get_personal_voice_audio(source_id: str, kind: str = "original", segment_id: Optional[str] = None):
    try:
        path = _PERSONAL_VOICE_STORE.audio_path(source_id, kind, segment_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Không tìm thấy audio")
    media_types = {".wav": "audio/wav", ".mp3": "audio/mpeg", ".m4a": "audio/mp4", ".aac": "audio/aac"}
    media_type = media_types.get(path.suffix.lower(), "application/octet-stream")
    return FileResponse(path, media_type=media_type, filename=path.name)


@app.post("/api/personal-voice/sources/{source_id}/segments", status_code=201)
def create_personal_voice_segment(source_id: str, request: PersonalVoiceSegmentRequest):
    try:
        return _PERSONAL_VOICE_STORE.create_segment(
            source_id, request.start_seconds, request.end_seconds,
            request.label, request.transcript,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Không tìm thấy bản thu")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/personal-voice/candidates", status_code=201)
def create_personal_voice_candidate(
    request: PersonalVoiceCandidateRequest,
    engine: TTSEngine = Depends(get_engine),
):
    """Generate one controlled VieNeu baseline from a stored 3–8 s segment.

    This route is never called automatically. Each click makes one explicitly
    named artifact so results are not overwritten or confused across references.
    """
    if request.engine_id != "vieneu_3_3_0":
        raise HTTPException(status_code=409, detail="Engine này chưa khả dụng trên máy")
    tests = {item["id"]: item for item in _personal_voice_test_set()["tests"]}
    if request.test_id not in tests:
        raise HTTPException(status_code=400, detail="Controlled test id không hợp lệ")
    try:
        reference = _PERSONAL_VOICE_STORE.audio_path(
            request.source_id, "segment", request.segment_id
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Không tìm thấy reference segment")
    output_id = f"vieneu_{request.segment_id}_{request.test_id}_{secrets.token_hex(4)}"
    output = _PERSONAL_VOICE_ROOT / "outputs" / f"{output_id}.wav"
    _TTS_SEMAPHORE.acquire()
    try:
        engine.generate(
            tests[request.test_id]["text"], speed=1.0,
            out_path=str(output), ref_audio=str(reference),
        )
    except Exception as exc:
        output.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Tạo candidate thất bại: {exc}")
    finally:
        _TTS_SEMAPHORE.release()
    import hashlib
    audio_hash = hashlib.sha256(output.read_bytes()).hexdigest()
    info = __import__("soundfile").info(str(output))
    manifest = {
        "id": output_id,
        "engine": request.engine_id,
        "source_id": request.source_id,
        "segment_id": request.segment_id,
        "test_id": request.test_id,
        "path": str(output),
        "sha256": audio_hash,
        "duration_seconds": round(info.frames / float(info.samplerate), 6),
        "sample_rate": info.samplerate,
        "tts_rerendered": True,
        "historical_podcast_stack_modified": False,
    }
    manifest_path = _PERSONAL_VOICE_ROOT / "metadata" / f"{output_id}.json"
    manifest_path.write_text(__import__("json").dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


@app.get("/api/personal-voice/candidates/{candidate_id}/audio")
def get_personal_voice_candidate_audio(candidate_id: str):
    if not candidate_id.startswith("vieneu_") or not candidate_id.replace("_", "").isalnum():
        raise HTTPException(status_code=404, detail="Không tìm thấy candidate")
    manifest_path = _PERSONAL_VOICE_ROOT / "metadata" / f"{candidate_id}.json"
    if not manifest_path.exists():
        raise HTTPException(status_code=404, detail="Không tìm thấy candidate")
    import json
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    output = Path(manifest["path"])
    if not output.exists() or output.parent.resolve() != (_PERSONAL_VOICE_ROOT / "outputs").resolve():
        raise HTTPException(status_code=404, detail="Không tìm thấy candidate audio")
    return FileResponse(output, media_type="audio/wav", filename=output.name)


@app.post("/api/voice-lab/references/analyze")
async def analyze_voice_lab_reference(ref_audio: UploadFile = File(...), reference_id: str = Form("")):
    """Analyze one uploaded reference and retain only its quality metadata."""
    filename = os.path.basename(ref_audio.filename or "reference")
    source_ext = os.path.splitext(filename)[1].lower()
    if source_ext not in CLONE_AUDIO_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Tệp tham chiếu phải là WAV, MP3 hoặc M4A")
    audio_bytes = await ref_audio.read(REF_MAX_BYTES + 1)
    if not audio_bytes or len(audio_bytes) > REF_MAX_BYTES:
        raise HTTPException(status_code=400, detail="Reference phải có dữ liệu và không vượt quá 5 MB")
    try:
        analysis = analyze_clip(audio_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    report = analysis.to_dict()
    metrics = report["metrics"]
    result = {
        "duration": metrics["duration_seconds"],
        "sample_rate": metrics["sample_rate"],
        "channels": metrics["channels"],
        "peak": metrics["peak"],
        "rms": metrics["rms"],
        "noise": metrics["noise_estimate"],
        "silence_ratio": metrics["silence_ratio"],
        "leading_silence": metrics["leading_silence"],
        "ending_silence": metrics["ending_silence"],
        "quality_score": analysis.score,
        "strengths": report["strengths"],
        "weaknesses": report["weaknesses"],
        "tips": ["Ưu tiên phòng yên tĩnh, nói tự nhiên và giữ micro ổn định."] if report["recommended"] else ["Thu lại ở nơi yên tĩnh, tránh clipping và giữ đoạn nói 5–8 giây."],
        "recommended": report["recommended"],
        "bars": report["bars"],
    }
    history_id = reference_id.strip() or f"ref_{secrets.token_hex(6)}"
    entry = voice_lab.ReferenceHistoryEntry(
        id=history_id,
        filename=filename,
        duration=result["duration"],
        score=result["quality_score"],
        sample_rate=result["sample_rate"],
        quality_report=result,
    )
    voice_lab.save_reference_analysis(entry)
    return result


@app.get("/api/voice-lab/references/history")
def voice_lab_reference_history():
    return {"references": voice_lab.load_reference_history()}


@app.patch("/api/voice-lab/references/{reference_id}/preferred")
def set_voice_lab_reference_preferred(reference_id: str):
    try:
        return voice_lab.set_reference_preferred(reference_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Voice Lab reference not found")


@app.get("/api/voice-lab/experiments")
def voice_lab_experiments():
    return {"experiments": voice_lab.load_experiments()}


@app.post("/api/voice-lab/experiments", status_code=201)
def create_voice_lab_experiment(
    payload: voice_lab.ExperimentCreate,
    engine: TTSEngine = Depends(get_engine),
):
    try:
        return voice_lab.create_experiment(payload, get_runtime_metadata(engine))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.patch("/api/voice-lab/experiments/{experiment_id}")
def evaluate_voice_lab_experiment(
    experiment_id: str,
    payload: voice_lab.ExperimentEvaluation,
):
    try:
        return voice_lab.evaluate_experiment(experiment_id, payload)
    except KeyError:
        raise HTTPException(status_code=404, detail="Voice Lab experiment not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.patch("/api/voice-lab/experiments/{experiment_id}/audio")
def set_voice_lab_experiment_audio(experiment_id: str, has_audio: bool = Body(..., embed=True)):
    try:
        return voice_lab.set_experiment_audio_status(experiment_id, has_audio)
    except KeyError:
        raise HTTPException(status_code=404, detail="Voice Lab experiment not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/api/voice-lab/branded-voice")
def voice_lab_branded_voice():
    return {"manifest": voice_lab.load_branded_manifest()}


@app.get("/api/voice-lab/temperature-candidates")
def voice_lab_temperature_candidates():
    return {"candidates": voice_lab.load_temperature_candidates()}


@app.post("/api/voice-lab/temperature-candidates", status_code=201)
def save_voice_lab_temperature_candidate(
    payload: voice_lab.TemperatureCandidateSelection,
    user_confirmed: bool = Body(False, embed=True),
    engine: TTSEngine = Depends(get_engine),
):
    if payload.saved_voice_id not in set(engine.get_user_voice_names()):
        raise HTTPException(status_code=400, detail="Temperature configuration requires an existing saved voice")
    try:
        selection = payload.model_copy(update={
            "evaluation_summary": voice_lab.temperature_summary(payload.saved_voice_id, payload.temperature),
        })
        return voice_lab.save_temperature_candidate(selection, user_confirmed=user_confirmed)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


def _engine_ref_max_seconds(engine) -> float:
    """Best-effort reference clip limit from the loaded engine (falls back 10s)."""
    try:
        import inspect as _inspect
        v = getattr(engine, "_model", None)
        if v is not None:
            underlying = getattr(v, "_v", None)
            eng = getattr(underlying, "engine", None)
            if eng is not None and hasattr(eng, "prepare_reference"):
                sig = _inspect.signature(eng.prepare_reference)
                if "max_seconds" in sig.parameters and sig.parameters["max_seconds"].default is not _inspect._empty:
                    return float(sig.parameters["max_seconds"].default)
    except Exception:
        pass
    return 10.0


@app.post("/api/voices/save")
async def save_voice(
    name: str = Form(None),
    description: str = Form(""),
    ref_audio: UploadFile = File(None),
    engine: TTSEngine = Depends(get_engine),
):
    try:
        name = voice_store.validate_voice_name(name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if ref_audio is None:
        raise HTTPException(status_code=400, detail="Thiếu tệp âm thanh tham chiếu")
    original_name = ref_audio.filename or ""
    source_ext = os.path.splitext(original_name)[1].lower()
    if source_ext not in CLONE_AUDIO_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Tệp tham chiếu phải là WAV, MP3 hoặc M4A")

    # Reject duplicates before reading/decoding an upload. The check is repeated
    # under _LOCK immediately before enrollment to cover races.
    if name in set(engine.get_voices() or []):
        raise HTTPException(status_code=409, detail="Giọng này đã tồn tại")

    tmp_ref = tempfile.NamedTemporaryFile(delete=False, prefix="save_voice_ref_", suffix=source_ext)
    tmp_ref_path = tmp_ref.name
    converted_tmp_path = None
    try:
        data = await ref_audio.read()
        if len(data) > REF_MAX_BYTES:
            raise HTTPException(status_code=413, detail="Tệp tham chiếu quá lớn")
        if not data:
            raise HTTPException(status_code=400, detail="Tệp âm thanh rỗng hoặc không hợp lệ")
        tmp_ref.write(data)
        tmp_ref.close()

        try:
            ref_wav_path, converted_tmp_path = _prepare_reference_wav(tmp_ref_path, source_ext)
        except RuntimeError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        except Exception:
            raise HTTPException(status_code=400, detail="Tệp âm thanh không hợp lệ, bị hỏng hoặc không thể giải mã")

        try:
            import soundfile as sf
            info = sf.info(ref_wav_path)
            duration = info.frames / float(info.samplerate)
        except Exception:
            raise HTTPException(status_code=400, detail="Tệp âm thanh không hợp lệ hoặc không thể đọc")

        allowed_max = min(REF_MAX_SECONDS, _engine_ref_max_seconds(engine))
        if duration <= 0:
            raise HTTPException(status_code=400, detail="Tệp âm thanh rỗng hoặc không hợp lệ")
        if duration > allowed_max:
            raise HTTPException(status_code=413, detail=f"Tệp tham chiếu quá dài (tối đa {allowed_max:.0f}s)")

        # Encodes the reference once (native add_voice) + persists a profile.
        # Reuse the inference semaphore since encoding is expensive on CPU.
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, _TTS_SEMAPHORE.acquire)
        try:
            with _LOCK:
                if name in set(engine.get_voices() or []):
                    raise HTTPException(status_code=409, detail="Giọng này đã tồn tại")
                try:
                    engine.add_saved_voice(name, ref_wav_path, description=str(description or "")[:200])
                except TypeError:
                    # Keep lightweight legacy/dummy engines compatible with the
                    # existing two-argument enrollment contract.
                    engine.add_saved_voice(name, ref_wav_path)
        finally:
            try:
                _TTS_SEMAPHORE.release()
            except Exception:
                pass
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Không thể lưu giọng: {e}")
    finally:
        try:
            tmp_ref.close()
        except Exception:
            pass
        for path in (tmp_ref_path, converted_tmp_path):
            if path:
                try:
                    os.remove(path)
                except Exception:
                    pass

    return {"ok": True, "voice": {"id": name, "name": name, "type": "saved"}}


@app.delete("/api/voices/{voice_id}")
def delete_voice(voice_id: str, engine: TTSEngine = Depends(get_engine)):
    if not hasattr(engine, "delete_saved_voice"):
        raise HTTPException(status_code=501, detail="Voice profile không được hỗ trợ")
    try:
        voice_store.validate_voice_name(voice_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Giọng không tồn tại")
    try:
        removed = engine.delete_saved_voice(voice_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Không thể xóa giọng: {e}")
    if not removed:
        raise HTTPException(status_code=403, detail="Không thể xóa giọng mặc định có sẵn")
    return {"ok": True}


def _remove_file(path: str):
    try:
        os.remove(path)
    except Exception:
        pass


@app.post("/api/tts")
def tts(req: TTSRequest, engine: TTSEngine = Depends(get_engine)):
    original_text = req.text or ""
    is_podcast_brand = req.voice == PODCAST_BRAND_VOICE_ID
    is_experimental_podcast = req.voice in PODCAST_VOICES
    # A supplied script is the user-approved synthesis source. Markup is an
    # additional opt-in interpretation layer, not a requirement for editing.
    text = original_text if (is_podcast_brand or is_experimental_podcast) else (req.tts_script if req.tts_script is not None else original_text)
    if not text or not text.strip():
        raise HTTPException(status_code=400, detail="Text must not be empty")
    if len(original_text) > TEXT_MAX_LENGTH or len(text) > TEXT_MAX_LENGTH:
        raise HTTPException(status_code=413, detail="Text too long")
    if req.prosody_markup and not is_podcast_brand:
        try:
            # Validate before model work; the parser also prevents markers from
            # entering the model path.
            parse_prosody_script(text)
            # Smart Text Processing runs only on clean parsed segments. This
            # preserves user marker boundaries while retaining the established
            # local date/number/money normalization for marked scripts.
            if req.smart_text_processing:
                text = transform_prosody_script(text, normalize_text)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
    elif req.smart_text_processing:
        text = normalize_text(text)
        if len(text) > TEXT_MAX_LENGTH:
            raise HTTPException(status_code=413, detail="Processed text too long")

    if req.voice and req.voice not in _valid_voice_ids(engine):
        raise HTTPException(status_code=400, detail="Invalid voice")

    # Phase 22.1: optional Voice Lab diagnostic. When absent, the generate call
    # below is byte-identical to the pre-22.1 production call.
    engine_kwargs: dict = {}
    if is_experimental_podcast:
        try: engine_kwargs["voice_profile"] = resolve_podcast_voice(req.voice)
        except (ValueError, RuntimeError) as exc: raise HTTPException(status_code=400, detail=str(exc))
    if req.conditioning_mode is not None:
        if req.conditioning_mode != "identity_only":
            raise HTTPException(status_code=422, detail="conditioning_mode must be 'identity_only'")
        if not req.voice or req.voice not in (engine.get_user_voice_names() or []):
            raise HTTPException(status_code=400, detail="conditioning_mode requires a saved (cloned) voice")
        engine_kwargs["use_ref_codes"] = False

    # validate sampling params (optional)
    temperature = _validate_sampling_param("temperature", req.temperature, 0.1, 1.5)
    top_k = _validate_sampling_param("top_k", req.top_k, 1, 100, integer=True)
    top_p = _validate_sampling_param("top_p", req.top_p, 0.5, 1.0)
    repetition_penalty = _validate_sampling_param("repetition_penalty", req.repetition_penalty, 1.0, 2.0)

    if is_podcast_brand:
        # Use the same durable, sequential, disk-backed path as Audio Studio.
        # Profile controls are frozen; user speed/markup/sampling do not alter it.
        job = _LONG_AUDIO_JOBS.create(
            text=text,
            voice=PODCAST_BRAND_VOICE_ID,
            speed=PODCAST_FINAL_TEMPO,
            prosody_markup=False,
            options={},
        )
        while job.state not in {"COMPLETED", "FAILED", "CANCELLED"}:
            time.sleep(0.05)
        if job.state != "COMPLETED" or not job.output_path or not job.output_path.exists():
            raise HTTPException(status_code=500, detail=f"Podcast generation failed: {job.error or job.state}")
        return FileResponse(
            str(job.output_path), media_type="audio/wav", filename=f"{job.id}.wav",
            headers={"X-AIVoice-Job-ID": job.id, "X-AIVoice-Pipeline": PODCAST_BRAND_VOICE_ID},
        )

    # create temp file for output
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    tmp_path = tmp.name
    tmp.close()

    # acquire semaphore (blocking). measure wait time for logging.
    wait_start = time.monotonic()
    _TTS_SEMAPHORE.acquire()
    wait_elapsed = time.monotonic() - wait_start
    if wait_elapsed > 0.0:
        logger.info("inference slot waited %.3fs", wait_elapsed)
    try:
        # let engine write to our temp path; forward sampling params only when provided
        generate_kwargs = dict(voice=req.voice, speed=req.speed, out_path=tmp_path,
                               temperature=temperature, top_k=top_k, top_p=top_p,
                               repetition_penalty=repetition_penalty, **engine_kwargs)
        if req.prosody_markup:
            engine.generate_prosody(text, **generate_kwargs)
        else:
            engine.generate(text, **generate_kwargs)
    except Exception as e:
        _remove_file(tmp_path)
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {e}")
    finally:
        try:
            _TTS_SEMAPHORE.release()
            logger.info("inference slot released")
        except Exception:
            pass

    return FileResponse(tmp_path, media_type="audio/wav", filename=os.path.basename(tmp_path), background=BackgroundTask(_remove_file, tmp_path))


@app.post("/api/tts/prosody/suggest")
def tts_prosody_suggest(req: ProsodySuggestionRequest):
    try:
        proposal = plan_context_aware_prosody(req.text)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"prosody_version": "podcast_prosody_v1", **proposal}


@app.post("/api/long-audio/jobs")
def create_long_audio_job(req: LongAudioRequest, engine: TTSEngine = Depends(get_engine)):
    """Start a sequential Audio Studio job; never run markup through VieNeu."""
    original_text = req.text or ""
    is_podcast_brand = req.voice == PODCAST_BRAND_VOICE_ID
    # Audio Studio historically serializes an empty string for an untouched
    # optional script. Treat it as absent rather than replacing real text.
    text = original_text if (is_podcast_brand or req.voice in PODCAST_VOICES) else (req.tts_script if req.tts_script and req.tts_script.strip() else original_text)
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text must not be empty")
    if len(original_text) > TEXT_MAX_LENGTH or len(text) > TEXT_MAX_LENGTH:
        raise HTTPException(status_code=413, detail="Text too long")
    if req.voice and req.voice not in _valid_voice_ids(engine):
        raise HTTPException(status_code=400, detail="Invalid voice")
    if req.prosody_markup and not is_podcast_brand:
        try:
            parse_prosody_script(text)
            if req.smart_text_processing:
                text = transform_prosody_script(text, normalize_text)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))
    elif req.smart_text_processing:
        text = normalize_text(text)
    if len(text) > TEXT_MAX_LENGTH:
        raise HTTPException(status_code=413, detail="Processed text too long")
    options = {
        "temperature": _validate_sampling_param("temperature", req.temperature, 0.1, 1.5),
        "top_k": _validate_sampling_param("top_k", req.top_k, 1, 100, integer=True),
        "top_p": _validate_sampling_param("top_p", req.top_p, 0.5, 1.0),
        "repetition_penalty": _validate_sampling_param("repetition_penalty", req.repetition_penalty, 1.0, 2.0),
    }
    # A browser retry/double-click with the same token returns the original job.
    if req.idempotency_key:
        existing_id = _LONG_AUDIO_IDEMPOTENCY.get(req.idempotency_key)
        existing = _LONG_AUDIO_JOBS.get(existing_id) if existing_id else None
        if existing:
            return _LONG_AUDIO_JOBS.public(existing)
    job = _LONG_AUDIO_JOBS.create(
        text=text,
        voice=req.voice,
        speed=PODCAST_FINAL_TEMPO if is_podcast_brand else req.speed,
        prosody_markup=False if is_podcast_brand else req.prosody_markup,
        options={} if is_podcast_brand else options,
    )
    if req.idempotency_key:
        _LONG_AUDIO_IDEMPOTENCY[req.idempotency_key] = job.id
    return _LONG_AUDIO_JOBS.public(job)


@app.get("/api/long-audio/jobs/{job_id}")
def get_long_audio_job(job_id: str):
    job = _LONG_AUDIO_JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Long Audio job not found")
    return _LONG_AUDIO_JOBS.public(job)


@app.delete("/api/long-audio/jobs/{job_id}")
def cancel_long_audio_job(job_id: str):
    job = _LONG_AUDIO_JOBS.cancel(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Long Audio job not found")
    return _LONG_AUDIO_JOBS.public(job)


@app.post("/api/long-audio/jobs/{job_id}/resume")
def resume_long_audio_job(job_id: str):
    job = _LONG_AUDIO_JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Long Audio job not found")
    if job.state not in {"FAILED", "CANCELLED"}:
        raise HTTPException(status_code=409, detail="Only failed or cancelled jobs can be resumed")
    return _LONG_AUDIO_JOBS.public(_LONG_AUDIO_JOBS.resume(job_id))


@app.get("/api/long-audio/jobs/{job_id}/audio")
def get_long_audio_result(job_id: str):
    job = _LONG_AUDIO_JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Long Audio job not found")
    if job.state != "COMPLETED" or not job.output_path or not job.output_path.exists():
        raise HTTPException(status_code=409, detail="Long Audio result is not ready")
    return FileResponse(str(job.output_path), media_type="audio/wav", filename=f"{job_id}.wav")


@app.post("/api/tts/clone")
async def tts_clone(
    request: Request,
    text: Optional[str] = Form(None),
    voice: Optional[str] = Form(None),
    speed: Optional[float] = Form(None),
    emotion: Optional[str] = Form(None),
    ref_audio: UploadFile = File(None),
    temperature: Optional[float] = Form(None),
    top_k: Optional[int] = Form(None),
    top_p: Optional[float] = Form(None),
    repetition_penalty: Optional[float] = Form(None),
    engine: TTSEngine = Depends(get_engine),
):
    # Compatibility: explicit FormData wins over the legacy query contract.
    def form_or_query(name: str, form_value, default=None):
        if form_value is not None:
            return form_value
        return request.query_params.get(name, default)

    text = form_or_query("text", text)
    voice = form_or_query("voice", voice)
    speed_raw = form_or_query("speed", speed, 1.0)
    emotion = form_or_query("emotion", emotion)
    temperature = form_or_query("temperature", temperature)
    top_k = form_or_query("top_k", top_k)
    top_p = form_or_query("top_p", top_p)
    repetition_penalty = form_or_query("repetition_penalty", repetition_penalty)
    try:
        speed = float(speed_raw)
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail="Invalid speed")

    # Basic form validation
    if text is None or not isinstance(text, str) or not text.strip():
        raise HTTPException(status_code=400, detail="Text must not be empty")
    if len(text) > TEXT_MAX_LENGTH:
        raise HTTPException(status_code=413, detail="Text too long")

    # Validate voice if provided
    voices = engine.get_voices() or ["default"]
    if voice and voice not in voices:
        raise HTTPException(status_code=400, detail="Giọng đọc không hợp lệ")

    # Validate file
    if ref_audio is None:
        raise HTTPException(status_code=400, detail="Thiếu tệp âm thanh tham chiếu")
    original_name = ref_audio.filename or ""
    source_ext = os.path.splitext(original_name)[1].lower()
    if source_ext not in CLONE_AUDIO_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Tệp tham chiếu phải là WAV, MP3 hoặc M4A",
        )

    # save to temporary file (keep the real extension so decoders recognize it)
    tmp_ref = tempfile.NamedTemporaryFile(delete=False, suffix=source_ext)
    tmp_ref_path = tmp_ref.name
    try:
        data = await ref_audio.read()
        # enforce upload size limit
        if len(data) > REF_MAX_BYTES:
            try:
                tmp_ref.close()
                os.remove(tmp_ref_path)
            except Exception:
                pass
            raise HTTPException(status_code=413, detail="Tệp tham chiếu quá lớn")
        tmp_ref.write(data)
        tmp_ref.close()
    except HTTPException:
        raise
    except Exception:
        try:
            os.remove(tmp_ref_path)
        except Exception:
            pass
        raise HTTPException(status_code=400, detail="Không thể lưu tệp tham chiếu")

    # Convert non-WAV uploads (MP3/M4A) into a temporary PCM WAV first.
    ref_wav_path = tmp_ref_path
    converted_tmp_path = None
    if source_ext != ".wav":
        try:
            ref_wav_path, converted_tmp_path = _prepare_reference_wav(tmp_ref_path, source_ext)
        except HTTPException:
            try:
                os.remove(tmp_ref_path)
            except Exception:
                pass
            raise
        except RuntimeError as e:
            try:
                os.remove(tmp_ref_path)
            except Exception:
                pass
            raise HTTPException(status_code=400, detail=str(e))
        except Exception:
            try:
                os.remove(tmp_ref_path)
            except Exception:
                pass
            raise HTTPException(status_code=500, detail="Không thể chuyển đổi tệp âm thanh sang WAV.")

    def _cleanup_clone_temps():
        for p in (tmp_ref_path, converted_tmp_path):
            if p:
                try:
                    os.remove(p)
                except Exception:
                    pass

    # run lightweight validation: check duration <= allowed max and readable wav
    try:
        import soundfile as sf
        info = sf.info(ref_wav_path)
        duration = info.frames / float(info.samplerate)
        if duration <= 0:
            _cleanup_clone_temps()
            raise HTTPException(status_code=400, detail="Tệp âm thanh rỗng hoặc không hợp lệ")
        # determine allowed max seconds from underlying engine if possible
        allowed_max = 10.0
        try:
            import inspect as _inspect
            v = getattr(engine, '_model', None)
            if v is not None:
                underlying = getattr(v, '_v', None)
                eng = getattr(underlying, 'engine', None)
                if eng is not None and hasattr(eng, 'prepare_reference'):
                    sig = _inspect.signature(eng.prepare_reference)
                    if 'max_seconds' in sig.parameters and sig.parameters['max_seconds'].default is not _inspect._empty:
                        allowed_max = float(sig.parameters['max_seconds'].default)
        except Exception:
            allowed_max = 10.0
        if duration > allowed_max:
            _cleanup_clone_temps()
            raise HTTPException(status_code=413, detail=f"Tệp tham chiếu quá dài (tối đa {allowed_max:.0f}s)")
    except HTTPException:
        raise
    except Exception:
        _cleanup_clone_temps()
        raise HTTPException(status_code=400, detail="Tệp âm thanh không hợp lệ hoặc định dạng không được hỗ trợ")

    # map emotion name -> token only for verified mappings
    emotion_map = {"natural": "<|emotion_0|>"}
    emotion_tag = None
    if emotion:
        if emotion not in emotion_map:
            _cleanup_clone_temps()
            raise HTTPException(status_code=422, detail="Biểu cảm không được hỗ trợ")
        emotion_tag = emotion_map[emotion]

    # prepare output temp
    out_tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    out_tmp_path = out_tmp.name
    out_tmp.close()

    # ensure temporary reference file is cleaned up in all outcomes
    try:
        # acquire semaphore (blocking). measure wait time for logging.
        wait_start = time.monotonic()
        _TTS_SEMAPHORE.acquire()
        wait_elapsed = time.monotonic() - wait_start
        if wait_elapsed > 0.0:
            logger.info("inference slot waited %.3fs", wait_elapsed)
        try:
            # validate optional sampling params for clone
            temperature_v = _validate_sampling_param("temperature", temperature, 0.1, 1.5)
            top_k_v = _validate_sampling_param("top_k", top_k, 1, 100, integer=True)
            top_p_v = _validate_sampling_param("top_p", top_p, 0.5, 1.0)
            repetition_penalty_v = _validate_sampling_param("repetition_penalty", repetition_penalty, 1.0, 2.0)

            # call engine.generate with ref_audio and emotion_tag; forward sampling params when provided
            engine.generate(
                text,
                voice=voice,
                speed=speed,
                out_path=out_tmp_path,
                ref_audio=ref_wav_path,
                emotion_tag=emotion_tag,
                temperature=temperature_v,
                top_k=top_k_v,
                top_p=top_p_v,
                repetition_penalty=repetition_penalty_v,
            )
        except HTTPException:
            _remove_file(out_tmp_path)
            raise
        except Exception as e:
            _remove_file(out_tmp_path)
            raise HTTPException(status_code=500, detail=f"TTS generation thất bại: {e}")
        finally:
            try:
                _TTS_SEMAPHORE.release()
                logger.info("inference slot released")
            except Exception:
                pass
    finally:
        _cleanup_clone_temps()

    return FileResponse(out_tmp_path, media_type="audio/wav", filename=os.path.basename(out_tmp_path), background=BackgroundTask(_remove_file, out_tmp_path))


@app.post("/api/tts/upload")
async def tts_upload(file: UploadFile = File(...), engine: TTSEngine = Depends(get_engine)):
    # only accept .txt
    if not file.filename.lower().endswith(".txt"):
        raise HTTPException(status_code=400, detail="Only .txt files are accepted")

    data = await file.read()
    try:
        text = data.decode("utf-8")
    except Exception:
        raise HTTPException(status_code=400, detail="Failed to decode file; ensure UTF-8")

    if not text.strip():
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    if len(text) > TEXT_MAX_LENGTH:
        raise HTTPException(status_code=413, detail="Text too long")

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    tmp_path = tmp.name
    tmp.close()

    # async endpoint: avoid blocking event loop by acquiring semaphore in executor
    loop = asyncio.get_running_loop()
    wait_start = time.monotonic()
    # acquire using executor so event loop is not blocked
    await loop.run_in_executor(None, _TTS_SEMAPHORE.acquire)
    wait_elapsed = time.monotonic() - wait_start
    if wait_elapsed > 0.0:
        logger.info("inference slot waited %.3fs (async)", wait_elapsed)
    try:
        # run blocking generate in executor to avoid blocking loop
        await loop.run_in_executor(None, engine.generate, text, None, 1.0, tmp_path)
    except Exception as e:
        _remove_file(tmp_path)
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {e}")
    finally:
        try:
            _TTS_SEMAPHORE.release()
            logger.info("inference slot released (async)")
        except Exception:
            pass

    return FileResponse(tmp_path, media_type="audio/wav", filename=os.path.basename(tmp_path), background=BackgroundTask(_remove_file, tmp_path))
