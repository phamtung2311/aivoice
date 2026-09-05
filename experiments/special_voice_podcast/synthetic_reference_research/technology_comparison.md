# Technology comparison

| technology | voice_design | new_identity_without_human_reference | virtual_speaker | stable_identity | multiple_candidate_generation | direct_Vietnamese | cross_lingual | Vietnamese_bridge_possible | CPU | 16GB_RAM | Intel | Linux | Python | model_size | code_license | weights_license | commercial_risk | identity_loss_risk | can_feed_VieNeu | overall_fit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Qwen3-TTS 1.7B VoiceDesign | Yes | Yes | sampling only | archive generated WAV; no saved design token | Yes, descriptions/sampling; max 3 PoC | No | 10 official languages | Via VieNeu only; experimental | supported code path, slow | POSSIBLE_WITH_QUANTIZATION / RAM_RISK standard PyTorch | CPU plausible; no Iris Xe path verified | Yes | official fresh Python 3.12 | 4.52 GB | Apache-2.0 | Apache-2.0 listed | REVIEW_REQUIRED | HIGH / UNKNOWN | Yes, input path | Primary experimental |
| Spark-TTS 0.5B | attributes | Yes, constrained | Yes | not robustly documented | Yes | No | zh/en | No safe bridge | undocumented/slow | POSSIBLE | no Intel path verified | Yes | Python 3.12 | 0.5B class | recheck | review | REVIEW_REQUIRED | HIGH | WAV yes | No |
| Fish Speech S2 Pro | no proven stable design | no | no | reference only | no | unknown | multilingual claim | unknown | GPU-oriented | NOT_REALISTIC | unverified | Yes | varies | 4B | research | research | RESTRICTIVE | unknown | WAV yes | No |
| CosyVoice 3 | style only | no | no | reference/preset | no | No | nine languages | no | possible but GPU docs | RAM_RISK | unverified | Yes | Python 3.10 | 0.5B variants | Apache-2.0 | recheck | REVIEW_REQUIRED | HIGH | WAV yes | No |
| F5 Vietnamese fork | no | no | no | source reference | no | community | limited | irrelevant | possible | POSSIBLE | unknown | Yes | varies | varies | MIT upstream | commonly NC | NON_COMMERCIAL | HIGH | WAV yes | No |
| IndexTTS Vietnamese fork | no | no | no | source reference | no | community | limited | irrelevant | unknown | RAM_RISK | unknown | Yes | varies | ~1.5B | varies | permission reported | RESTRICTIVE | HIGH | WAV yes | No |

Classifications are conservative estimates, not benchmarks. No OpenVINO, ONNX, or Intel Iris Xe implementation is documented for selected Qwen VoiceDesign. Future work must use CPU only.

