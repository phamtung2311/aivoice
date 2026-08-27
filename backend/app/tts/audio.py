import numpy as np
import soundfile as sf
from typing import List


def edge_silence_samples(audio: np.ndarray, threshold: float = 0.003) -> tuple[int, int]:
    """Return leading/trailing near-silence without modifying generated audio."""
    samples = np.asarray(audio, dtype=np.float32)
    if samples.size == 0:
        return 0, 0
    amplitude = np.max(np.abs(samples), axis=1) if samples.ndim == 2 else np.abs(samples)
    audible = np.flatnonzero(amplitude > threshold)
    if audible.size == 0:
        return len(amplitude), len(amplitude)
    return int(audible[0]), int(len(amplitude) - audible[-1] - 1)


def join_audios(audio_list: List[np.ndarray], sr: int, gap_samples: List[int] | None = None) -> np.ndarray:
    """Join generated chunks without trimming/fading their speech edges.

    ``gap_samples`` contains one non-negative gap for each boundary.  It is
    intentionally an insertion-only operation: weak first/last phonemes remain
    untouched and the final chunk can never disappear during concatenation.
    """
    if not audio_list:
        return np.array([], dtype=np.float32)

    # Ensure a single channel layout.  Do not silently downmix a generated chunk.
    arrays = [np.asarray(a, dtype=np.float32) for a in audio_list]
    if any(a.ndim != arrays[0].ndim for a in arrays):
        raise ValueError("Generated chunks have incompatible channel layouts")
    if arrays[0].ndim not in (1, 2):
        raise ValueError("Generated chunks must be mono or multi-channel waveforms")
    if arrays[0].ndim == 2 and any(a.shape[1] != arrays[0].shape[1] for a in arrays):
        raise ValueError("Generated chunks have incompatible channel counts")

    gaps = list(gap_samples or [])
    if len(gaps) not in (0, len(arrays) - 1):
        raise ValueError("gap_samples must contain one value per chunk boundary")
    if not gaps:
        gaps = [0] * max(0, len(arrays) - 1)
    pieces = []
    for index, audio in enumerate(arrays):
        pieces.append(audio)
        if index < len(gaps):
            gap = max(0, int(gaps[index]))
            if gap:
                shape = (gap,) if audio.ndim == 1 else (gap, audio.shape[1])
                pieces.append(np.zeros(shape, dtype=np.float32))
    out = np.concatenate(pieces, axis=0)

    # clip to [-1,1]
    out = np.clip(out, -1.0, 1.0)
    return out


def resample_audio(audio: np.ndarray, orig_sr: int, speed: float) -> np.ndarray:
    """Change playback speed by resampling via linear interpolation.

    speed > 1.0 => faster playback (shorter array)
    speed < 1.0 => slower playback (longer array)
    """
    if speed == 1.0:
        return audio
    if audio.size == 0:
        return audio

    length = audio.shape[0]
    new_length = max(1, int(length / speed))
    # handle mono or multi-channel
    if audio.ndim == 1:
        old_idx = np.arange(length)
        new_idx = np.linspace(0, length - 1, new_length)
        return np.interp(new_idx, old_idx, audio).astype(np.float32)
    else:
        # interpolate each channel
        channels = []
        for ch in range(audio.shape[1]):
            old = audio[:, ch]
            old_idx = np.arange(length)
            new_idx = np.linspace(0, length - 1, new_length)
            channels.append(np.interp(new_idx, old_idx, old))
        return np.stack(channels, axis=1).astype(np.float32)


def save_wav(path: str, audio: np.ndarray, sr: int):
    if not isinstance(sr, int) or sr <= 0:
        raise ValueError("WAV sample rate must be positive")
    waveform = np.asarray(audio, dtype=np.float32)
    if waveform.size == 0:
        raise ValueError("Cannot write an empty WAV")
    sf.write(path, waveform, sr, subtype="PCM_16")
