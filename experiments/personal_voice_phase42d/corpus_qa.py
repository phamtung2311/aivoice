#!/usr/bin/env python3
"""Conservative, local-only corpus QA for the Phase 42D RVC feasibility gate."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import soundfile as sf


FRAME_SECONDS = 0.020
MIN_SILENCE_SECONDS = 0.35
EDGE_PAD_SECONDS = 0.12
MIN_VALID_SECONDS = 0.40
MIN_REVIEW_SECONDS = 1.00
MAX_PARENT_SECONDS = 12.0


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def dbfs(value: float) -> float:
    return 20 * math.log10(max(value, 1e-12))


def frame_rms(audio: np.ndarray, frame: int) -> np.ndarray:
    usable = (len(audio) // frame) * frame
    if not usable:
        return np.array([], dtype=np.float32)
    return np.sqrt(np.mean(np.square(audio[:usable].reshape(-1, frame)), axis=1))


def contiguous(mask: np.ndarray) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    start: int | None = None
    for i, value in enumerate(mask):
        if value and start is None:
            start = i
        elif not value and start is not None:
            out.append((start, i))
            start = None
    if start is not None:
        out.append((start, len(mask)))
    return out


def split_long(start: int, end: int, frame_values: np.ndarray, frame: int, sr: int) -> list[tuple[int, int, bool]]:
    """Prefer a low-energy point near each 12 s boundary; flag forced splits."""
    result: list[tuple[int, int, bool]] = []
    cursor = start
    max_frames = int(MAX_PARENT_SECONDS * sr / frame)
    while end - cursor > int(MAX_PARENT_SECONDS * sr):
        nominal = cursor + int(MAX_PARENT_SECONDS * sr)
        nominal_frame = nominal // frame
        lo = max(cursor // frame + 1, nominal_frame - int(1.5 * sr / frame))
        hi = min(end // frame - 1, nominal_frame + int(1.5 * sr / frame))
        if lo >= hi:
            point = nominal
            forced = True
        else:
            local = frame_values[lo:hi]
            point = (lo + int(np.argmin(local))) * frame
            forced = float(frame_values[point // frame]) > float(np.quantile(frame_values, 0.30))
        result.append((cursor, point, forced))
        cursor = point
    result.append((cursor, end, False))
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--segments", required=True, type=Path)
    parser.add_argument("--metadata", required=True, type=Path)
    args = parser.parse_args()
    source = args.input.resolve()
    args.segments.mkdir(parents=True, exist_ok=True)
    args.metadata.mkdir(parents=True, exist_ok=True)
    info = sf.info(source)
    if info.channels != 1 or info.samplerate != 40000:
        raise ValueError(f"expected mono 40 kHz PCM corpus WAV, got {info.channels} ch / {info.samplerate} Hz")
    audio, sr = sf.read(source, dtype="float32", always_2d=False)
    audio = np.asarray(audio, dtype=np.float32)
    if audio.ndim != 1 or audio.size == 0:
        raise ValueError("invalid mono audio")

    duration = len(audio) / sr
    peak = float(np.max(np.abs(audio)))
    rms = float(np.sqrt(np.mean(np.square(audio))))
    dc = float(np.mean(audio))
    clipped_samples = int(np.count_nonzero(np.abs(audio) >= 0.999))
    frame = int(FRAME_SECONDS * sr)
    frms = frame_rms(audio, frame)
    # Conservative adaptive gate: it marks low-energy pauses, never "bad speech".
    silence_threshold = max(0.0025, rms * 0.18)
    quiet = frms < silence_threshold
    long_quiet = np.zeros_like(quiet, dtype=bool)
    min_quiet_frames = int(MIN_SILENCE_SECONDS / FRAME_SECONDS)
    for start, end in contiguous(quiet):
        if end - start >= min_quiet_frames:
            long_quiet[start:end] = True
    silence_ratio = float(np.mean(quiet)) if quiet.size else 0.0
    long_silence_ratio = float(np.mean(long_quiet)) if long_quiet.size else 0.0

    # Between long quiet spans lies a candidate utterance. Preserve edge breath/pause.
    boundaries = contiguous(long_quiet)
    pieces: list[tuple[int, int, bool]] = []
    cursor = 0
    pad = int(EDGE_PAD_SECONDS * sr)
    for quiet_start, quiet_end in boundaries:
        end = max(cursor, quiet_start * frame + pad)
        if end > cursor:
            pieces.extend(split_long(cursor, end, frms, frame, sr))
        cursor = max(cursor, quiet_end * frame - pad)
    if cursor < len(audio):
        pieces.extend(split_long(cursor, len(audio), frms, frame, sr))

    segments: list[dict[str, object]] = []
    review_paths: list[str] = []
    for index, (start, end, forced_split) in enumerate(pieces, start=1):
        if end <= start:
            continue
        piece = audio[start:end]
        sec = len(piece) / sr
        item_peak = float(np.max(np.abs(piece)))
        item_rms = float(np.sqrt(np.mean(np.square(piece))))
        item_dc = float(np.mean(piece))
        item_clipped = int(np.count_nonzero(np.abs(piece) >= 0.999))
        clip_ratio = item_clipped / max(1, len(piece))
        reasons: list[str] = []
        if sec < MIN_VALID_SECONDS:
            status = "REJECT_TECHNICAL"
            reasons.append("duration_below_0.40s")
        elif item_rms < 0.001:
            status = "REJECT_TECHNICAL"
            reasons.append("near_silence")
        elif clip_ratio > 0.001:
            status = "REJECT_TECHNICAL"
            reasons.append("severe_clipping_over_0.1pct_samples")
        else:
            status = "AUTO_PASS"
            if sec < MIN_REVIEW_SECONDS:
                reasons.append("short_for_training_review")
            if item_rms < 0.004:
                reasons.append("extremely_quiet_review")
            if item_peak >= 0.99 or abs(item_dc) >= 0.015:
                reasons.append("level_or_dc_review")
            if forced_split:
                reasons.append("forced_low_energy_split_review")
            if reasons:
                status = "REVIEW"
        filename = f"seg_{index:04d}.wav"
        path = args.segments / filename
        sf.write(path, piece, sr, subtype="PCM_16")
        record = {
            "id": f"seg_{index:04d}", "source": str(source),
            "start_seconds": round(start / sr, 6), "end_seconds": round(end / sr, 6),
            "duration_seconds": round(sec, 6), "path": str(path.resolve()),
            "sha256": digest(path), "sample_rate": sr, "channels": 1,
            "peak": item_peak, "rms": item_rms, "rms_dbfs": dbfs(item_rms),
            "dc_offset": item_dc, "clipped_samples": item_clipped,
            "clip_ratio": clip_ratio, "qa_status": status, "qa_reasons": reasons,
        }
        segments.append(record)
        if status == "REVIEW":
            review_paths.append(str(path.resolve()))

    totals = {status: sum(float(x["duration_seconds"]) for x in segments if x["qa_status"] == status)
              for status in ("AUTO_PASS", "REVIEW", "REJECT_TECHNICAL")}
    summary = {
        "input": str(source), "input_sha256": digest(source), "sample_rate": sr,
        "channels": 1, "raw_duration_seconds": duration, "raw_minutes": duration / 60,
        "peak": peak, "rms": rms, "rms_dbfs": dbfs(rms), "dc_offset": dc,
        "clipped_samples": clipped_samples, "clip_ratio": clipped_samples / len(audio),
        "silence_threshold": silence_threshold, "frame_seconds": FRAME_SECONDS,
        "silence_ratio": silence_ratio, "long_silence_ratio": long_silence_ratio,
        "segment_policy": {"min_silence_seconds": MIN_SILENCE_SECONDS, "edge_pad_seconds": EDGE_PAD_SECONDS,
                           "min_valid_seconds": MIN_VALID_SECONDS, "max_parent_seconds": MAX_PARENT_SECONDS},
        "counts": {status: sum(1 for x in segments if x["qa_status"] == status)
                   for status in ("AUTO_PASS", "REVIEW", "REJECT_TECHNICAL")},
        "duration_seconds_by_status": totals,
        "segments": segments,
    }
    (args.metadata / "corpus_qa_manifest.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (args.metadata / "review_candidates.m3u").write_text("#EXTM3U\n" + "\n".join(review_paths) + ("\n" if review_paths else ""), encoding="utf-8")
    print(json.dumps({key: summary[key] for key in ("raw_minutes", "peak", "rms_dbfs", "dc_offset", "clip_ratio", "silence_ratio", "long_silence_ratio", "counts", "duration_seconds_by_status")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
