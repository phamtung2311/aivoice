"""Deterministic, user-authored podcast prosody markup.

This module intentionally contains no model or language-model logic.  The
small syntax is only an editing aid: ``|`` (light), ``||`` (medium), and
``|||`` (long) create a requested pause after the preceding spoken segment.
"""
from dataclasses import dataclass
import re

PODCAST_PROSODY_VERSION = "podcast_prosody_v1"
PAUSE_PRESETS_MS = {"light": 70, "medium": 140, "long": 260}
MARKER_PAUSES_MS = {"|": PAUSE_PRESETS_MS["light"], "||": PAUSE_PRESETS_MS["medium"], "|||": PAUSE_PRESETS_MS["long"]}
PAUSE_MARKERS = {pause_ms: marker for marker, pause_ms in MARKER_PAUSES_MS.items()}
_MARKER_RE = re.compile(r"(\|{1,3})")


@dataclass(frozen=True)
class ProsodySegment:
    text: str
    pause_after_ms: int | None = None


def parse_prosody_script(text: str) -> list[ProsodySegment]:
    """Parse a user TTS script without letting control markers reach a model.

    Whitespace immediately beside a marker is editorial spacing and is not
    spoken. Punctuation remains part of its adjacent spoken segment. Empty or
    consecutive markers are rejected instead of guessing at a double pause.
    """
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Prosody script must contain text")
    if "||||" in text:
        raise ValueError("Prosody markers may contain at most three bars")

    parts = _MARKER_RE.split(text)
    segments: list[ProsodySegment] = []
    pending_text: str | None = None
    pending_pause: int | None = None
    for index, part in enumerate(parts):
        if part in MARKER_PAUSES_MS:
            if pending_text is None or not pending_text.strip() or pending_pause is not None:
                raise ValueError("Each prosody marker must follow one spoken segment")
            pending_pause = MARKER_PAUSES_MS[part]
            continue
        if pending_text is None:
            pending_text = part.strip()
        elif pending_pause is not None:
            if not part.strip():
                if index == len(parts) - 1:
                    break  # A final marker requests silence after the last words.
                raise ValueError("Each prosody marker must be followed by spoken text")
            segments.append(ProsodySegment(pending_text, pending_pause))
            pending_text, pending_pause = part.strip(), None
        else:
            pending_text += part
    if pending_text is None or not pending_text.strip():
        raise ValueError("Prosody script must end with spoken text")
    segments.append(ProsodySegment(pending_text, pending_pause))
    return segments


def transform_prosody_script(text: str, transform) -> str:
    """Apply a clean-text transform per segment without exposing markers to it."""
    pieces: list[str] = []
    for segment in parse_prosody_script(text):
        pieces.append(transform(segment.text))
        if segment.pause_after_ms is not None:
            pieces.append(PAUSE_MARKERS[segment.pause_after_ms])
    return " ".join(pieces)
