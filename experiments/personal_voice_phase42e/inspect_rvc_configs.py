#!/usr/bin/env python3
"""Static parameter-state audit of upstream-compatible RVC configurations."""

from __future__ import annotations

import gc
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1] / "personal_voice_phase42d" / "rvc_source"
sys.path.insert(0, str(ROOT))

from infer.module.models import (  # noqa: E402
    MultiPeriodDiscriminator,
    MultiPeriodDiscriminatorV2,
    SynthesizerTrnMs256NSFsid,
    SynthesizerTrnMs768NSFsid,
)


CONFIGS = (
    ("v1-32k", "configs/v1/32k.json", SynthesizerTrnMs256NSFsid, MultiPeriodDiscriminator),
    ("v1-40k", "configs/v1/40k.json", SynthesizerTrnMs256NSFsid, MultiPeriodDiscriminator),
    ("v2-32k", "configs/v2/32k.json", SynthesizerTrnMs768NSFsid, MultiPeriodDiscriminatorV2),
    ("v2-48k", "configs/v2/48k.json", SynthesizerTrnMs768NSFsid, MultiPeriodDiscriminatorV2),
)


def count(model) -> int:
    return sum(parameter.numel() for parameter in model.parameters())


def main() -> None:
    for name, relative_config, generator_type, discriminator_type in CONFIGS:
        config = json.loads((ROOT / relative_config).read_text())
        generator = generator_type(
            config["data"]["filter_length"] // 2 + 1,
            config["train"]["segment_size"] // config["data"]["hop_length"],
            **config["model"],
            is_half=False,
            sr=f"{config['data']['sampling_rate'] // 1000}k",
        )
        discriminator = discriminator_type(config["model"]["use_spectral_norm"])
        generator_parameters = count(generator)
        discriminator_parameters = count(discriminator)
        total = generator_parameters + discriminator_parameters
        print(
            f"{name}: G={generator_parameters}; D={discriminator_parameters}; "
            f"total={total}; fp32_weights_mib={total * 4 / 1048576:.2f}; "
            f"adam_moments_mib={total * 8 / 1048576:.2f}"
        )
        del generator, discriminator
        gc.collect()


if __name__ == "__main__":
    main()
