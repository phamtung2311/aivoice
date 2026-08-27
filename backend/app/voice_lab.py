"""Small local JSON store and validation models for branded-voice experiments."""

from __future__ import annotations

import json
import os
import secrets
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


SCHEMA_VERSION = 1
VERIFIED_CUES = ["[cười]", "[thở dài]", "[hắng giọng]"]
BASELINE_PARAMETERS = {
    "speed": 1.0,
    "temperature": 0.8,
    "top_k": 25,
    "top_p": 0.95,
    "repetition_penalty": 1.2,
}

_LOCK = threading.RLock()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def voice_lab_dir() -> Path:
    return Path(os.environ.get("VOICE_LAB_DIR", str(Path("data") / "voice_lab")))


def corpus_path() -> Path:
    return Path(os.environ.get("VOICE_LAB_CORPUS_PATH", str(Path("data") / "voice_lab" / "evaluation_corpus.json")))


def quality_corpus_path() -> Path:
    return Path(os.environ.get("VOICE_LAB_QUALITY_CORPUS_PATH", str(Path("data") / "voice_lab" / "quality_corpus.json")))


def experiments_path() -> Path:
    return voice_lab_dir() / "experiments.json"


def branded_manifest_path() -> Path:
    return voice_lab_dir() / "branded_voice.json"


def temperature_candidates_path() -> Path:
    return voice_lab_dir() / "temperature_candidates.json"


def _read_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"Invalid Voice Lab JSON: {path}") from exc


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temp_path, path)


class ReferenceMetadata(BaseModel):
    id: Literal["reference_a", "reference_b", "reference_c", "saved_voice"]
    label: str = Field(min_length=1, max_length=64)
    filename: str = Field(min_length=1, max_length=255)
    format: Literal["wav", "mp3", "m4a"]
    size_bytes: int = Field(gt=0, le=5 * 1024 * 1024)
    duration_seconds: Optional[float] = Field(default=None, gt=0, le=8)


class ExperimentParameters(BaseModel):
    speed: float = 1.0
    temperature: float = Field(default=0.8, ge=0.1, le=1.5)
    top_k: int = Field(default=25, ge=1, le=100)
    top_p: float = Field(default=0.95, ge=0.5, le=1.0)
    repetition_penalty: float = Field(default=1.2, ge=1.0, le=2.0)

    @field_validator("speed")
    @classmethod
    def identity_speed_must_be_native(cls, value: float) -> float:
        if float(value) != 1.0:
            raise ValueError("Voice Lab identity experiments require speed=1.0")
        return 1.0

    @field_validator("top_k")
    @classmethod
    def initial_voice_lab_keeps_top_k_fixed(cls, value: int) -> int:
        if value != 25:
            raise ValueError("Initial Voice Lab experiments require top_k=25")
        return 25


class ListeningScores(BaseModel):
    identity: int = Field(ge=1, le=5)
    naturalness: int = Field(ge=1, le=5)
    pronunciation: int = Field(ge=1, le=5)
    prosody: int = Field(ge=1, le=5)
    audio_cleanliness: int = Field(ge=1, le=5)
    consistency: int = Field(ge=1, le=5)


class ExperimentCreate(BaseModel):
    reference: ReferenceMetadata
    saved_voice_id: Optional[str] = Field(default=None, max_length=64)
    evaluation_text_id: str = Field(min_length=1, max_length=64)
    parameters: ExperimentParameters = Field(default_factory=ExperimentParameters)
    round: Literal["reference_selection", "temperature", "top_p", "repetition_penalty", "custom"] = "reference_selection"
    run_number: int = Field(default=1, ge=1, le=2)
    has_audio: bool = False

    @model_validator(mode="after")
    def validate_controlled_round(self):
        p = self.parameters
        if self.round == "reference_selection" and p.model_dump() != BASELINE_PARAMETERS:
            raise ValueError("Reference selection round must use baseline parameters")
        if self.round == "temperature":
            if not self.saved_voice_id:
                raise ValueError("Temperature round requires a saved voice")
            if p.temperature not in (0.7, 0.8, 0.9) or p.top_k != 25 or p.top_p != 0.95 or p.repetition_penalty != 1.2 or p.speed != 1.0:
                raise ValueError("Temperature round must vary only temperature across 0.7/0.8/0.9")
        if self.round == "top_p":
            if p.top_p not in (0.9, 0.95) or p.repetition_penalty != 1.2:
                raise ValueError("Top P round must use 0.90 or 0.95 and keep repetition baseline")
        if self.round == "repetition_penalty" and p.repetition_penalty not in (1.1, 1.2, 1.3):
            raise ValueError("Repetition round must use 1.1, 1.2, or 1.3")
        return self


class ExperimentEvaluation(BaseModel):
    scores: ListeningScores
    notes: str = Field(default="", max_length=2000)
    missing_words: bool = False
    missing_word_note: str = Field(default="", max_length=500)

    @model_validator(mode="after")
    def missing_word_note_requires_flag(self):
        if self.missing_word_note.strip() and not self.missing_words:
            raise ValueError("missing_word_note requires missing_words=true")
        return self


class ExperimentRecord(ExperimentCreate):
    id: str
    created_at: str
    runtime: Dict[str, str]
    evaluation_text: str
    cue: Optional[str] = None
    status: Literal["pending_evaluation", "evaluated"] = "pending_evaluation"
    scores: Optional[ListeningScores] = None
    notes: str = ""
    missing_words: bool = False
    missing_word_note: str = ""
    evaluated_at: Optional[str] = None
    average_score: Optional[float] = None


class TemperatureCandidateSelection(BaseModel):
    """A user-confirmed sampling candidate; never contains voice identity data."""
    saved_voice_id: str = Field(min_length=1, max_length=64)
    temperature: float
    top_k: int = 25
    top_p: float = 0.95
    repetition_penalty: float = 1.2
    speed: float = 1.0
    selected_at: str = Field(default_factory=_utc_now)
    evaluation_summary: Dict[str, float] = Field(default_factory=dict)

    @model_validator(mode="after")
    def only_temperature_candidate_is_allowed(self):
        if self.temperature not in (0.7, 0.8, 0.9):
            raise ValueError("Temperature candidate must be 0.7, 0.8, or 0.9")
        if (self.top_k, self.top_p, self.repetition_penalty, self.speed) != (25, 0.95, 1.2, 1.0):
            raise ValueError("Temperature candidate must keep speed=1.0, top_k=25, top_p=0.95, repetition_penalty=1.2")
        return self


class StylePreset(BaseModel):
    name: Literal["Natural", "Storytelling"]
    parameters: ExperimentParameters
    text_guidance: str = Field(default="", max_length=500)


class BrandedVoiceManifest(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    saved_voice_id: str = Field(min_length=1, max_length=64)
    runtime: Dict[str, str]
    reference_id: Literal["reference_a", "reference_b", "reference_c"]
    parameters: ExperimentParameters
    recommended_speed: float = 1.0
    verified_cues: List[str] = Field(default_factory=lambda: list(VERIFIED_CUES))
    created_at: str = Field(default_factory=_utc_now)
    evaluation_summary: Dict[str, float] = Field(default_factory=dict)
    notes: str = Field(default="", max_length=2000)
    style_presets: List[StylePreset] = Field(default_factory=list, max_length=2)

    @field_validator("recommended_speed")
    @classmethod
    def recommended_speed_stays_native(cls, value: float) -> float:
        if float(value) != 1.0:
            raise ValueError("Initial branded voice manifest requires recommended_speed=1.0")
        return 1.0

    @field_validator("verified_cues")
    @classmethod
    def cues_must_be_verified(cls, values: List[str]) -> List[str]:
        if any(value not in VERIFIED_CUES for value in values):
            raise ValueError("Manifest contains an unverified cue")
        return values


def load_corpus(path: Optional[Path] = None) -> dict:
    data = _read_json(Path(path) if path else corpus_path(), None)
    if not isinstance(data, dict) or not isinstance(data.get("sentences"), list):
        raise ValueError("Voice Lab corpus is missing or invalid")
    if len(data["sentences"]) != 6:
        raise ValueError("Voice Lab corpus must contain exactly 6 sentences")
    ids = [item.get("id") for item in data["sentences"] if isinstance(item, dict)]
    if len(ids) != 6 or len(set(ids)) != 6:
        raise ValueError("Voice Lab corpus sentence ids must be unique")
    return data


def load_quality_corpus(path: Optional[Path] = None) -> dict:
    """Neutral, fixed corpus for structural quality comparisons (no emotion cues)."""
    data = _read_json(Path(path) if path else quality_corpus_path(), None)
    if not isinstance(data, dict) or not isinstance(data.get("sentences"), list):
        raise ValueError("Voice quality corpus is missing or invalid")
    ids = [item.get("id") for item in data["sentences"] if isinstance(item, dict)]
    if len(ids) < 5 or len(ids) != len(set(ids)) or any(not item for item in ids):
        raise ValueError("Voice quality corpus requires at least five unique sentence ids")
    return data


def load_experiment_corpus() -> dict:
    """Expose both legacy identity and Phase 20 neutral quality texts centrally."""
    identity = load_corpus()
    quality = load_quality_corpus()
    combined = identity["sentences"] + quality["sentences"]
    if len({item.get("id") for item in combined}) != len(combined):
        raise ValueError("Voice Lab corpus ids must be globally unique")
    return {"sentences": combined, "rubric": identity["rubric"], "score_scale": identity.get("score_scale", {})}


def load_experiments(path: Optional[Path] = None) -> List[dict]:
    store = Path(path) if path else experiments_path()
    data = _read_json(store, {"version": SCHEMA_VERSION, "experiments": []})
    records = data.get("experiments", []) if isinstance(data, dict) else []
    if not isinstance(records, list):
        raise ValueError("Voice Lab experiments store is invalid")
    return records


def _save_experiments(records: List[dict], path: Optional[Path] = None) -> None:
    _write_json(Path(path) if path else experiments_path(), {"version": SCHEMA_VERSION, "experiments": records})


def temperature_summary(saved_voice_id: str, temperature: float) -> Dict[str, float]:
    """Summarize user-entered scores only; no waveform/model quality judgment."""
    records = [
        ExperimentRecord.model_validate(item) for item in load_experiments()
        if item.get("round") == "temperature"
        and item.get("saved_voice_id") == saved_voice_id
        and item.get("parameters", {}).get("temperature") == temperature
        and item.get("status") == "evaluated"
    ]
    summary: Dict[str, float] = {"evaluated_runs": float(len(records)), "missing_word_count": float(sum(record.missing_words for record in records))}
    if not records:
        return summary
    averages = [record.average_score for record in records if record.average_score is not None]
    if averages:
        summary["average_score"] = round(sum(averages) / len(averages), 2)
    for criterion in ListeningScores.model_fields:
        values = [getattr(record.scores, criterion) for record in records if record.scores is not None]
        if values:
            summary[f"{criterion}_average"] = round(sum(values) / len(values), 2)
    return summary


def load_temperature_candidates(path: Optional[Path] = None) -> Dict[str, dict]:
    data = _read_json(Path(path) if path else temperature_candidates_path(), {"version": SCHEMA_VERSION, "candidates": {}})
    candidates = data.get("candidates", {}) if isinstance(data, dict) else {}
    if not isinstance(candidates, dict):
        raise ValueError("Temperature candidates store is invalid")
    return {voice_id: TemperatureCandidateSelection.model_validate(candidate).model_dump(mode="json") for voice_id, candidate in candidates.items()}


def save_temperature_candidate(selection: TemperatureCandidateSelection, *, user_confirmed: bool, path: Optional[Path] = None) -> dict:
    if not user_confirmed:
        raise ValueError("Temperature selection must be explicitly confirmed by the user")
    target = Path(path) if path else temperature_candidates_path()
    with _LOCK:
        candidates = load_temperature_candidates(target)
        candidates[selection.saved_voice_id] = selection.model_dump(mode="json")
        _write_json(target, {"version": SCHEMA_VERSION, "candidates": candidates})
    return candidates[selection.saved_voice_id]


def create_experiment(payload: ExperimentCreate, runtime: Dict[str, str]) -> dict:
    corpus = load_experiment_corpus()
    sentence = next((item for item in corpus["sentences"] if item.get("id") == payload.evaluation_text_id), None)
    if sentence is None:
        raise ValueError("Unknown evaluation_text_id")

    record = ExperimentRecord(
        **payload.model_dump(),
        id=f"exp_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}_{secrets.token_hex(3)}",
        created_at=_utc_now(),
        runtime={str(k): str(v) for k, v in runtime.items()},
        evaluation_text=sentence["text"],
        cue=sentence.get("cue"),
    )
    with _LOCK:
        records = load_experiments()
        records.append(record.model_dump(mode="json"))
        _save_experiments(records)
    return record.model_dump(mode="json")


def evaluate_experiment(experiment_id: str, evaluation: ExperimentEvaluation) -> dict:
    with _LOCK:
        records = load_experiments()
        index = next((i for i, item in enumerate(records) if item.get("id") == experiment_id), None)
        if index is None:
            raise KeyError(experiment_id)
        record = ExperimentRecord.model_validate(records[index])
        score_values = list(evaluation.scores.model_dump().values())
        updated = record.model_copy(update={
            "status": "evaluated",
            "scores": evaluation.scores,
            "notes": evaluation.notes,
            "missing_words": evaluation.missing_words,
            "missing_word_note": evaluation.missing_word_note.strip(),
            "evaluated_at": _utc_now(),
            "average_score": round(sum(score_values) / len(score_values), 2),
        })
        records[index] = updated.model_dump(mode="json")
        _save_experiments(records)
    return updated.model_dump(mode="json")


def set_experiment_audio_status(experiment_id: str, has_audio: bool) -> dict:
    """Synchronize browser IndexedDB cleanup with the persistent experiment row."""
    with _LOCK:
        records = load_experiments()
        index = next((i for i, item in enumerate(records) if item.get("id") == experiment_id), None)
        if index is None:
            raise KeyError(experiment_id)
        record = ExperimentRecord.model_validate(records[index])
        updated = record.model_copy(update={"has_audio": bool(has_audio)})
        records[index] = updated.model_dump(mode="json")
        _save_experiments(records)
    return updated.model_dump(mode="json")


def load_branded_manifest(path: Optional[Path] = None) -> Optional[dict]:
    data = _read_json(Path(path) if path else branded_manifest_path(), None)
    if data is None:
        return None
    return BrandedVoiceManifest.model_validate(data).model_dump(mode="json")


def save_branded_manifest(
    manifest: BrandedVoiceManifest,
    *,
    user_confirmed: bool = False,
    path: Optional[Path] = None,
) -> dict:
    if not user_confirmed:
        raise ValueError("A branded voice winner must be explicitly selected by the user")
    payload = manifest.model_dump(mode="json")
    with _LOCK:
        _write_json(Path(path) if path else branded_manifest_path(), payload)
    return payload
