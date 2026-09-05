# Voice-design landscape

A valid system makes a new identity from description, latent, or documented virtual-speaker control. DSP changes are excluded.

| Technology | Cloning | Voice design | Virtual speaker | Cross-lingual identity | Vietnamese | Result |
|---|---|---|---|---|---|---|
| Qwen3-TTS 12Hz 1.7B VoiceDesign | Base sibling only | Yes: free-form described voice | Sampling only; no saved design token documented | Officially within 10 supported languages | No | Strongest factory |
| Spark-TTS 0.5B | Yes | Attribute creation | Yes: gender, pitch, rate | Chinese/English only | No | No Vietnamese bridge |
| Fish Speech S2 Pro | Reference/instructed TTS | No stable-design identity proven | No API documented | Multilingual claim | Unverified | Research license and 4B |
| CosyVoice 3 | Yes | Style instruction, not new identity | No | Nine-language set | No | No Vietnamese bridge |
| F5-TTS, GPT-SoVITS, IndexTTS, OpenVoice | Reference cloning | No | No | Varies | Community forks | Do not reopen: no new identity |
| StyleTTS2 | Style sampling, not a stable new speaker product | No | Insufficient | No production bridge | No | English-biased |

## Qwen evidence

The official Qwen repository lists the VoiceDesign model as 1.7B and limits it to Chinese, English, Japanese, Korean, German, French, Russian, Portuguese, Spanish, and Italian. The official workflow documents VoiceDesign creating a short reference then the Base model making a reusable clone prompt. This proves synthetic identity creation and stable reuse inside Qwen, not cross-model transfer.

Persist the selected synthetic WAV plus model revision, description, text, deterministic settings or seed if used, and checksum. Qwen documents no first-class saved VoiceDesign speaker token.

References: [Qwen official repository](https://github.com/QwenLM/Qwen3-TTS), [model card](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign), [Spark-TTS](https://github.com/SparkAudio/Spark-TTS), [Fish Speech](https://github.com/fishaudio/fish-speech), [CosyVoice](https://github.com/QwenAudio/CosyVoice).

