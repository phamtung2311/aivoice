# PHASE 11 — VOICE QUALITY & PROSODY INVESTIGATION

> RESEARCH ONLY. Không sửa production, không commit.
> Mỗi kết luận đều có evidence từ source trong `.venv` / model cache.

---

## 1. Executive Summary

- **Model thực sự đang chạy**: dù project khai `model_name="pnnbao-ump/VieNeu-TTS-v2"`, nhưng `vieneu 3.3.0` luôn route qua `V3TurboVieNeuTTS` (xem section 2). Trên CPU chạy ONNX (`OnnxV3LiteEngine`), 48 kHz.
- **Voice system**: mỗi giọng = `speaker_emb` 192-d (x-vector) + `codes` pre-encoded. Preset có sẵn; cho phép tạo và **lưu voice profile thật** qua `add_voice`/`save_voices`.
- **Cloning**: reference → trim/denoise → `(speaker_emb, ref_codes)` (giới hạn `max_seconds=8.0`). Giọng/quyền đến từ speaker embedding; đây là kênh quyết định chất lượng lớn nhất.
- **Emotion**: special-token inline trong **phoneme stream**. Có 3 cue tài liệu: `[cười]/[chuckle]`, `[sigh]/[thở dài]`, `[clear throat]/[hắng giọng]`. Không có intensity slider.
- **Prosody**: model **KHÔNG có** pitch/duration/stress natively. Nhưng **pause/ngữ điệu** được **native** điều khiển qua ranh giới `para/sentence/minor` (0.35/0.18/0.04s) từ newline + dấu câu.
- **Sampling** (temp/top-k/top-p/rep-penalty): điều chỉnh **stochasticity generation**, không phải prosody. Không có seed param.
- **Biggest opportunity**: cải thiện chất giọng nguồn (reference/voice profile) + khai thác `emotion` cue + `gap/pause`. Chunking 400>256 làm mất continuity prosody giữa chunk — là bottleneck thật.

---

## 2. Actual Runtime Architecture

```
Frontend (index.html + app.js)
   ↓ HTTP  http://127.0.0.1:8000
FastAPI (backend/main.py)
   ↓ POST /api/tts | /api/tts/clone
TTSEngine.generate (backend/app/tts/engine.py)
   ↓ chunk ~400 chars → engine thực
ModelLoader (backend/app/tts/model.py)  → self._v = Vieneu(**kw)
   ↓
vieneu.sau.factory.Vieneu(mode="v3turbo")  ← DEFAULT. Bỏ qua model_name "v2"
   ↓
V3TurboVieNeuTTS (vieneu/v3turbo.py)   → self.sample_rate = 48_000
   ↓ (CPU/ONNX)
OnnxV3LiteEngine (vieneu/_v3_turbo_engine/onnx_runtime_lite.py)
   ↓ ONNX Runtime → 48k WAV
```

**Bằng chứng route-v2→v3:**
- `vieneu/__init__.py`: `from .factory import Vieneu`.
- `factory.py` `Vieneu(mode="v3turbo")` default → `return V3TurboVieNeuTTS(**kwargs)` → mọi model_name bị lượn qua V3Turbo.
- `ModelLoader` (backend) dùng `backend="onnx"` → ONNX path trong `V3Turbo.__init__`.

**Model artifacts (ONNX/CPU):**
- backbone: `pnnbao-ump/VieNeu-TTS-v3-Turbo/onnx_int8` (`vieneu_prefill.onnx`, `decode_step`, `acoustic_cached`).
- codec: `OpenMOSS-Team/MOSS-Audio-Tokenizer-Nano-ONNX` (MOSS audio tokenizer).
- speaker encoder/denoiser: same repo root.

## 3. Voice Capabilities

| Capability        | Status | Evidence | Notes |
| ----------------- | ------ | -------- | ----- |
| Preset voices     | NATIVE | `_load_v3_voices()` (v3turbo.py:178) | mỗi voice = speaker_emb 192-d + codes; `list_preset_voices()` |
| Reference voice   | NATIVE | `prepare_reference` → speaker_emb+codes | trim → denoise→44.1k → emb |
| Voice cloning     | NATIVE | `V3Turbo.infer(ref_audio=...)` / `_resolve_ref` | precedence: ref_audio > voice > default |
| Speaker embedding | NATIVE | `_speaker_anchor` (onnx_lite:217) 192-d x + Linear+LN | điều kiện toàn prompt |
| Voice profile     | NATIVE | `add_voice()` / `save_voices()` (v3turbo.py:248,295) | encode 1 lần, lưu JSON, dùng lại `voice=name` |

**Q2** Có 3 cách tạo giọng: preset name, reference audio (clone), speaker profile (add_voice).
**Q3** Preset khác nhau ở **speaker_emb + codes** (mỗi voice có model embedding riêng), không chỉ ref audio.
**Q4** Có — `ref_audio` tạo giọng mới, hoặc `add_voice` để đăng ký giọng mới.
**Q5** Có — `add_voice(...)` + `save_voices()` → lưu `(speaker_emb, codes)` vào JSON → dùng lại. **aivoice hiện chưa expose**.
**Q6** Giới hạn thật: `_MAX_REF_SECONDS = 8.0` (onnx_runtime_lite:50), `prepare_reference` trim > 8s; denoise → mono 44.1k; top_db=30 edgesilence. → aivoice (max 8s, 5MiB) khớp mốc 8s.

---

## 4. Emotion Capabilities

**Cơ chế (bằng chứng rõ):** `vieneu_utils/phonemize_text.py` — `_EMOTION_TAG_TO_K` và `phonemize_text_with_emotions()` chèn `<|emotion_k|>` **trực tiếp vào chuỗi phoneme** (prompt token qua `prompt_v3_turbo.build_prompt_2d`). Không phải embedding riêng, không có intensity.

| Feature            | Status | Evidence | Notes |
| ------------------ | ------ | -------- | ----- |
| Emotion tokens     | NATIVE | config emotion_0..7_token_id=8..15; phonemize maps 1,2,3 | inline trong phoneme |
| Number of emotions | PARTIAL | chỉ 3 cue tài liệu + `natural`(e0) | emotion_4..7 là token id, **không có tên/bằng chứng** |
| Emotion intensity  | NOT SUPPORTED | không có param intensity | token đơn không mix % |
| Emotion + cloning  | NATIVE (thông qua kênh) | emotion text + ref speaker khác kênh | kết hợp được |
| Emotion + voice    | NATIVE | emotion tag + preset speaker | khác kênh |

**Q11** — Truyền bằng cách **special text token trong phoneme prompt** (`build_prompt_2d`), không phải embedding/vectơ riêng.
**Q12 – intensity: NOT SUPPORTED** (only bật/tắt cue, không scale%).
**Q13** — Không hỗ trợ "giọng A + sad" như nút emotion riêng; chỉ kết hợp ref speaker (timbre) + 3 cue prosody.
**Q14 – prosody vs timbre**: emotion token = part-of-phonemes → ảnh hưởng ngữ điệu/rhythm/phát âm, **không phải** timbre (timbre từ speaker ref).

---
## 5. Prosody Capabilities

| Control | Status | Evidence | Notes |
| ------- | ------ | -------- | ----- |
| Pitch      | NOT SUPPORTED | no pitch param in `infer` sig | — |
| Intonation | INDIRECT | qua dấu câu/punctuation; punc_norm (sea-g2p) | sentence/punctuation |
| Duration   | NOT SUPPORTED | no duration param | `max_new_frames` implies length cap |
| Pause      | NATIVE | `V3_GAP_SILENCE={para:0.35,sentence:0.18,minor:0.04}` | newline/dấu câu → pause thật |
| Stress     | NOT SUPPORTED | no stress param | |
| Emphasis   | NOT SUPPORTED | no emphasis layout | |
| Rhythm     | INDIRECT | gap + punctuation | |
| SSML       | NOT SUPPORTED | no SSML path | |

**Silence native**: `core_utils.gaps_to_silence` maps gap type; `join_audio_chunks(..., silence_ps=...)`. `aivoice` không pass `silence_p` (default) nhưng model tự dùng gaps → pause do dấu câu đã có. Lưu ý: `silence_p`/`crossfade_p` trong signature `V3Turbo.infer` **không được dùng** trong nhánh `infer` đơn (join dùng gaps).

## 6. Text Control

- **Dấu câu & newline → prosody thật**: `punc_norm` (sea-g2p) ép câu ngắn về `.`, thêm `.` cuối; `normalize_to_chunks_v3_with_gaps` phân loại ranh giới `para/sentence/minor` → silence.
- **Emotion inline (không phải SSML)**: `[cười]`, `[chuckle]`, `[sigh]/[thở dài]`, `[clear throat]/[hắng giọng]` hoặc raw `<|emotion_k|>`. Đây là **cú pháp text hợp lệ duy nhất** để kiểm soát đọc; *không* phải SSML.
- **Pronunciation hint / markup khác**: NOT VERIFIED (không thấy). Không có WPS / custom markup ngoài emotion.
- **Pause control qua text**: có (newline=para 0.35s, dấu câu=sentence 0.18s).

---
## 6-7. Sampling & Sampling vs Prosody

Signature `V3Turbo.infer`: temperature (0.8), top_k (25), top_p (0.95), max_new_frames (300), repetition_penalty (1.2), repetition_window (64). aivo validate 0.1–1.5 / 1–100 / 0.5–1.0 / 1.0–2.0.

| Param | Effect |
| ----- | ------ |
| temperature | `logits/T`; ≤0 → **argmax (greedy, deterministic)** (ONNX `_sample`) |
| top_k | lọc k token top trước softmax (giới hạn explore) |
| top_p | nucleus: giữ tập token tích lũy p < top_p |
| repetition_penalty | ngừng lặp (giảm vòng lặp) |
| repetition_window | cửa sổ cho rep penalty |
| max_new_frames | trần số frame AR (gián tiếp length) |
| batch_size | GPU-only (bỏ qua trên CPU) |

### SAMPLING vs PROSODY
- **Sampling**: điều khiển **stochasticity phân phối chọn mã acoustic** — biến thể ngẫu nhiên của logits gốc, **KHÔNG phải** hệ thống prosody. Thấp temp → ổn định; cao → đa dạng nhưng có thể run rẩy, không phải "cảm xúc".
- **Prosody** (ngữ điệu/pause/emotion) đến từ: giọng reference (speaker_emb/prosody base) + text/normalization + emotion cue + gap/silence.
- **OVER**: không được quảng cáo sampling như prosody control. Không có source chứng minh.

## Determinism
- KHÔNG có `seed` param (`infer` sig + `_sample` dùng `np.random.choice`). Cùng text+params ⇒ output có biến đổi random.
- Deterministic chỉ khi `temperature<=0` (greedy argmax). Không nên expose seed UI (global np.random seed không an toàn concurrency).

## 7. Voice Cloning Deep Dive

Cơ chế:
```
ref_audio (wav)
 → _load_mono → (n,)
 → nếu > max_seconds=8.0 → trim
 → optional denoise (denoiser) → float32 @44.1kHz
 → speaker_encoder.embed → speaker_emb (192-d x-vector)
 → encode_ref_wav → ref_codes (n_vq MOSS codec)
 → (speaker_emb, ref_codes)
TTS: speaker anchor (192-d→H) + ref_codes nối làm row ref trong prompt (audio_ref_slot)
```

**Giới hạn thật** (`onnx_runtime_lite.prepare_reference`, `_MAX_REF_SECONDS=8.0`): trim theo giây (không hard-drop quá dài), denoise → 44.1k. aivoice (5MiB, 8s) nằm trong giới hạn này.

**Q7** — ref → encoded codes → conditioning (embed anchor + ref rows) → generation. Đúng pipeline.
**Q8 – cache lâu dài**: Có, `add_voice`+`save_voices` lưu `(embed, codes)` JSON → tái sử dụng không cần encode lại.
**Q9**: `speaker_emb` quyết định timbre/giọng/prosody base; `ref_codes` là conditioning cụ thể. accent/speed/style đến từ ref_codes + huấn luyện, không phải param. Emotion cue = text riêng.

---
## 8. Chunking & Continuity
- aivo `engine.py` chia ~400 chars theo câu, rồi gọi `model.infer(chunk)` với `max_chars` default=256 của v3 → mỗi `infer` là clean AR chạy lại từ đầu → per-chunk **KHÔNG** kế thừa context AR.
- speaker_emb + ref_codes giống nhau mọi chunk → giọng nhất quán.
- prosody continuity giữa chunk không đảm bảo (mỗi chunk reinfer, max_expected_frames cap riêng). Vì aivo cắt theo câu, ngắt ≈ ngắt câu → gap sentence giảm gãy.
- Cách giảm (đề xuất): mỗi chunk kết thúc punctuation rõ, tránh cắt giữa cụm, giữ ref tốt, cân nhắc pass `max_chars` lớn hơn để ít tái-chunk. Không tự sửa.

## 9. Audio Post-Processing
- `audio.py.resample_audio` (speed≠1) dùng **linear interpolation → thay pitch** (không pitch-preserving).
- `join_audios` + fade 10ms chống click (khác gap thật của model).
- **Speed native?** NOT — model không có param speed; aivo xử hậu.
- Để speed giữ pitch sau này: time-stretch hậu xử lý — nhưng thêm dependency; không tự làm.

---
## 10. Biggest Quality Bottlenecks
1. Reference/voice source quality — timbre+prosody base từ speaker/reference.
2. Chunk/continuity prosody (400→256 re-chunk, infer độc lập từng chunk).
3. Speed resample (linear → pitch shift).
4. Không deterministic/seed (`np.random`).
5. Chưa khai thác emotion cue + gap + `max_chars`/`repetition_window`.

## 11. Recommended Roadmap (không implement)
| Feature | Why | Impact | Difficulty/Risk | Type |
| ------- | --- | ------ | --------------- | ---- |
| P1. Voice profiles (`add_voice`/`save_voices`) | chất source giọng quan trọng nhất | High | Med/Low | NATIVE |
| P1. Expose emotion cues (`[cười]`,`[thở dài]`,`[hắng giọng]`) đúng tên | cải prosody/đọc tự nhiên | Med-High | Low | NATIVE |
| P2. Expose `max_chars`/newline/`gap` → kiểm soát nhịp | cải prosody + giảm gãy | Med | Low | NATIVE/INDIRECT |
| P2. Ref denoise/trim feedback trong cloning UX | ref tốt hơn | Med | Low | NATIVE |
| P3. Voice profile persistence (lưu JSON) | tiện | Med | Med | NATIVE |
| P4. Sampling experiment & deterministic preset | - | Low-Med | Low | tùy |

## 12. What We Should NOT Build
- Pitch/SSML/emphasis/intensity sliders — model không hỗ trợ (chỉ hậu xử lý, phức tạp).
- Seed UI — không có param; global np.random seed không an toàn.
- Nhiều concurrency — CPU-only.
- Tự đặt tên "emotion" cho token 4–7 — không có mapping, rủi sai.
- Auth/rate-limit phức tạp — local personal.

## 13. Evidence (file/function)
- `vieneu/factory.py`: `Vieneu(mode="v3turbo")` default.
- `vieneu/v3turbo.py`: `V3TurboVieNeuTTS` (sample_rate 48k), `_load_v3_voices`, `add_voice`, `save_voices`, `_resolve_ref`, `infer` sig.
- `vieneu_utils/phonemize_text.py`: `_EMOTION_TAG_TO_K`, `phonemize_text_with_emotions`, `normalize_to_chunks_v3_with_gaps`, `_merge_short_chunks`.
- `vieneu_utils/core_utils.py`: `V3_GAP_SILENCE`, `gaps_to_silence`, `join_audio_chunks`, `max_expected_frames`.
- `vieneu/_v3_turbo_engine/onnx_runtime_lite.py`: `prepare_reference` (`_MAX_REF_SECONDS=8.0`, denoise→44.1k), `infer` sig (no seed/pitch/speed), `_sample` (np.random, temp≤0→argmax), `_speaker_anchor`.
- `vieneu/_v3_turbo_engine/configuration_v3_turbo.py`: emotion_0..7 id=8..15.
- `backend/...` (aivoice): engine.py chunk 400 & pass sampling; main.py emotion map only `natural`.

## 14. Git state check
- Sau investigation: `git status --short` — chỉ có file mới `docs/PHASE_11_INVESTIGATION.md` (untracked). **Không commit.**

## 15. Final Recommendation (hướng duy nhất cho Phase 12)
> **Phase 12 — "Điều khiển giọng tự nhiên dựa trên NATIVE + prosody thật":** Mở rộng `aivoice`:
> (a) **Voice profile thật** (`add_voice`+`save_voices`) — cải thiện nguồn giọng (tác động chất lượng lớn nhất).
> (b) **Expose 3 emotion cue inline** (`[cười]`,`[thở dài]`,`[hắng giọng]`) theo đúng mapping.
> (c) **Tôn trọng prosody native**: pass `max_chars` hợp lý + tận dụng newline/dấu câu/gap để pause đúng.
> (d) **Thêm `repetition_window`/`max_new_frames`** mà source hỗ trợ (không giới hạn 4 sampling param hiện tại).

Không tạo pitch slider/SSML/intensity (model không có). Ưu tiên (a)+(b): tác động giọng+prosody lớn, CPU-only, ít rủi ro, không thêm dependency.

---