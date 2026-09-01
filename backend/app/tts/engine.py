import os
import logging
import tempfile
from pathlib import Path
from typing import Optional, List

import numpy as np
import soundfile as sf

from .model import ModelLoader
from .text import preprocess_text, split_into_sentences, chunk_sentences
from .audio import edge_silence_samples, join_audios, resample_audio, save_wav
from .exceptions import (ModelLoadError, GenerationError, InvalidInputError)
from .prosody import PODCAST_PROSODY_VERSION, parse_prosody_script

logger = logging.getLogger(__name__)

QUALITY_OUTER_CHUNK_CHARS = 240


class TTSEngine:
    """Clean TTS Engine wrapper.

    Usage:
        engine = TTSEngine(model_name=..., device='cpu'|'cuda')
        path = engine.generate(text, voice='default', speed=1.0)
    """

    def __init__(self, model_name: Optional[str] = None, backend: Optional[str] = None, device: Optional[str] = None, cache_model: bool = True):
        self.model_name = model_name
        self.backend = backend
        self.device = device
        self._model = None
        self.cache_model = cache_model
        if cache_model:
            self._load_model()

    def _load_model(self):
        try:
            self._model = ModelLoader(backend=self.backend, model_name=self.model_name, device=self.device)
        except Exception as e:
            logger.exception("Failed to load model: %s", e)
            raise ModelLoadError(str(e))

    def get_voices(self) -> List[str]:
        if self._model is None:
            self._load_model()
        try:
            return self._model.get_voices()
        except Exception:
            return ["default"]

    def get_preset_names(self) -> List[str]:
        if self._model is None:
            self._load_model()
        try:
            return self._model.get_preset_names()
        except Exception:
            return list(self.get_voices() or ["default"])

    def get_user_voice_names(self) -> List[str]:
        if self._model is None:
            self._load_model()
        try:
            return self._model.get_user_voice_names()
        except Exception:
            return []

    def get_special_voice_names(self) -> List[str]:
        if self._model is None:
            self._load_model()
        try:
            return self._model.get_special_voice_names()
        except Exception:
            return []

    def get_voice_metadata(self, name: str) -> dict:
        if self._model is None:
            self._load_model()
        try:
            return self._model.get_voice_metadata(name)
        except Exception:
            return {}

    def install_special_voice(self, name: str, ref_audio: str, metadata: dict) -> str:
        if self._model is None:
            self._load_model()
        return self._model.install_special_voice(name, ref_audio, metadata)

    def add_saved_voice(self, name: str, ref_audio: str, description: str = "") -> str:
        if self._model is None:
            self._load_model()
        return self._model.add_saved_voice(name, ref_audio, description=description)

    def delete_saved_voice(self, name: str) -> bool:
        if self._model is None:
            self._load_model()
        return self._model.remove_saved_voice(name)

    def generate(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: float = 1.0,
        out_path: Optional[str] = None,
        max_chunk_chars: int = QUALITY_OUTER_CHUNK_CHARS,
        ref_audio: Optional[str] = None,
        emotion_tag: Optional[str] = None,
        denoise: bool = True,
        use_ref_codes: bool = True,
        # sampling params: if None -> do not forward, let underlying model use its defaults
        temperature: Optional[float] = None,
        top_k: Optional[int] = None,
        top_p: Optional[float] = None,
        repetition_penalty: Optional[float] = None,
        quality_diagnostics: bool = False,
    ) -> str:
        """Generate WAV for `text` and return path to file.

        - `speed` between 0.5 and 2.0
        - `voice` logical name
        """
        if not text or not text.strip():
            raise InvalidInputError("Empty text provided")
        if not (0.5 <= speed <= 2.0):
            raise InvalidInputError("Speed must be between 0.5 and 2.0")

        if self._model is None:
            self._load_model()

        clean = preprocess_text(text)
        sentences = split_into_sentences(clean)
        chunks = chunk_sentences(sentences, max_chars=max_chunk_chars)

        if not chunks:
            raise InvalidInputError("Text contains no speakable content")

        audios = []
        chunk_metrics = []
        sr = getattr(self._model, "sample_rate", 24000)

        # Prepare one native voice profile and reuse it for every generated chunk.
        ref_codes = None
        reference_voice = None
        if ref_audio is not None:
            try:
                speaker_emb, ref_codes = self._model.encode_reference(ref_audio, denoise=denoise, use_ref_codes=use_ref_codes)
                # VieNeu v3 resolves cloned identity from a voice profile dict.
                # Passing ref_codes as an extra kwarg is ignored by its public infer().
                reference_voice = {"speaker_emb": speaker_emb, "codes": ref_codes}
            except Exception as e:
                logger.exception("Failed to encode reference audio: %s", e)
                raise InvalidInputError(f"Invalid reference audio: {e}")

        for i, chunk in enumerate(chunks):
            try:
                # Build kwargs to forward: ModelLoader will only forward supported args
                call_kwargs = {}
                if emotion_tag is not None:
                    call_kwargs['emotion_tag'] = emotion_tag
                if denoise is not None:
                    call_kwargs['denoise'] = denoise
                if use_ref_codes is not None:
                    call_kwargs['use_ref_codes'] = use_ref_codes
                # forward sampling params only if explicitly provided (None means keep model default)
                if temperature is not None:
                    call_kwargs['temperature'] = temperature
                if top_k is not None:
                    call_kwargs['top_k'] = top_k
                if top_p is not None:
                    call_kwargs['top_p'] = top_p
                if repetition_penalty is not None:
                    call_kwargs['repetition_penalty'] = repetition_penalty

                audio = self._model.infer(
                    chunk,
                    voice=reference_voice if reference_voice is not None else voice,
                    **call_kwargs,
                )
            except Exception as e:
                logger.exception("Error generating chunk %s: %s", i, e)
                raise GenerationError(f"Failed to generate audio for chunk {i}: {e}")

            raw_audio = np.asarray(audio)
            if np.issubdtype(raw_audio.dtype, np.integer):
                audio = raw_audio.astype(np.float32) / np.iinfo(raw_audio.dtype).max
            else:
                audio = raw_audio.astype(np.float32)
            if audio.size == 0 or audio.ndim not in (1, 2):
                raise GenerationError(f"Generated chunk {i} has no valid waveform")
            leading, trailing = edge_silence_samples(audio)
            chunk_metrics.append({
                "index": i,
                "chars": len(chunk),
                "ending": chunk[-1:] if chunk else "",
                "duration_seconds": round(float(audio.shape[0]) / sr, 4),
                "peak": round(float(np.max(np.abs(audio))), 6),
                "rms": round(float(np.sqrt(np.mean(np.square(audio)))), 6),
                "leading_silence_ms": round(leading * 1000 / sr, 2),
                "trailing_silence_ms": round(trailing * 1000 / sr, 2),
            })

            audios.append(audio)

        # Only fill a measured silence deficit.  Existing model pauses are kept,
        # avoiding both rushed joins and doubled sentence silence.
        target_pause_ms = []
        for chunk in chunks[:-1]:
            ending = chunk.rstrip()[-1:] if chunk.strip() else ""
            target_pause_ms.append(130 if ending in ".!?…" else 75 if ending in ",;:" else 45)
        gaps = []
        for index, target_ms in enumerate(target_pause_ms):
            existing_ms = chunk_metrics[index]["trailing_silence_ms"] + chunk_metrics[index + 1]["leading_silence_ms"]
            gaps.append(max(0, int((target_ms - existing_ms) * sr / 1000)))
        joined = join_audios(audios, sr, gap_samples=gaps)

        # apply speed via resampling if needed (model may not support native speed)
        if speed != 1.0:
            joined = resample_audio(joined, sr, speed)

        out_dir = Path("output/tests")
        out_dir.mkdir(parents=True, exist_ok=True)
        if out_path is None:
            out_path = out_dir / f"tts_output_{abs(hash(text))%100000}.wav"
        else:
            out_path = Path(out_path)

        # save
        try:
            save_wav(str(out_path), joined, sr)
        except Exception as e:
            logger.exception("Failed to save WAV: %s", e)
            raise GenerationError(f"Failed to save WAV: {e}")

        # Diagnostics are opt-in and intentionally omit text/reference identity.
        self.last_generation_diagnostics = {
            "input_chars": len(clean),
            "outer_chunk_count": len(chunks),
            "chunks": chunk_metrics,
            "inserted_gap_ms": [round(gap * 1000 / sr, 2) for gap in gaps],
            "speed": speed,
            "final_duration_seconds": round(float(joined.shape[0]) / sr, 4),
            "final_peak": round(float(np.max(np.abs(joined))), 6),
            "final_rms": round(float(np.sqrt(np.mean(np.square(joined)))), 6),
        } if quality_diagnostics else None
        return str(out_path)

    def generate_prosody(
        self,
        tts_script: str,
        voice: Optional[str] = None,
        speed: float = 1.0,
        out_path: Optional[str] = None,
        **kwargs,
    ) -> str:
        """Generate user-marked segments and fill only pause-silence deficits.

        A marked boundary deliberately does not inherit the normal punctuation
        join target: its explicit target replaces it. Generated edge silence is
        retained, and only the remaining deficit is inserted.
        """
        if not (0.5 <= speed <= 2.0):
            raise InvalidInputError("Speed must be between 0.5 and 2.0")
        segments = parse_prosody_script(tts_script)
        audios = []
        sr = None
        with tempfile.TemporaryDirectory(prefix="aivoice_prosody_") as temp_dir:
            for index, segment in enumerate(segments):
                part_path = Path(temp_dir) / f"segment_{index}.wav"
                # Reuse the established clean-text path for every segment. This
                # guarantees markup itself can never be passed to VieNeu.
                self.generate(segment.text, voice=voice, speed=1.0, out_path=str(part_path), **kwargs)
                audio, part_sr = sf.read(str(part_path), dtype="float32", always_2d=False)
                if audio.size == 0:
                    raise GenerationError(f"Prosody segment {index} has no valid waveform")
                if sr is None:
                    sr = int(part_sr)
                elif sr != int(part_sr):
                    raise GenerationError("Prosody segments have incompatible sample rates")
                audios.append(np.asarray(audio, dtype=np.float32))

        assert sr is not None
        gaps = []
        for index, segment in enumerate(segments[:-1]):
            _leading_previous, trailing_previous = edge_silence_samples(audios[index])
            leading_next, _trailing_next = edge_silence_samples(audios[index + 1])
            existing_ms = (trailing_previous + leading_next) * 1000 / sr
            gaps.append(max(0, int((segment.pause_after_ms - existing_ms) * sr / 1000)))
        joined = join_audios(audios, sr, gap_samples=gaps)
        if speed != 1.0:
            joined = resample_audio(joined, sr, speed)

        if out_path is None:
            out_dir = Path("output/tests")
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / f"tts_prosody_{abs(hash(tts_script)) % 100000}.wav"
        try:
            save_wav(str(out_path), joined, sr)
        except Exception as e:
            raise GenerationError(f"Failed to save prosody WAV: {e}") from e
        self.last_generation_diagnostics = {
            "prosody_version": PODCAST_PROSODY_VERSION,
            "segment_count": len(segments),
            "explicit_pause_targets_ms": [segment.pause_after_ms for segment in segments[:-1]],
            "inserted_gap_ms": [round(gap * 1000 / sr, 2) for gap in gaps],
        }
        return str(out_path)
