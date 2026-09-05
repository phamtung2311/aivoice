# Phase 36I — Vietnamese reference bridge audit

## Canonical Candidate 03 package (unchanged)

- Qwen VoiceDesign canonical source: `experiments/brand_speaker_phase33c/baseline_anchor/BRAND_CANDIDATE_03_BASELINE/qwen_source.wav`
  - mono 24 kHz, 6.960 s, zero clipped samples
  - SHA-256: `3f3f5c6771ed437297ffdd89c5ea2aebd2d34dd531235ad5dd12e93bf18b5f06`
- exact English transcript: `A quiet evening settles over the city. I speak clearly, naturally, and without rushing.`
- VoiceDesign description: `A mature adult male voice with a medium-low register, dark-neutral back resonance, a controlled matte texture with restrained natural grain, and a firm broad vocal body. It must be clearly unlike a smooth bass narrator: neutral delivery, no forced rasp, no accent, no acting.`
- frozen VieNeu implementation assets: `speaker_emb.npy` (shape `[192]`) and `reference_codes.npy` (shape `[87, 16]`) in the same immutable baseline anchor.
- frozen best-known VieNeu checkpoint: `experiments/brand_voice_phase35b/BEST_KNOWN_BRAND_VOICE_CHECKPOINT/phase34_clip_c.wav`, with a matching copy of the frozen embedding/codes. It remains a checkpoint, not a replacement identity.

No user voice is present or proposed anywhere in this audit.

## Existing Vietnamese Candidate 03 WAVs

Low-energy figures below use the same waveform-only method as Phase 36F/36G: mono waveform, 20 ms RMS, 10 ms hop, -40 dBFS, 80 ms minimum region. They cannot certify pronunciation or identity; those remain listening judgments.

| Candidate | Provenance / exact transcript | Objective suitability | Decision |
|---|---|---|---|
| `baseline_anchor/.../phase33b_vietnamese_raw.wav` | Direct VieNeu transfer from frozen Candidate 03 embedding + paired codes. Exact transcript: `Có những ngày chúng ta không cần phải nói thật nhiều. Chỉ cần một giọng nói rõ ràng, một nhịp kể vừa phải, và vài phút bình yên để nghe lại điều mình đang nghĩ. Câu chuyện này bắt đầu rất đơn giản, rồi từ từ mở ra theo cách tự nhiên nhất.` | 14.240 s, 48 kHz mono, zero clipped; leading/trailing 0.10/0.23 s; 3.33 s internal low-energy, five major gaps. Too long for the 3–10 s reference guidance and carries the continuity artifact being investigated. | Reject as bridge reference. |
| `raw_outputs/Passage_1/variant_A.wav` | Frozen Candidate 03 embedding/codes; exact Passage 1 text in `run_refinement_matrix.py`. | 10.320 s, zero clipped; 2.18 s internal low-energy, four major gaps. | Reject: slightly above target duration and too fragmented. |
| `raw_outputs/Passage_1/variant_B.wav` | Same identity, Phase 33C natural sampling. | 10.320 s, zero clipped; 2.34 s internal low-energy, four major gaps. | Reject. |
| `raw_outputs/Passage_1/variant_C.wav` | Same identity, Phase 33C stable sampling. | 10.960 s, zero clipped; 2.45 s internal low-energy, four major gaps. | Reject. |
| `raw_outputs/Passage_1/variant_D.wav` | Same identity, Phase 33C signature sampling (0.82/25/0.97/1.15), the configuration carried into Phase 34. Exact transcript: `Có những buổi sáng, điều ta cần nhất chỉ là một câu chuyện mở đầu thật gần gũi. Hôm nay, chúng ta sẽ bắt đầu từ một điều nhỏ, rồi cùng đi chậm rãi qua phần còn lại của ngày.` | 10.800 s, 48 kHz mono, zero clipped; leading/trailing 0.17/0.25 s; 2.45 s internal low-energy, four major gaps. It has the strongest identity/configuration provenance among existing short candidates, but still fails clean-continuity suitability. | Reject as bridge reference. |
| Phase 34 / 35 / 35B long-form raw/checkpoint WAVs | Candidate 03 frozen conditioning and known scripts, but 18–49 s material; Phase 35 and 35B strategies were rejected by listening. | Phase 34 frozen checkpoint is 42.48 s with 11.52 s internal low-energy and 21 major gaps; too long and contains multi-chunk prosody. | Reject. |

The inspection found no existing Vietnamese WAV that is both a close 3–10 s reference and clean enough to avoid transferring the artifacts under study.

## Selected bridge candidate — one only

**Option B: generate one new synthetic Vietnamese bridge through the existing local VieNeu Candidate 03 path.**

- future bridge WAV: `experiments/brand_voice_phase36i/bridge_reference/candidate03_vietnamese_bridge_vieneu.wav`
- exact known transcript: `Hôm nay chúng ta cùng đi qua một câu chuyện ngắn với giọng kể rõ ràng và tự nhiên.`
- form: one neutral Vietnamese sentence, no names/numbers, no comma, single final period; intended to fall near 5–8 seconds at established Candidate 03 settings.
- direct conditioning source: immutable Candidate 03 `speaker_emb.npy` and paired `reference_codes.npy`.
- rendering: existing local CPU VieNeu path, same established Phase 34 sampling (`temperature=0.82`, `top_k=25`, `top_p=0.97`, `repetition_penalty=1.15`), speed 1.0, 240-character one-call ceiling, denoise false, ref codes true, seed 34001.

### Identity interpretation and risk

The bridge is a direct use of frozen Candidate 03 *VieNeu conditioning*, so it is the closest available synthetic way to preserve the canonical identity without user audio or speaker redesign. It is not a new canonical identity and does not replace the Phase 33C Qwen source.

There is unavoidable two-stage transfer risk: VieNeu can approximate Candidate 03 while imprinting its Vietnamese articulation/prosody; VietVoice may in turn clone both desired identity cues and residual VieNeu artifacts. The short, neutral, single-sentence bridge minimizes but cannot eliminate this risk. Any perceived identity retention remains a listening test against the canonical source.

## Future isolated VietVoice bridge test (not run)

After the bridge itself is explicitly generated and validated, run exactly one VietVoice test:

- reference WAV / transcript: selected Vietnamese bridge above, exact original transcript above
- target: `Một câu chuyện rõ ràng cần được kể liền mạch, có điểm nhấn đúng chỗ.`
- speed: **1.0** (restored to isolate reference language)
- seed 9527; NFE 32; fuse 1; 24 kHz; CPUExecutionProvider; same model/cache/preprocessing/pause configuration
- future output: `experiments/brand_voice_phase36i/output/vietvoice_candidate03_vietnamese_bridge_speed1.wav`

No VietVoice generation is authorized or performed by this audit.

## Prepared manual command (not run)

Because a new bridge is necessary, the future one-shot non-overwrite generator is prepared at `run_generate_candidate03_vietnamese_bridge.py`. Run it only after approving bridge generation:

```bash
cd '/home/tung/ai voice' && .venv/bin/python experiments/brand_voice_phase36i/run_generate_candidate03_vietnamese_bridge.py
```

It writes only the synthetic bridge asset and metrics within Phase 36I. It does not touch production or call VietVoice.
