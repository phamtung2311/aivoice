# Local free voice-factory comparison

| technology | new speaker without reference | voice description | Vietnamese support | CPU-only / 16 GB | license | recommendation |
|---|---|---|---|---|---|---|
| Qwen3-TTS VoiceDesign | Yes | Yes | Official language list excludes Vietnamese | Unknown; official examples emphasize CUDA/FlashAttention, 1.7B | Repo Apache-2.0; verify weights | Do not PoC |
| Spark-TTS | Yes, via gender/pitch/rate | Limited | Official Chinese/English only | Unknown | Apache-2.0 repo; verify weights | Do not PoC |
| Fish Speech | No reviewed arbitrary-speaker path | Not suitable here | Model-specific verification needed | Heavy/unknown | Research license; commercial agreement required | Reject |
| Chatterbox Multilingual | Default voice; custom identity needs audio prompt | No voice design | Official list excludes Vietnamese | CPU mode exists but PyTorch-heavy | MIT repo; verify weights | Reject |

Sources: [Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS),
[Spark-TTS](https://github.com/SparkAudio/Spark-TTS),
[Fish Speech license](https://github.com/fishaudio/fish-speech/blob/main/LICENSE),
[Chatterbox](https://github.com/resemble-ai/chatterbox).

No reviewed alternative combines reference-free identity creation, verified
Vietnamese support, clear commercial terms, and a credible local 16-GB CPU path.
