# Exact production model asset inventory

The offline v1 backup contains the exact Hugging Face cache trees required by the observed CPU ONNX runtime: `pnnbao-ump/VieNeu-TTS-v3-Turbo` (226 MiB) and `OpenMOSS-Team/MOSS-Audio-Tokenizer-Nano-ONNX` (87 MiB), total 313 MiB. File-level SHA256 values are in `MODEL_ASSET_MANIFEST.sha256`; cache refs preserve the locally observed revision rather than claiming upstream latest. The voice preset asset SHA256 is `574e6acf03823c4cafdc43f106731ce5fce6de30228fe383831b8b9064ee0bd8`.
