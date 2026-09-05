"""Frozen Podcast Brand Voice policy, semantic planner, and canonical identity."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re

import numpy as np

from .text import preprocess_text, split_into_sentences

PODCAST_BRAND_VOICE_ID = "podcast_brand_voice_v1"
PODCAST_BRAND_SOURCE_VOICE_ID = "podcast_synthetic_candidate_03"
PODCAST_PIPELINE_VERSION = "podcast_brand_voice_v1"
PODCAST_SEMANTIC_PLANNER_VERSION = "podcast_semantic_planner_v2"
PODCAST_PROSODY_PROFILE = "phase41e_v3_semantic_focus"
PODCAST_PAUSE_PROFILE = "phase41h_v2"
PODCAST_FINAL_TEMPO = 0.98
PODCAST_TARGET_CHARS = 220
PODCAST_HARD_MAX_CHARS = 350

_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
PODCAST_CANDIDATE_03_ROOT = (
    _REPOSITORY_ROOT
    / "experiments/brand_voice_phase41b/baseline/PODCAST_SYNTHETIC_CANDIDATE_03"
)
PODCAST_SPEAKER_ARRAY_SHA256 = "980d5856f58a8619b6abf0c3935de74ddfb5c333b9b8fae2fd5c3b6ef7067771"
PODCAST_SPEAKER_FILE_SHA256 = "c763159d8ed6ed4b0f1916f8b0762d1902743d293fcd7874541966d7f9ee10a1"
PODCAST_REFERENCE_CODES_FILE_SHA256 = "fe8f8e3e1766a7954595fa3a355e46aca8c3e27be4aba4bb1db8d9b60a960aa5"

PODCAST_PAUSES_SECONDS = {
    "semantic_thought_boundary": 0.10,
    "setup_resolution_boundary": 0.06,
    "thought_transition": 0.22,
    "paragraph_transition": 0.32,
    "final": 0.0,
}

PODCAST_INFERENCE_CONFIG = {
    "mode": "v3turbo",
    "backend": "onnx",
    "temperature": 0.8,
    "top_k": 25,
    "top_p": 0.95,
    "repetition_penalty": 1.2,
    "repetition_window": 64,
    "denoise": True,
    "use_ref_codes": True,
    "silence_p": 0.15,
    "crossfade_p": 0.0,
    "apply_watermark": True,
    "sample_rate": 48000,
    "max_new_frames": 600,
    "max_chars": 800,
    "batch_size": 1,
}

# Adapter arguments for TTSEngine.generate. A preplanned chunk bypasses its
# generic splitter, then max_chars=800 is forwarded to VieNeu exactly.
PODCAST_ENGINE_CONFIG = {
    "temperature": 0.8,
    "top_k": 25,
    "top_p": 0.95,
    "repetition_penalty": 1.2,
    "repetition_window": 64,
    "denoise": True,
    "use_ref_codes": True,
    "silence_p": 0.15,
    "crossfade_p": 0.0,
    "apply_watermark": True,
    "max_new_frames": 600,
    "model_max_chars": 800,
    "batch_size": 1,
    "expected_sample_rate": 48000,
    "preplanned_text": True,
}

_TERMINAL_PUNCTUATION = re.compile(r"[.!?…]+(?=\s|$)")
_ANAPHORIC_START = re.compile(
    r"^(?:(?:Cảm giác|Trạng thái|Tình huống)\s+ấy|Điều này)\b",
    re.IGNORECASE,
)
_DISCOURSE_RESET = re.compile(r"^(?:Sau đó|Mỗi lần|Đôi khi)\b", re.IGNORECASE)
_STANDALONE_CONTRAST = re.compile(r"^Không phải\b.*\bmà\b", re.IGNORECASE)
_EXPLICIT_SETUP = re.compile(r"^(?:Hãy hình dung|Một cách thực tế|Dĩ nhiên)\b", re.IGNORECASE)


@dataclass(frozen=True)
class PodcastChunk:
    index: int
    paragraph_index: int
    text: str
    boundary_after: str
    primary_focus_phrase: str | None

    @property
    def pause_after_seconds(self) -> float:
        return PODCAST_PAUSES_SECONDS[self.boundary_after]


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sha256_array(value: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(value).tobytes()).hexdigest()


def load_canonical_candidate_03() -> tuple[dict, dict]:
    """Load and verify the lossless canonical Candidate 03 profile or fail."""
    speaker_path = PODCAST_CANDIDATE_03_ROOT / "speaker_emb.npy"
    codes_path = PODCAST_CANDIDATE_03_ROOT / "reference_codes.npy"
    try:
        speaker_file_hash = _sha256_file(speaker_path)
        codes_file_hash = _sha256_file(codes_path)
        if speaker_file_hash != PODCAST_SPEAKER_FILE_SHA256:
            raise RuntimeError("Candidate 03 speaker_emb.npy hash mismatch")
        if codes_file_hash != PODCAST_REFERENCE_CODES_FILE_SHA256:
            raise RuntimeError("Candidate 03 reference_codes.npy hash mismatch")
        speaker = np.load(speaker_path, allow_pickle=False).astype(np.float32, copy=False)
        codes = np.load(codes_path, allow_pickle=False)
        speaker_array_hash = _sha256_array(speaker)
        if speaker_array_hash != PODCAST_SPEAKER_ARRAY_SHA256:
            raise RuntimeError("Candidate 03 speaker embedding array hash mismatch")
    except Exception as exc:
        if isinstance(exc, RuntimeError):
            raise
        raise RuntimeError(f"Canonical Candidate 03 cannot be resolved: {exc}") from exc
    return {"speaker_emb": speaker, "codes": codes}, {
        "speaker_array_sha256": speaker_array_hash,
        "speaker_file_sha256": speaker_file_hash,
        "reference_codes_file_sha256": codes_file_hash,
        "canonical_root": str(PODCAST_CANDIDATE_03_ROOT),
    }


def semantic_chunk_to_tts_text(text: str) -> str:
    """Apply the exact terminal-punctuation policy used by Phase 41G."""
    clean = preprocess_text(text)
    return " ".join(_TERMINAL_PUNCTUATION.sub("", clean).split())


def canonical_lexical_text(text: str) -> str:
    """Word-preserving comparison; sentence-terminal punctuation is acoustic."""
    return semantic_chunk_to_tts_text(text)


def _focus_phrase(text: str) -> str | None:
    lowered = text.lower()
    for marker in ("mà là", "quan trọng", "thật sự", "chính là"):
        offset = lowered.rfind(marker)
        if offset >= 0:
            phrase = text[offset:].strip(" ,;:.")
            return phrase[:120] or None
    clauses = [part.strip(" ,;:.") for part in re.split(r"\s*[,;:]\s+", text) if part.strip(" ,;:.")]
    words = clauses[-1].split() if clauses else []
    return " ".join(words[-12:]) or None


def _starts_new_thought(sentence: str) -> bool:
    return bool(_ANAPHORIC_START.search(sentence) or _DISCOURSE_RESET.search(sentence))


def _looks_like_setup(sentences: tuple[str, ...]) -> bool:
    text = " ".join(sentences)
    if _EXPLICIT_SETUP.search(text):
        return True
    if re.search(r"^Mỗi lần\b", text, re.IGNORECASE) and re.search(r"\bđang\b", text, re.IGNORECASE):
        return True
    if re.search(r"^Điều quan trọng\b", text, re.IGNORECASE) and re.search(r"\bkhông cần\b", text, re.IGNORECASE):
        return True
    if (len(sentences) > 1 and re.search(r"^Khi\b", sentences[1], re.IGNORECASE)
            and not re.search(r"\bkhông phải\b", sentences[0], re.IGNORECASE)):
        return True
    return bool(len(sentences) > 1 and re.search(r"^Nhưng\b", sentences[0], re.IGNORECASE))


def plan_podcast_text(text: str) -> list[PodcastChunk]:
    """Plan Vietnamese prose with general discourse-aware sentence grouping."""
    clean = preprocess_text(text)
    if not clean:
        return []
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n|\n", clean) if p.strip()]
    planned: list[tuple[int, str, tuple[str, ...]]] = []
    for paragraph_index, paragraph in enumerate(paragraphs):
        current: list[str] = []

        def flush() -> None:
            if current:
                planned.append((paragraph_index, " ".join(current), tuple(current)))
                current.clear()

        for sentence in split_into_sentences(paragraph):
            tts_sentence = semantic_chunk_to_tts_text(sentence)
            if not tts_sentence:
                continue
            if current and _starts_new_thought(tts_sentence):
                flush()
            if current and len(" ".join((*current, tts_sentence))) > PODCAST_TARGET_CHARS:
                flush()
            current.append(tts_sentence)
            if _STANDALONE_CONTRAST.search(tts_sentence):
                flush()
        flush()

    result = []
    for index, (paragraph_index, chunk_text, sentences) in enumerate(planned):
        if len(chunk_text) > PODCAST_HARD_MAX_CHARS:
            raise ValueError(f"Semantic chunk exceeds {PODCAST_HARD_MAX_CHARS} characters")
        if index == len(planned) - 1:
            boundary = "final"
        elif planned[index + 1][0] != paragraph_index:
            boundary = "paragraph_transition"
        elif _looks_like_setup(sentences):
            boundary = "setup_resolution_boundary"
        else:
            boundary = "semantic_thought_boundary"
        result.append(PodcastChunk(index, paragraph_index, chunk_text, boundary, _focus_phrase(chunk_text)))

    if canonical_lexical_text(" ".join(item.text for item in result)) != canonical_lexical_text(clean):
        raise AssertionError("Semantic planning changed lexical text")
    return result


def inference_config_hash() -> str:
    payload = json.dumps(PODCAST_INFERENCE_CONFIG, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def profile_hash() -> str:
    payload = repr((PODCAST_PIPELINE_VERSION, PODCAST_SEMANTIC_PLANNER_VERSION,
                    PODCAST_PROSODY_PROFILE, PODCAST_PAUSE_PROFILE, PODCAST_FINAL_TEMPO,
                    PODCAST_PAUSES_SECONDS, PODCAST_INFERENCE_CONFIG,
                    PODCAST_SPEAKER_ARRAY_SHA256))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
