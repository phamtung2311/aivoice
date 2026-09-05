# Phase 40B — Freeze & validate Candidate B (Podcast Candidate B)

## 1. File/package baseline đã tạo

Canonical Candidate B baseline package (frozen, immutable):

`experiments/brand_voice_phase40b/baseline/PODCAST_CANDIDATE_B_BASELINE/`

| File | Purpose | Size |
|---|---|---|
| `speaker_emb.npy` | canonical Candidate B speaker embedding (float32 `[192]`) | 896 B |
| `reference_codes.npy` | canonical reference codes — Thanh Bình (Bắc, kể chuyện, int64 `[42,16]`) | 5 504 B |
| `manifest.json` | file-bytes SHA-256 + `array_sha256` + size; `immutable: true` | — |
| `freeze_record.json` | formula, hashes, VieNeu version, generation parameters, Phase 40A provenance | — |

Runner for reproducibility: `experiments/brand_voice_phase40b/baseline/run_freeze_baseline.py`.

Candidate B was NOT changed: the baseline reproduces the exact Phase 40A
float32 computation and matches the Phase 40A manifest hashes below.

## 2. Exact embedding formula + hashes

```text
speaker_emb_B = 0.75 × Phạm Tuyên + 0.25 × Thanh Bình
reference codes = Thanh Bình — Bắc — kể chuyện
```

Convex float32 blend, no renormalization (runtime contract: ONNX applies Linear
projection then LayerNorm internally).

| Item | SHA-256 |
|---|---|
| `speaker_emb` array (canonical identity) | `0c0cbc23228c89cfc27b0d109603b42b3fa0ca071cf728801455ec2cae752b53` |
| `speaker_emb.npy` file bytes | `09ce43e1facce2878df2e4bc78581213804d1beca638e6861f8794ba3f63986e` |
| emb norm | `10.962793350219727` |
| `reference_codes` array | `38964457925e5cf4362c90026e4bf552ddf1cf6acc35bc9555cd06c12603efb8` |
| `reference_codes.npy` file bytes | `fe8f8e3e1766a7954595fa3a355e46aca8c3e27be4aba4bb1db8d9b60a960aa5` |

Both array hashes match Phase 40A (`experiments/brand_voice_phase40a/manifest.json`
candidate B, `embedding_geometry.json`). VieNeu 3.3.0, voice asset
`voices_v3_turbo.json` SHA-256 `574e6acf03823c4cafdc43f106731ce5fce6de30228fe383831b8b9064ee0bd8`
(unchanged), ONNX/CPU, 48 kHz.

## 3. Voice library integration

`podcast_candidate_b` được thêm vào thư viện giọng như một voice thử nghiệm
(user có thể chọn như các voice khác), metadata:

```text
category: Podcast / Experimental
status: candidate
is_final_brand_voice: false
is_special: true
special_type: podcast_candidate
```

- `backend/app/tts/special_voices.py` — định nghĩa `podcast_candidate_b`, trỏ về
  baseline canonical `.npy` (chỉ dùng trong provisioning để tránh re-encode).
- `backend/app/tts/voice_store.py` — `PROFILE_METADATA_FIELDS` (+`status`,
  `is_final_brand_voice`), additive, không ảnh hưởng profile cũ.
- `backend/app/tts/model.py` — `get_voice_metadata` truyền thêm 2 trường mới.
- `backend/main.py` — `/api/voices` trả thêm `status`, `is_final_brand_voice`
  cho special voices (additive).
- `scripts/install_podcast_candidate_b.py` — provisioning mới đã chạy: verify
  baseline manifest (file + array hashes) rồi ghi `data/voices/voices.json`.

Kết quả provisioning: `podcast_candidate_b` có mặt trong `data/voices/voices.json`
với category/status/is_final_brand_voice đúng. Bản này là UI/library copy (emb
round 6 decimals theo contract `serialize_profile`, hash khác canonical — chỉ
dùng để UI chọn giọng), KHÔNG được dùng làm nguồn cho validation.

Các voice khác KHÔNG bị đổi: `podcast_brand_beta`, `review_film`, `tùng`,
`tùng 2`, `tùng 3` giữ nguyên hash (đã kiểm tra trước/sau).

## 4. Ba test texts (mới, chưa từng dùng)

1. **reflective / triết lý** (`texts/passage_1_reflective.txt`, 194 chars):
   > Người ta hay nghĩ rằng trưởng thành là khi mọi câu hỏi đều có câu trả lời. Nhưng thật ra, trưởng thành là biết đặt những câu hỏi tốt hơn, và đủ điềm tĩnh để lắng nghe câu trả lời của chính mình.

2. **explanatory / giảng giải** (`texts/passage_2_explanatory.txt`, 193 chars):
   > Một podcast không chỉ là giọng đọc. Điều tạo nên sức hút là nhịp điệu, sự chân thật, và những khoảng lặng đủ để người nghe tự suy nghĩ. Giọng tốt không át nội dung, mà đưa nội dung đến gần hơn.

3. **storytelling / kể chuyện có suy ngẫm** (`texts/passage_3_storytelling.txt`, 191 chars):
   > Tôi nhớ buổi chiều đứng trước sân ga, chờ một chuyến tàu không hẹn giờ. Lúc ấy tôi chưa biết rằng những chuyến muộn nhất thường dạy ta kiên nhẫn nhất, và sự kiên nhẫn ấy luôn có lý do của nó.

## 5. Generation settings (giữ NGUYÊN Candidate B, không tuning)

Cùng một config ổn định cho cả 3 đoạn (bằng chính `inference_defaults` của
Phase 40A / VieNeu defaults):

```text
denoise: True            use_ref_codes: True
temperature: 0.8         top_k: 25          top_p: 0.95
max_new_frames: 300      repetition_penalty: 1.2   repetition_window: 64
max_chars: 256           silence_p: 0.15    crossfade_p: 0.0
apply_watermark: True    batch_size: None
numpy_seed: 40002 (mỗi đoạn)
backend: ONNX / CPU / 48 kHz      speed: 1.0
```

Chỉ dùng canonical `.npy` từ baseline, không đổi embedding, không đổi codes,
không tune temperature/top-k/top-p/speed, không variants, không blend mới,
không post-processing.

## 6. Generation metrics

Model load: 5.902 s. Total wall: 23.415 s. Peak RSS: 1885.488 MiB.

| Passage | Duration | Gen s | RTF | Peak | RMS | Clipped (≥0.999) | WAV SHA-256 |
|---|---:|---:|---:|---:|---:|---:|---|
| 1 reflective | 10.000 s | 6.519 | 0.652 | 0.999969 | 0.107537 | 3 | `f22b76c28e24a240f7fa9c674c6132f2e7b60fd6a68a9fc4c5e59670bb8d3230` |
| 2 explanatory | 11.280 s | 5.514 | 0.489 | 0.838745 | 0.091577 | 0 | `81e62ea616e01534f409a1052babad53e2520500d9ba338773caa79fe1736fa5` |
| 3 storytelling | 10.160 s | 5.428 | 0.534 | 0.783020 | 0.099035 | 0 | `3b378b282c3954e3ff31eacc73a9c401913d5490b8b864ceb95c58cacd10f305` |

Tất cả đều PCM16 mono 48 kHz, frame-complete, finite. Đoạn 1 có 3/480 000 mẫu
(0.0006%) chạm full-scale digital (32767/32768 = 0.999969), không hard-clip —
nằm trong tolerance 1% của contract `valid_audio` (giống Phase 40A). Con số này
được ghi trung thực trong `manifest.json`; không áp post-processing.

## 7. Ba WAV để nghe

- `experiments/brand_voice_phase40b/audio/passage_1_reflective.wav`
- `experiments/brand_voice_phase40b/audio/passage_2_explanatory.wav`
- `experiments/brand_voice_phase40b/audio/passage_3_storytelling.wav`

Hướng dẫn nghe + tiêu chí đánh giá: `experiments/brand_voice_phase40b/HUMAN_REVIEW.md`.

## 8. Git / files changed

HEAD vẫn `a310b58ef58fb7df53e0af796ba066069f1c4049` (không commit; giữ nguyên
pattern worktree dirty của project). Các file dirty không liên quan không bị sửa.

Modified:
- `backend/app/tts/special_voices.py`
- `backend/app/tts/voice_store.py`
- `backend/app/tts/model.py`
- `backend/main.py`

New:
- `experiments/brand_voice_phase40b/` (baseline package, texts, audio, manifest,
  provenance, HUMAN_REVIEW, run scripts, report)
- `scripts/install_podcast_candidate_b.py`
- `tests/test_phase40b_podcast_candidate_b.py`

Local provisioned data (gitignored):
- `data/voices/voices.json` — thêm `podcast_candidate_b` (không đổi voice cũ)

Tests:
- Full `tests/` suite: **218 passed, 2 failed — cả 2 failure là pre-existing tại HEAD**,
  frontend test drift không liên quan Phase 40B (không file frontend nào bị sửa,
  `git status -- frontend/` sạch):
  - `tests/test_phase25_audio_studio.py` — test kỳ vọng `audio-studio.js?v=1.0.2`
    nhưng HTML đã commit ở HEAD dùng `v=1.4.1`.
  - `tests/test_phase30q3_timeline_transitions.py` — test kỳ vọng một chuỗi
    `setTimeout` cũ không còn trong standalone studio app tại HEAD.
- Phase 40B + các test liên quan (phase40b registry/API, voice profiles,
  Phase 22.1, Phase 29D, Phase 30Q): 31 passed.

## 9. Current gate

```text
CANDIDATE B CROSS-TEXT VALIDATION:
PENDING HUMAN QA
```

STOP — không phát triển tiếp Candidate B cho tới khi user nghe 3 đoạn và đánh giá.
Nếu cả 3 đoạn vẫn có character riêng và hợp podcast:
`CANDIDATE B = PROMISING BASELINE`.
Nếu chỉ đoạn Phase 40A hay: `CANDIDATE B = CONTRAST EFFECT / UNSTABLE`, dừng phát triển.
