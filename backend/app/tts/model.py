import inspect
import logging
from typing import Dict, Optional

import numpy as np

from . import voice_store

logger = logging.getLogger(__name__)


class ModelLoader:
    """Abstraction around the underlying TTS model library (Vieneu).

    This keeps model import/load logic in one place and exposes a minimal API:
      - infer(text, voice, **kwargs) -> numpy audio
      - get_voices() -> list
      - save(audio, path)
      - sample_rate attribute
    """

    def __init__(self, backend: Optional[str] = None, model_name: Optional[str] = None, device: Optional[str] = None):
        try:
            from vieneu import Vieneu
        except Exception as e:
            raise RuntimeError("Missing dependency 'vieneu'. Install requirements and try again") from e

        self.backend = backend or "onnx"
        self.model_name = model_name or "pnnbao-ump/VieNeu-TTS-v2"
        self.device = device

        kwargs = {"backend": self.backend, "model_name": self.model_name}
        if device is not None:
            # pass device if library supports it
            kwargs["device"] = device

        try:
            self._v = Vieneu(**kwargs)
        except TypeError:
            # some versions may not accept device kwarg
            kwargs.pop("device", None)
            self._v = Vieneu(**kwargs)

        # sample rate fallback
        self.sample_rate = getattr(self._v, "sample_rate", 24000)

        # Names of built-in preset voices (captured BEFORE loading user-saved
        # voices so we can always distinguish presets from user profiles).
        self._preset_names: frozenset = frozenset()
        try:
            self._preset_names = frozenset(getattr(self._v, "_preset_voices", {}).keys())
        except Exception:
            self._preset_names = frozenset()

        # Restore any previously saved user voice profiles (no re-encoding needed).
        self._load_user_voices()

    # ── Voice profile operations (native VieNeu registration + our persistence) ──
    def get_preset_names(self):
        return sorted(self._preset_names)

    def get_user_voice_names(self) -> list:
        all_voices = set(self.get_voices() or [])
        return sorted(all_voices - set(self._preset_names))

    def _user_profiles(self) -> Dict[str, dict]:
        """Serialize currently-registered user voices to plain Python (vieneu JSON shape)."""
        profiles: Dict[str, dict] = {}
        try:
            all_v = getattr(self._v, "_preset_voices", {})
        except Exception:
            all_v = {}
        default_style = getattr(self._v, "default_style", None)
        for name in self.get_user_voice_names():
            v = all_v.get(name)
            if not isinstance(v, dict):
                continue
            profiles[name] = voice_store.serialize_profile(v, default_style)
        return profiles

    def _load_user_voices(self) -> None:
        profiles = voice_store.load_user_voices()
        try:
            all_v = getattr(self._v, "_preset_voices", {})
        except Exception:
            all_v = None
        if not isinstance(all_v, dict):
            return
        default_style = getattr(self._v, "default_style", None)
        for name, d in profiles.items():
            all_v[name] = voice_store.deserialize_profile(d, default_style)

    def add_saved_voice(self, name: str, ref_audio: str, denoise: bool = True, description: str = "") -> str:
        """Register a new user voice from reference audio using the native mechanism.

        Uses ``Vieneu.add_voice`` (encodes once: speaker_emb + ref_codes), then
        persists a user profile so later sessions restore it without re-encoding.
        """
        if name in self.get_preset_names():
            raise ValueError("Tên giọng trùng với giọng mặc định có sẵn.")
        if name in self.get_user_voice_names():
            raise ValueError("Tên giọng đã tồn tại.")
        add = getattr(self._v, "add_voice", None)
        if not callable(add):
            raise RuntimeError("Voice profile không được hỗ trợ bởi backend TTS.")
        add(name, ref_audio, denoise=denoise, save=False)
        try:
            profile = getattr(self._v, "_preset_voices", {}).get(name)
            if isinstance(profile, dict):
                profile["description"] = str(description).strip()[:200]
        except Exception:
            pass
        self._persist_user_voices()
        return name

    def remove_saved_voice(self, name: str) -> bool:
        """Delete a user voice only. Return False if it is a preset (not removable)."""
        if name in self._preset_names:
            return False
        rem = getattr(self._v, "remove_voice", None)
        if callable(rem):
            rem(name, save=False)
        self._persist_user_voices()
        return True

    def _persist_user_voices(self) -> None:
        voice_store.save_user_voices(self._user_profiles())

    def infer(self, text: str, voice: Optional[str] = None, **kwargs):
        # Try to pass kwargs (like speed) if supported
        try:
            sig = inspect.signature(self._v.infer)
            call_kwargs = {}
            # detect if underlying infer accepts **kwargs (VAR_KEYWORD)
            has_varkw = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())
            if "voice" in sig.parameters:
                call_kwargs["voice"] = voice
            for k, v in kwargs.items():
                if k in sig.parameters or has_varkw:
                    call_kwargs[k] = v

            return self._v.infer(text, **call_kwargs)
        except TypeError:
            # fallback: call without kwargs except voice if supported
            try:
                if voice is not None:
                    return self._v.infer(text, voice=voice)
                return self._v.infer(text)
            except Exception as e:
                raise

    def encode_reference(self, ref_audio: str, **kwargs):
        """Return a tuple (speaker_emb, ref_codes) by delegating to the underlying
        implementation when available. This allows callers to prepare a reference
        once and pass `ref_codes` into per-chunk `infer` calls to avoid reprocessing
        the reference for every chunk.
        """
        import inspect as _inspect

        enc = getattr(self._v, "encode_reference", None)
        if callable(enc):
            try:
                sig = _inspect.signature(enc)
                has_varkw = any(
                    p.kind == _inspect.Parameter.VAR_KEYWORD
                    for p in sig.parameters.values()
                )
                supported = {
                    k: v for k, v in kwargs.items()
                    if k in sig.parameters or has_varkw
                }
                return enc(ref_audio, **supported)
            except TypeError as e:
                logger.warning("encode_reference rejected kwargs (%s); retrying with defaults", e)
                try:
                    return enc(ref_audio)
                except Exception as inner:
                    logger.exception("encode_reference failed")
                    raise RuntimeError(f"Reference encoding failed: {inner}") from inner
            except Exception:
                raise

        # Fallback: some implementations expose `encode_reference` under other names
        # or provide `prepare_reference` on an engine attribute. Try common fallbacks.
        try:
            engine = getattr(self._v, "engine", None)
            if engine is not None and hasattr(engine, "prepare_reference"):
                return engine.prepare_reference(ref_audio, **kwargs)
        except Exception:
            pass

        raise RuntimeError("Reference encoding not supported by underlying TTS backend")

    def get_voices(self):
        # try common attributes/methods
        if hasattr(self._v, "get_voices"):
            try:
                vs = self._v.get_voices()
                return list(vs) if vs is not None else ["default"]
            except Exception:
                pass
        for attr in ("voices", "preset_voices", "preset_voices_list", "_preset_voices"):
            if hasattr(self._v, attr):
                try:
                    vs = getattr(self._v, attr)
                    # if it's dict-like, return keys
                    if isinstance(vs, dict):
                        return list(vs.keys())
                    return list(vs) if vs is not None else ["default"]
                except Exception:
                    continue
        # last resort: inspect attributes for named voices
        try:
            # some libs expose `list(self._v._preset_voices)` only via repr
            if hasattr(self._v, "_preset_voices"):
                vs = getattr(self._v, "_preset_voices")
                return list(vs)
        except Exception:
            pass

        return ["default"]

    def save(self, audio, path: str):
        # let underlying lib save if it supports
        if hasattr(self._v, "save"):
            try:
                return self._v.save(audio, path)
            except Exception:
                pass

        # otherwise write with soundfile
        try:
            import soundfile as sf
            sf.write(path, audio, self.sample_rate)
        except Exception as e:
            logger.exception("Failed to save audio: %s", e)
            raise
