# Vietnamese bridge options

## Result: no verified external bridge

No candidate found combines new synthetic identity, Vietnamese output, cross-lingual reference preservation, free local commercial-safe weights, and realistic 16 GB CPU operation.

| Bridge | Vietnamese | Cross-lingual transfer | Commercial posture | Result |
|---|---|---|---|---|
| Qwen3-TTS VoiceDesign/Base | No; official 10-language list excludes it | Within supported languages | Apache code and listed weights | Not a Vietnamese bridge |
| Spark-TTS | No; Chinese/English | Within stated scope | License/weights review | Not a bridge |
| CosyVoice 3 | No; official nine-language list excludes it | Within stated scope | Apache code; academic-purpose disclaimer | Not a bridge |
| Chatterbox Multilingual V3 | Not in official language list | Cross-language clone | Review release terms | Not a bridge |
| Vietnamese community forks | Claims vary | Usually reference cloning | NC, permission, or unknown | Not a new-identity path |

## Experimental bridge: installed VieNeu

Phase 30E inspected installed VieNeu 3.3.0: its reference preparation consumes a WAV, trims it, generates an x-vector and MOSS reference codes, and accepts neither a reference language nor transcript. Thus:

Qwen English synthetic WAV → VieNeu reference encoder → VieNeu Vietnamese output

is supported by the input path and technically plausible, but is not a published cross-lingual preservation claim. Identity-loss risk is HIGH/UNKNOWN. The English codec reference may inject prosody/phonetic context. Test Vietnamese tones, intelligibility, speaker drift, metallic/codec artifacts, breath/noise, and TTS-on-TTS character.

