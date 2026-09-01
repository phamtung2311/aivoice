"""Minimal adapter around the pinned community IndexTTS2 source.

It does not patch upstream files. Its only policy is to reject Qwen text emotion
for this low-VRAM PoC and to keep all inference calls serial.
"""
from __future__ import annotations

from pathlib import Path

from common import MODEL_DIR, configure_hf_environment


def load_low_vram_engine():
    configure_hf_environment()
    config_path = MODEL_DIR / "config.yaml"
    if not config_path.is_file():
        raise FileNotFoundError("Missing model/config.yaml; run asset verification first.")
    if (MODEL_DIR / "qwen0.6bemo4-merge").exists():
        raise RuntimeError("Qwen directory exists; low-VRAM initial PoC requires it to remain excluded.")

    # This import resolves only after the notebook installs the pinned community source.
    from indextts.infer_v2 import IndexTTS2
    return IndexTTS2(
        cfg_path=str(config_path),
        model_dir=str(MODEL_DIR),
        device="cuda:0",
        use_fp16=True,
        use_cuda_kernel=False,
        use_deepspeed=False,
        use_accel=False,
        use_torch_compile=False,
    )


def generate(engine, *, speaker: Path, text: str, output: Path, generation: dict, emotion_audio: Path | None = None, emotion_vector: list[float] | None = None):
    if emotion_audio is not None and emotion_vector is not None:
        raise ValueError("Choose one emotion mechanism per sample.")
    output.parent.mkdir(parents=True, exist_ok=True)
    return engine.infer(
        spk_audio_prompt=str(speaker),
        text=text,
        output_path=str(output),
        emo_audio_prompt=str(emotion_audio) if emotion_audio else None,
        emo_alpha=generation["emo_alpha"],
        emo_vector=emotion_vector,
        use_emo_text=False,
        emo_text=None,
        use_random=generation["use_random"],
        verbose=True,
        top_p=generation["top_p"],
        top_k=generation["top_k"],
        temperature=generation["temperature"],
        num_beams=generation["num_beams"],
        repetition_penalty=generation["repetition_penalty"],
        max_mel_tokens=generation["max_mel_tokens"],
    )
