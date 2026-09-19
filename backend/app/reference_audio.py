"""Decode uploaded reference recordings; callers own temporary-file cleanup."""

import logging
import os
import tempfile

from fastapi import HTTPException

logger = logging.getLogger(__name__)


def _ffmpeg_available() -> bool:
    """True when the system FFmpeg binary can be executed."""
    import shutil
    return shutil.which("ffmpeg") is not None


def _decode_audio_to_wav(src_path: str, dst_path: str, source_ext: str) -> None:
    """Decode any supported reference audio into a plain PCM WAV file.

    MP3 is decoded with soundfile (libsndfile ≥1.1 has native MP3 support).
    M4A/AAC requires FFmpeg. Raises RuntimeError with a user-safe message on
    any failure so callers can translate it into an HTTP error.
    """
    ext = source_ext.lower()
    try:
        if ext == ".mp3":
            import numpy as np
            import soundfile as sf
            data, sr = sf.read(src_path, dtype="float32", always_2d=False)
            if getattr(data, "ndim", 1) > 1:
                data = data.mean(axis=1)
            data = np.asarray(data, dtype=np.float32)
            if data.size == 0:
                raise ValueError("empty audio")
            sf.write(dst_path, data, sr, subtype="PCM_16")
            return
        if ext == ".m4a":
            if not _ffmpeg_available():
                raise RuntimeError(
                    "Máy chưa cài FFmpeg nên không thể chuyển đổi tệp M4A. "
                    "Hãy dùng tệp WAV hoặc MP3."
                )
            import subprocess
            proc = subprocess.run(
                ["ffmpeg", "-y", "-i", src_path, "-vn", dst_path],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if proc.returncode != 0 or not os.path.exists(dst_path) or os.path.getsize(dst_path) == 0:
                logger.warning("FFmpeg conversion failed: %s", (proc.stderr or "")[-500:])
                raise RuntimeError("Không thể giải mã tệp M4A.")
            return
        raise RuntimeError(f"Định dạng không được hỗ trợ: {ext}")
    except HTTPException:
        raise
    except RuntimeError:
        raise
    except Exception as e:
        logger.warning("Audio decode/conversion error (%s): %s", source_ext, e)
        raise RuntimeError("Tệp âm thanh không hợp lệ, bị hỏng hoặc không thể giải mã.")


def _prepare_reference_wav(upload_path: str, source_ext: str):
    """Return a filesystem path to a WAV file ready for the clone engine.

    For WAV uploads this is the uploaded file itself. For MP3/M4A a converted
    temporary WAV is produced; the caller owns its lifecycle and must remove it.
    """
    if source_ext == ".wav":
        return upload_path, None
    fd, converted = tempfile.mkstemp(prefix="clone_conv_", suffix=".wav")
    os.close(fd)
    try:
        _decode_audio_to_wav(upload_path, converted, source_ext)
    except Exception:
        try:
            os.remove(converted)
        except Exception:
            pass
        raise
    return converted, converted
