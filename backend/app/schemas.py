"""Request contracts shared by the HTTP endpoints."""

from typing import Optional

from pydantic import BaseModel, Field

TEXT_MAX_LENGTH = 10000


class TTSRequest(BaseModel):
    text: str = Field(..., description="Text to synthesize")
    voice: Optional[str] = Field(None, description="Voice id")
    speed: float = Field(1.0, ge=0.5, le=2.0, description="Playback speed")
    # optional sampling params — None means "use model defaults"
    temperature: Optional[float] = Field(None, description="Sampling temperature")
    top_k: Optional[int] = Field(None, description="Top-K sampling")
    top_p: Optional[float] = Field(None, description="Top-P sampling")
    repetition_penalty: Optional[float] = Field(None, description="Repetition penalty")
    # Phase 22.1 diagnostic only: 'identity_only' drops reference codes for a
    # SAVED voice (use_ref_codes=False). Absent → production behavior unchanged.
    conditioning_mode: Optional[str] = Field(None, description="Voice Lab diagnostic conditioning mode ('identity_only')")
    smart_text_processing: bool = Field(True, description="Apply deterministic local speech-text normalization")
    tts_script: Optional[str] = Field(None, description="Optional user-edited prosody script")
    prosody_markup: bool = Field(False, description="Interpret |, ||, and ||| in tts_script")


class LongAudioRequest(TTSRequest):
    """Audio Studio's durable, progress-reporting generation request."""
    idempotency_key: Optional[str] = Field(None, max_length=100)


class ProsodySuggestionRequest(BaseModel):
    text: str = Field(..., max_length=TEXT_MAX_LENGTH)


class NLPPreviewRequest(BaseModel):
    text: str = Field(..., max_length=TEXT_MAX_LENGTH)
    smart_text_processing: bool = True


class PersonalVoiceSegmentRequest(BaseModel):
    start_seconds: float = Field(..., ge=0)
    end_seconds: float = Field(..., gt=0)
    label: str = Field("", max_length=100)
    transcript: str = Field("", max_length=2000)


class PersonalVoiceCandidateRequest(BaseModel):
    source_id: str
    segment_id: str
    engine_id: str = "vieneu_3_3_0"
    test_id: str


class CloneForm(BaseModel):
    text: str = Field(..., description="Text to synthesize")
    voice: Optional[str] = Field(None, description="Voice id")
    speed: float = Field(1.0, ge=0.5, le=2.0, description="Playback speed")
    emotion: Optional[str] = Field(None, description="Emotion name (mapped server-side)")
    # optional sampling params for clone requests
    temperature: Optional[float] = Field(None, description="Sampling temperature")
    top_k: Optional[int] = Field(None, description="Top-K sampling")
    top_p: Optional[float] = Field(None, description="Top-P sampling")
    repetition_penalty: Optional[float] = Field(None, description="Repetition penalty")
