"""Reference quality analyzer for Voice Lab (Phase 23).

Pure local DSP — no AI model, no ASR, no cloud, no new dependency (numpy +
soundfile, both already used by the clone pipeline). Input: a decoded PCM WAV
file (caller reuses the existing reference decode path). Output: structural
metrics plus a 0-100 quality score with human-readable strengths/weaknesses.

The analyzer runs ONCE after a reference upload, never on every Generate.
"""

from __future__ import annotations

import io
import math
import shutil
import subprocess
from typing import Dict, List

import numpy as np
import soundfile as sf

_VA_THRESHOLD = 0.02
_CLIP_THRESHOLD = 0.999
_IDEAL_MIN, _IDEAL_MAX = 5.0, 8.0

_W_CLIP = 22
_W_NOISE = 18
_W_VOLUME = 16
_W_SILENCE = 16
_W_DURATION = 14
_W_STABILITY = 14


def _clamp(v: float) -> float:
    return max(0.0, min(1.0, v))


def _rescale(value: float, lo: float, hi: float) -> float:
    if hi <= lo:
        return 1.0
    return _clamp((value - lo) / (hi - lo))


def _db(v: float) -> float:
    return 20.0 * math.log10(v + 1e-9)


def _mono(data: np.ndarray) -> np.ndarray:
    data = np.asarray(data, dtype=np.float32)
    if data.ndim == 2:
        return data.mean(axis=1)
    return data.reshape(-1)


def _duration_score(dur: float) -> float:
    if dur <= 0:
        return 0.0
    if _IDEAL_MIN <= dur <= 8.0:
        return 1.0
    if dur < _IDEAL_MIN:
        return _rescale(dur, 1.0, _IDEAL_MIN)
    return _rescale(dur, 8.0, 10.0)


class ReferenceQuality:
    def __init__(self, metrics, score, strengths, weaknesses, bars):
        self.metrics = metrics
        self.score = score
        self.strengths = strengths
        self.weaknesses = weaknesses
        self.bars = bars

    def to_dict(self):
        return {
            "score": self.score,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "bars": {k: round(v, 3) for k, v in self.bars.items()},
            "metrics": {k: self._clean(v) for k, v in self.metrics.items()},
            "recommended": self.score >= 80,
        }

    @staticmethod
    def _clean(v):
        if isinstance(v, dict):
            return {k: round(x, 5) if isinstance(x, (int, float)) else x for k, x in v.items()}
        return round(v, 5) if isinstance(v, (int, float)) else v


def analyze_wav(wav_bytes_or_path, sample_rate_override: int = 0) -> ReferenceQuality:
    """Analyze a decoded WAV (raw bytes or filesystem path) via pure DSP."""
    is_bytes = isinstance(wav_bytes_or_path, (bytes, bytearray))
    src = io.BytesIO(bytes(wav_bytes_or_path)) if is_bytes else wav_bytes_or_path
    info = sf.info(src)
    if is_bytes:
        src.seek(0)
    sr = int(sample_rate_override) if sample_rate_override else int(info.samplerate)
    channels_in = int(info.channels)
    raw, _ = sf.read(src, dtype="float32", always_2d=False)
    return _analyze_array(_mono(raw), sr, channels_in)


def analyze_clip(audio_bytes: bytes) -> ReferenceQuality:
    """Analyze one uploaded reference clip without retaining it.

    The Voice Lab API deliberately has a single DSP entry point.  Callers pass
    the request bytes directly; this routine does not write an audio file or
    invoke any model/enrollment code.
    """
    if not isinstance(audio_bytes, (bytes, bytearray)) or not audio_bytes:
        raise ValueError("Reference audio is empty")
    try:
        return analyze_wav(audio_bytes)
    except Exception as first_error:
        # libsndfile handles WAV and most MP3 files directly.  For an M4A/AAC
        # upload, reuse the already-required FFmpeg binary through pipes: no
        # decoded or uploaded audio is retained on disk.
        if shutil.which("ffmpeg"):
            try:
                converted = subprocess.run(
                    ["ffmpeg", "-v", "error", "-i", "pipe:0", "-f", "wav", "pipe:1"],
                    input=bytes(audio_bytes), capture_output=True, timeout=60,
                )
                if converted.returncode == 0 and converted.stdout:
                    return analyze_wav(converted.stdout)
            except Exception:
                pass
        raise ValueError("Reference audio is invalid or cannot be decoded") from first_error


def quality_score(analysis: ReferenceQuality) -> int:
    """Return the bounded 0--100 score from a completed clip analysis."""
    if not isinstance(analysis, ReferenceQuality):
        raise TypeError("quality_score expects a ReferenceQuality analysis")
    return int(max(0, min(100, analysis.score)))


def _analyze_array(audio: np.ndarray, sr: int, channels_in: int) -> ReferenceQuality:
    total = len(audio)
    duration = total / float(sr) if sr else 0.0
    peak = float(np.max(np.abs(audio))) if total else 0.0
    rms = float(np.sqrt(np.mean(np.square(audio)))) if total else 0.0

    abs_audio = np.abs(audio)
    voiced = abs_audio > _VA_THRESHOLD
    voiced_count = int(np.count_nonzero(voiced))
    voiced_ratio = voiced_count / total if total else 0.0

    idx = np.nonzero(voiced)[0]
    leading = (idx[0] / sr) if idx.size else duration
    ending = ((total - 1 - idx[-1]) / sr) if idx.size else 0.0

    clip_frames = int(np.count_nonzero(abs_audio >= _CLIP_THRESHOLD))
    clip_ratio = clip_frames / total if total else 0.0

    quiet = abs_audio <= _VA_THRESHOLD
    noise_est = float(np.sqrt(np.mean(np.square(audio[quiet])))) if np.any(quiet) else 0.0
    speaking_rate = float(voiced_count / duration) if duration > 0 else 0.0

    flen = max(1, int(0.025 * sr))
    nf = max(1, total // flen)
    framed = audio[: nf * flen].reshape(nf, flen)
    frame_rms = np.sqrt(np.mean(np.square(framed), axis=1))
    vrms = frame_rms[frame_rms > _VA_THRESHOLD]
    energy_std = float(np.std(20.0 * np.log10(vrms + 1e-9))) if vrms.size >= 2 else 0.0

    metrics = {
        "duration_seconds": round(duration, 3),
        "sample_rate": int(sr),
        "channels": int(channels_in),
        "mono": bool(channels_in == 1),
        "clipping": {"ratio": round(clip_ratio, 5), "frames": clip_frames},
        "peak": round(peak, 4),
        "rms": round(rms, 4),
        "silence_ratio": round(1.0 - voiced_ratio, 4),
        "leading_silence": round(leading, 3),
        "ending_silence": round(ending, 3),
        "rms_db": round(_db(rms), 1),
        "noise_estimate": round(noise_est, 4),
        "speaking_rate": round(speaking_rate, 2),
        "energy_stability_db": round(energy_std, 2),
    }
    return _score(metrics)


def _score(m: Dict) -> ReferenceQuality:
    clip_ratio = m["clipping"]["ratio"]
    clip_pen = _clamp(clip_ratio / 0.02 if clip_ratio > 0 else 0.0)

    noise_db = _db(m["noise_estimate"]) if m["noise_estimate"] > 0 else -120.0
    noise_pen = _clamp(1.0 - _rescale(-noise_db, 30.0, 70.0))

    loud = _clamp(_rescale(m["rms_db"], -40.0, -14.0))
    vol_pen = 1.0 - loud

    sil_pen = _clamp(_rescale(m["silence_ratio"], 0.15, 0.65))
    dur_pen = 1.0 - _duration_score(m["duration_seconds"])
    stab_pen = _clamp(_rescale(m["energy_stability_db"], 2.0, 10.0))

    score = 100.0 - (
        _W_CLIP * clip_pen
        + _W_NOISE * noise_pen
        + _W_VOLUME * vol_pen
        + _W_SILENCE * sil_pen
        + _W_DURATION * dur_pen
        + _W_STABILITY * stab_pen
    )
    score = int(round(max(0.0, min(100.0, score))))

    strengths, weaknesses = [], []
    if clip_pen <= 0.1:
        strengths.append("sạch, không bị clipping")
    elif clip_pen >= 0.6:
        weaknesses.append("có vẻ bị clipping (âm vỡ)")
    if noise_pen <= 0.15:
        strengths.append("ít tạp âm nền")
    elif noise_pen > 0.5:
        weaknesses.append("nền nhiễu khá rõ")
    if vol_pen <= 0.12:
        strengths.append("âm lượng ổn định, vừa đủ")
    elif vol_pen > 0.5:
        weaknesses.append("âm lượng hơi thấp")
    if m["rms_db"] > -14:
        weaknesses.append("volume gần hạn — ít headroom")
    if sil_pen <= 0.2:
        strengths.append("ít khoảng lặng, nói trôi chảy")
    elif sil_pen > 0.6:
        weaknesses.append("nhiều khoảng lặng / nói chậm")
    if m["leading_silence"] > 0.4 or m["ending_silence"] > 0.6:
        weaknesses.append("có khoảng lặng dài đầu/cuối mẫu")
    if m["duration_seconds"] < 3.5:
        weaknesses.append("reference khá ngắn — nên 6–10 giây")
    if not strengths:
        strengths.append("giọng khá ổn để thử")
    if not weaknesses:
        weaknesses.append("không tìm thấy vấn đề rõ rệt")

    bars = {
        "noise": round(1.0 - noise_pen, 3),
        "volume": round(1.0 - vol_pen, 3),
        "silence": round(1.0 - sil_pen, 3),
        "clipping": round(1.0 - clip_pen, 3),
        "duration": round(_duration_score(m["duration_seconds"]), 3),
    }
    return ReferenceQuality(m, score, strengths, weaknesses, bars)
