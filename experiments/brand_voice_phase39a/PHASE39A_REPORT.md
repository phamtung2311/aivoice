# Phase 39A — podcast brand voice identity reset

## 1. Execution status

`PASS` — exactly four intended, sequential, CPU-only Qwen VoiceDesign WAVs
were generated and validated. Quality/identity remains pending human QA.

## 2. Candidate 03 status

`RETIRED AS ACTIVE BRAND TARGET`

Candidate 03 remains untouched as historical evidence. Phase 38C OpenVoice
Candidate 03 identity transfer is recorded as `HUMAN FAIL`; no tuning followed.

## 3. Exact shared audition text

> When the noise fades, we begin to see what truly matters: not the answer we inherited, but the principle we choose to live by.

All four candidates spoke this identical English text.

## 4. Final VoiceDesign prompts

### A — Dark Reflective Mentor

> Design a fictional mature male podcast narrator with a medium-low register and a dark-neutral, slightly back-set resonance. Give the voice a close, intimate presence, restrained dry grain, moderate vocal weight, and firm clean consonants. Pitch movement is economical, with occasional subtle downward sentence endings; energy stays controlled, alert, and deliberately thoughtful. The acoustic signature should be compact dark resonance plus fine dry texture, recognizable without being gimmicky. Use neutral English pronunciation. Avoid sleepiness, excessive bass, theatricality, news or radio delivery, advertising polish, whispering, forced rasp, and regional accent.

### B — Weathered Essayist

> Design a fictional mature male podcast narrator in a lower-mid register with warm chest resonance and a lightly weathered surface. Use restrained natural roughness, slightly irregular organic texture, substantial but human vocal weight, and confident articulation that never becomes an announcer voice. His cadence should feel lived-in and reflective, with clear emphasis on the central idea and natural variation between phrases. The acoustic signature is warm chest body plus subtle weathering. Use neutral English pronunciation. Avoid forced rasp, trailer drama, commercial polish, radio or television news, heroic acting, whispering, sleepiness, exaggerated emotion, and regional accent.

### C — Quiet Analytical Philosopher

> Design a fictional male podcast narrator with a medium-low register, a dry matte timbre, narrower forward-focused resonance, and precise consonant edges. Keep vocal weight moderate, emotion restrained, and diction exact, while introducing slight natural asymmetry in pitch movement so the voice remains human and attentive. Use a close-mic intellectual presence and selectively weighted phrase endings. The acoustic signature is matte dryness plus precise forward focus. Use neutral English pronunciation. Avoid sterility, robotic rhythm, academic lecturing, corporate narration, advertising, newsreading, theatricality, whispering, exaggerated rasp, young-influencer energy, and regional accent.

### D — Warm Night Essayist

> Design a fictional mature male nighttime podcast narrator with a deep but natural register, warm-dark lower resonance, rounded vocal body, and smooth restrained richness. Let phrase onsets begin slightly soft, then gather into firm, focused words; maintain calm confidence, alert thoughtfulness, and intimate headphone presence. The acoustic signature is a soft-entry contrast against a solid warm-dark core, memorable but never cinematic. Use neutral English pronunciation. Avoid artificial bass, meditation or ASMR pacing, sleepiness, whispering, trailer narration, commercial or broadcast delivery, theatrical acting, over-polish, and regional accent.

## 5. Seeds and generation settings

- seeds: A `39001`, B `39002`, C `39003`, D `39004`;
- model: `Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign`, existing local assets;
- qwen-tts 0.1.1; transformers 4.57.3; PyTorch 2.13.0+cpu;
- Python 3.12.14; device CPU; dtype `torch.bfloat16`; eager attention;
- language `English`; non-streaming mode;
- do_sample true; temperature 0.9; top-k 50; top-p 1.0;
- repetition penalty 1.05;
- subtalker sampling true; temperature 0.9; top-k 50; top-p 1.0;
- max new tokens 8192.

No model download, grid, reroll, Vietnamese generation, conversion, or
post-processing occurred.

## 6. Generation metrics

| Candidate | Take | Generation | Duration | Format | Peak | RMS | Clipped | Peak RSS |
|---|---:|---:|---:|---|---:|---:|---:|---:|
| A | 1 | 525.519 s | 10.720 s | PCM16 mono, 24 kHz | 0.558594 | 0.080063 | 0 | 5065.141 MiB |
| B | 1 | 508.983 s | 10.800 s | PCM16 mono, 24 kHz | 0.722656 | 0.068657 | 0 | 5065.141 MiB |
| C | 1 | 440.842 s | 9.440 s | PCM16 mono, 24 kHz | 0.710938 | 0.054074 | 0 | 5065.141 MiB |
| D | 1 | 688.912 s | 8.960 s | PCM16 mono, 24 kHz | 0.531250 | 0.067635 | 0 | 5065.141 MiB |

Model load was 4.167 seconds. Total wall time was 2168.685 seconds
(36 minutes 8.685 seconds). All WAVs are non-empty, finite, frame-complete, and
free of severe clipping.

## 7. Human audition package

Exactly:

- `audio/candidate_A.wav`
- `audio/candidate_B.wav`
- `audio/candidate_C.wav`
- `audio/candidate_D.wav`

## 8. Human gate

Classify each as `NO`, `MAYBE`, or `YES`. Only a clear `YES — this voice has a
character I would actually want as my podcast identity` may progress.

`PODCAST BRAND IDENTITY CASTING: PENDING HUMAN QA`

Production, previous phases, and Candidate 03 historical assets remain
untouched. Downstream synthetic corpus rights remain `UNRESOLVED`.
