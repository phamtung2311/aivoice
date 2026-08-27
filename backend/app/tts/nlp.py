"""Deterministic, opt-in Vietnamese speech-text normalization (Phase 24).

This is intentionally a small regex/dictionary layer.  It does not call a
model, change normal Vietnamese prose, collapse whitespace, or rewrite source
markup.  The TTS API is its only production caller.
"""

from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Dict


_DIGITS = ("không", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín")
_SCALES = ("", "nghìn", "triệu", "tỷ", "nghìn tỷ", "triệu tỷ")
_DEFAULT_DICTIONARY = {
    "OpenAI": "Ô-pần AI",
    "ChatGPT": "Chat G P T",
    "HTML": "hát ti em eo",
    "CSS": "xi ét ét",
    "CPU": "xê pi u",
    "GPU": "gi pi u",
    "USB": "iu ét bê",
    "API": "ây pi ai",
    "URL": "iu a en",
    "SQL": "ét kiu eo",
    "AI": "ây ai",
}

_DATE_RE = re.compile(r"(?<![\w/])([0-3]?\d)/(0?\d|1[0-2])/(\d{4})(?![\w/])")
_VIETNAMESE_DATE_RE = re.compile(r"(?<!\w)ngày\s+([0-3]?\d)\s+tháng\s+(0?\d|1[0-2])\s+năm\s+(\d{4})(?!\w)", re.IGNORECASE)
_MONEY_RE = re.compile(r"(?<![\w.])(\d{1,3}(?:\.\d{3})+)(?:\s*)đ(?!\w)", re.IGNORECASE)
_PERCENT_RE = re.compile(r"(?<!\w)(\d+(?:,\d+)?)%(?!\w)")
_TIME_RE = re.compile(r"(?<![\w:])(\d{1,2}):(\d{2})(?![\w:])")
_FRACTION_RE = re.compile(r"(?<![\w/])(\d+)\s*/\s*(\d+)(?![\w/])")
_DECIMAL_RE = re.compile(r"(?<![\w,])(\d+),(\d+)(?![\w,])")


def custom_dictionary_path() -> Path:
    return Path(os.environ.get("NLP_CUSTOM_DICTIONARY_PATH", str(Path("data") / "nlp" / "custom_dictionary.json")))


@lru_cache(maxsize=8)
def _load_custom_dictionary(path_text: str, mtime_ns: int) -> Dict[str, str]:
    path = Path(path_text)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Invalid custom NLP dictionary: {path}") from exc
    if not isinstance(raw, dict):
        raise ValueError("Custom NLP dictionary must be a JSON object")
    return {str(key): str(value) for key, value in raw.items() if str(key) and str(value)}


def load_dictionary() -> Dict[str, str]:
    """Return built-in pronunciations overlaid by editable local entries."""
    path = custom_dictionary_path()
    try:
        mtime_ns = path.stat().st_mtime_ns
    except FileNotFoundError:
        mtime_ns = -1
    return {**_DEFAULT_DICTIONARY, **_load_custom_dictionary(str(path), mtime_ns)}


def _read_under_thousand(value: int, *, padded: bool = False) -> str:
    hundred, remainder = divmod(value, 100)
    words = []
    if hundred or padded:
        words.extend((_DIGITS[hundred], "trăm"))
    tens, unit = divmod(remainder, 10)
    if tens >= 2:
        words.extend((_DIGITS[tens], "mươi"))
        if unit == 1:
            words.append("mốt")
        elif unit == 4:
            words.append("tư")
        elif unit == 5:
            words.append("lăm")
        elif unit:
            words.append(_DIGITS[unit])
    elif tens == 1:
        words.append("mười")
        words.append("lăm" if unit == 5 else _DIGITS[unit] if unit else "")
    elif unit:
        if hundred or padded:
            words.append("lẻ")
        words.append(_DIGITS[unit])
    return " ".join(word for word in words if word)


def number_to_words(value: int) -> str:
    """Read a non-negative integer using compact Vietnamese cardinal wording."""
    value = int(value)
    if value == 0:
        return _DIGITS[0]
    if value < 0:
        return "âm " + number_to_words(-value)
    groups = []
    while value:
        groups.append(value % 1000)
        value //= 1000
    words = []
    for index in range(len(groups) - 1, -1, -1):
        group = groups[index]
        if not group:
            continue
        # A present lower group is read as three digits after a higher group,
        # which makes 2026 read “hai nghìn không trăm hai mươi sáu”.
        padded = index < len(groups) - 1 and group < 100
        words.append(_read_under_thousand(group, padded=padded))
        if index < len(_SCALES) and _SCALES[index]:
            words.append(_SCALES[index])
    return " ".join(words)


def _replace_dictionary(text: str, dictionary: Dict[str, str]) -> str:
    if not dictionary:
        return text
    alternatives = "|".join(re.escape(key) for key in sorted(dictionary, key=len, reverse=True))
    pattern = re.compile(rf"(?<!\w)({alternatives})(?!\w)")
    return pattern.sub(lambda match: dictionary[match.group(1)], text)


def _normalize_ddmmyyyy(match: re.Match) -> str:
    """Read a date with an explicit, separately spoken year introducer."""
    day, month, year = (int(match.group(index)) for index in (1, 2, 3))
    # The comma prevents the TTS/G2P layer from coalescing the adjacent words
    # in dates such as month 5: “tháng năm, năm hai nghìn ...”.
    return f"ngày {number_to_words(day)} tháng {number_to_words(month)}, năm {number_to_words(year)}"


def normalize_text(text: str, *, enabled: bool = True) -> str:
    """Return deterministic spoken forms for recognized text patterns only."""
    if text is None:
        return ""
    if not enabled:
        return text

    # Keep URLs and inline/fenced code unchanged, so markdown-like text and
    # technical examples retain their syntax verbatim.
    protected = []

    def protect(match):
        protected.append(match.group(0))
        return f"\uFFF0{len(protected) - 1}\uFFF1"

    result = re.sub(r"```[\s\S]*?```|`[^`]*`|https?://[^\s)]+", protect, text)
    # Normalize written and slash dates to the same wording.  The written
    # form consumes its existing year introducer, so it cannot duplicate
    # “năm” before the year.
    result = _VIETNAMESE_DATE_RE.sub(_normalize_ddmmyyyy, result)
    result = _DATE_RE.sub(_normalize_ddmmyyyy, result)
    result = _MONEY_RE.sub(lambda m: f"{number_to_words(int(m.group(1).replace('.', '')))} đồng", result)
    result = _PERCENT_RE.sub(lambda m: f"{number_to_words(int(m.group(1).split(',')[0]))}{' phẩy ' + ' '.join(_DIGITS[int(d)] for d in m.group(1).split(',')[1]) if ',' in m.group(1) else ''} phần trăm", result)
    result = _TIME_RE.sub(lambda m: f"{number_to_words(int(m.group(1)))} giờ {number_to_words(int(m.group(2)))} phút", result)
    result = _FRACTION_RE.sub(lambda m: f"{number_to_words(int(m.group(1)))} phần {number_to_words(int(m.group(2)))}", result)
    result = _DECIMAL_RE.sub(lambda m: f"{number_to_words(int(m.group(1)))} phẩy {' '.join(_DIGITS[int(d)] for d in m.group(2))}", result)
    result = _replace_dictionary(result, load_dictionary())
    return re.sub(r"\uFFF0(\d+)\uFFF1", lambda m: protected[int(m.group(1))], result)
