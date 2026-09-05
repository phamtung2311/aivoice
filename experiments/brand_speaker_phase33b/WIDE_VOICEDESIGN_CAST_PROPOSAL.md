# Wide Qwen VoiceDesign Cast — proposal

Status: proposal only.  No audio has been generated, no model has been downloaded, and production has not been changed.

## Why the previous audition stops here

Phase 33A provides only weak, partial evidence: one user-identified cross-passage pair was verified as the same synthetic speaker, while the broader 12-clip grouping was too difficult to be useful.  The remaining private mapping remains unrevealed and the listening test is closed.  It does **not** establish a perceptually separated Brand Voice cast.

The next question is narrower and higher-value:

> Can deliberately *widely designed* synthetic identities remain clearly different after Qwen VoiceDesign → VieNeu Vietnamese cloning?

The differences must come from speaker identity (timbre, resonance, vocal weight, texture, and pitch character), not a different pace or pause pattern.

## Local asset audit

The required Phase 30 source-generation assets are already present locally:

| Asset | Local state |
| --- | --- |
| Qwen3-TTS-12Hz-1.7B-VoiceDesign checkpoint | Present; `model.safetensors` plus tokenizer/config, model directory about 4.3 GB |
| Phase 30 Qwen environment | Present; `.venv` about 1.6 GB |
| VoiceDesign generation scripts and prior prompts | Present in `experiments/special_voice_podcast/qwen_voice_factory/` |
| Prior Qwen source/reference and VieNeu conditioning artifacts | Present, read-only evidence only for this phase |
| CUDA GPU on this workstation | Not available (`nvidia-smi` is absent) |

No download is required to run this PoC on a compatible GPU machine.  Existing Phase 30 CPU measurements generated an approximately 7–9 second source reference in **308–670 seconds**, at a peak process RSS of about **5.1 GB**.  CPU generation is therefore excluded from the proposed experiment.

## Compute contract

Qwen's official guidance uses CUDA + BF16 and recommends FlashAttention 2 to reduce memory use; it does not publish a hard VRAM minimum for VoiceDesign 1.7B.  For this project, the operational requirement is:

| Requirement | PoC target |
| --- | --- |
| GPU | One NVIDIA CUDA GPU with **at least 12 GB VRAM**; 16 GB is preferred for margin |
| Precision | BF16-capable GPU; use the existing model checkpoint |
| Attention | FlashAttention 2 when compatible; otherwise validate eager/SDPA memory before generating |
| Host RAM | 16 GB minimum; 32 GB preferred |
| Disk already required | approximately 6 GB for the checkpoint and existing environment, plus less than 1 GB for the PoC outputs |
| Expected work | 4 short Qwen designs + 4 Vietnamese cloned probes; no training or fine-tuning |

The 12 GB number is a practical execution floor, not a claim of an official Qwen minimum.  Before any generation, the runner must verify CUDA availability, VRAM, BF16 support, and a successful one-model load; otherwise it stops without producing an incomplete cast.

## Smallest high-information PoC

Generate exactly **four** intentionally distant source identities, then clone each through the unchanged VieNeu path.  Every variable other than identity is fixed:

- one shared short source sentence for Qwen VoiceDesign (about 8 seconds);
- one shared neutral Vietnamese probe (20–25 seconds) for VieNeu;
- same VieNeu generation parameters, text segmentation, loudness normalization, and playback order;
- no user recording, no production profile update, no model training, and no candidate promotion.

This produces eight new files total: four Qwen reference sources and four Vietnamese probes.  It is the minimum set that can answer whether the bridge preserves an obvious identity spread.  It deliberately does not repeat the costly 12-clip cross-passage test until the four-way spread passes first.

### Candidate design lanes

All descriptions will explicitly prohibit exaggerated acting and will hold rate/pauses neutral.  The intended contrasts are:

| Lane | Designed identity characteristics |
| --- | --- |
| A — dark velvet | low-to-low-mid center, dense chest resonance, rounded dark timbre, smooth surface, substantial vocal weight |
| B — bright glass | higher and lighter pitch character, forward oral resonance, clean bright timbre, lean weight, crisp untextured onset |
| C — dry linen | mid pitch, dry/close resonance, low-bass restraint, lightly grainy natural texture, narrow and intimate body |
| D — warm stone | low-mid pitch, broad warm resonance, anchored heavy body, soft edge, stable matte texture without rasp |

These are four different identity hypotheses, not four delivery styles.  The subsequent listener check asks only whether all four Vietnamese probes are readily distinguishable on the same text.  If they are not, the experiment fails and no Brand Voice is selected.

## Go / no-go gates

1. **Technical gate:** each Qwen reference is 6–10 seconds, clean, non-clipped, and audibly follows its identity lane; otherwise regenerate only the failed lane after logging why.
2. **Bridge gate:** each VieNeu Vietnamese probe is clean, intelligible, and preserves a perceptibly different identity on identical text.
3. **Listener gate:** a short four-way blind ranking must show confident separation before any cross-passage stability test or production consideration.

No candidate will be called a keeper or connected to Podcast Beta during this PoC.

WAITING FOR USER APPROVAL OF WIDE VOICEDESIGN CAST
