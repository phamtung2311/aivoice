# Phase 44A — per-voice license and provenance audit

Access date: 2026-09-05. Primary source: https://huggingface.co/pnnbao-ump/VieNeu-TTS-v3-Turbo/blob/main/README.md (model card, licensing FAQ, preset roster). It states Apache-2.0 applies to shipped model, ONNX, tokenizer and bundled `voices_v3_turbo.json` speaker/reference assets; bundled-preset audio may be used in commercial/monetized content; and bundled speakers/rightsholders gave appropriate consent. Installed SDK/model revision: VieNeu 3.3.0 V3 Turbo, asset SHA256 `574e6acf03823c4cafdc43f106731ce5fce6de30228fe383831b8b9064ee0bd8`.

| Voice | Engine/model | Original released preset | Code | model/checkpoint + voice asset | output terms | Provenance | Verdict | Exact reason |
|---|---|---|---|---|---|---|---|---|
| Existing 01 | VieNeu V3 Turbo ONNX | Phạm Tuyên | Apache-2.0 | Apache-2.0 | Explicit commercial/monetized preset output allowed | bundled North male, natural; consent/rightsholder confirmation | COMMERCIAL-SAFE | All three commercial layers pass. |
| Existing 02 | VieNeu V3 Turbo ONNX | Minh Đức | Apache-2.0 | Apache-2.0 | Explicit commercial/monetized preset output allowed | bundled North male, news; consent/rightsholder confirmation | COMMERCIAL-SAFE | All three commercial layers pass. |
| Existing 03 | VieNeu V3 Turbo ONNX | Thanh Bình | Apache-2.0 | Apache-2.0 | Explicit commercial/monetized preset output allowed | bundled North male, storytelling; consent/rightsholder confirmation | COMMERCIAL-SAFE | All three commercial layers pass. |
| Existing 04 | VieNeu V3 Turbo ONNX | Quang Sơn | Apache-2.0 | Apache-2.0 | Explicit commercial/monetized preset output allowed | bundled Central male, natural; consent/rightsholder confirmation | COMMERCIAL-SAFE | All three commercial layers pass. |
| Existing 05 | VieNeu V3 Turbo ONNX | Xuân Vĩnh | Apache-2.0 | Apache-2.0 | Explicit commercial/monetized preset output allowed | bundled South male, natural; consent/rightsholder confirmation | COMMERCIAL-SAFE | All three commercial layers pass. |
| Existing 06 | VieNeu V3 Turbo ONNX | Thái Sơn | Apache-2.0 | Apache-2.0 | Explicit commercial/monetized preset output allowed | bundled South male, storytelling; consent/rightsholder confirmation | COMMERCIAL-SAFE | All three commercial layers pass. |
| Existing 07 | VieNeu V3 Turbo ONNX | Minh Triết | Apache-2.0 | Apache-2.0 | Explicit commercial/monetized preset output allowed | bundled South male, news; consent/rightsholder confirmation | COMMERCIAL-SAFE | All three commercial layers pass. |
| Existing 08 | VieNeu V3 Turbo ONNX | Đức Trí | Apache-2.0 | Apache-2.0 | Explicit commercial/monetized preset output allowed | bundled South male, audiobook; consent/rightsholder confirmation | COMMERCIAL-SAFE | All three commercial layers pass. |

No individual preset has a distinct restrictive term in the authoritative v3.3.0 shipped asset. These verdicts cover copyright/license and disclosed consent only; human listening remains the quality gate.
