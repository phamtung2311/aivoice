# PHASE 18 WORK REPORT

## Status

PASS

## Voice Lab status

```text
READY FOR REFERENCES
```

## Executive summary

Phase 18 chuyển AIVoice từ giao diện TTS local sang một Voice Lab nhỏ theo workflow `thử -> nghe -> chấm -> lưu -> so sánh`. Hệ thống hiện có runtime metadata có thể tái lập, evaluation corpus tiếng Việt cố định, experiment persistence bằng JSON local, rubric nghe chuẩn, branded voice manifest có bảo vệ chống tạo winner giả và UI tối thiểu để chạy từng sample.

Không có reference thật được cung cấp trong workspace. Vì vậy phase dừng đúng tại `READY FOR REFERENCES`, không chạy mass inference, không tạo audio thử vô nghĩa và không chọn branded voice winner.

## Runtime metadata

`/api/health` vẫn giữ field `model` cũ để backward compatibility và bổ sung metadata introspect từ runtime đang nạp:

```json
{
  "engine_library": "vieneu",
  "engine_version": "3.3.0",
  "runtime_family": "v3turbo",
  "runtime_class": "V3TurboVieNeuTTS",
  "runtime_backend": "onnx",
  "device": "cpu"
}
```

Version được đọc bằng package metadata với fallback graceful. Runtime class/family/backend/device được suy ra từ engine và model đang chạy, không hard-code class V3.

## Voice Lab architecture

- `backend/app/voice_lab.py` chứa schema, validation và helper persistence nhỏ gọn.
- `data/voice_lab/evaluation_corpus.json` là nguồn corpus/rubric duy nhất.
- `data/voice_lab/experiments.json` chỉ được tạo khi user generate/record sample thật.
- `data/voice_lab/branded_voice.json` chỉ được tạo khi user xác nhận winner.
- Generation dùng lại `/api/tts/clone`; không copy inference logic và không bypass semaphore.
- Các endpoint local mới: `GET /api/voice-lab/corpus`, `GET/POST /api/voice-lab/experiments`, `PATCH /api/voice-lab/experiments/{id}`, `GET /api/voice-lab/branded-voice`.

## Evaluation corpus

Corpus gồm đúng 6 câu tiếng Việt cố định:

1. Brand introduction cho identity, clarity và naturalness.
2. Call to action cho energy, clarity và ending.
3. Numbers/date/time/amount cho phát âm số tiếng Việt.
4. Punctuation cho pause và phrasing.
5. Narrative dài hơn cho prosody, consistency và identity drift.
6. Emotion sentence dùng cue native đã verified `[cười]`.

Corpus không được hard-code rải rác trong JavaScript và không random.

## Experiment persistence

Experiment record lưu ID, timestamps, runtime metadata, reference ID/label/file metadata, optional saved voice ID, canonical evaluation text ID/text, controlled round, repeat number, sampling parameters, cue, status, scores, notes và average score.

Record mới có `status = pending_evaluation`; sau khi user chấm đủ rubric, record chuyển thành `evaluated`. File JSON được ghi local bằng atomic replace và lock tiến trình. Audio, raw WAV, speaker embedding và acoustic codes không nằm trong experiment JSON.

## Listening rubric

Rubric dùng thang 1-5 cho 6 tiêu chí:

- Identity.
- Naturalness.
- Pronunciation.
- Prosody.
- Audio cleanliness, với 5 là sạch và không lỗi.
- Consistency.

UI yêu cầu chấm đủ 6 tiêu chí trước khi lưu. Average chỉ hỗ trợ so sánh; code không tự kết luận voice tốt nhất.

## Branded voice manifest

Schema manifest hỗ trợ name, saved voice ID, runtime/engine metadata, reference identifier, sampling, recommended speed 1.0, verified cues, timestamp, evaluation summary, notes và tối đa 2 style preset chuẩn bị cho Natural/Storytelling.

Helper từ chối lưu manifest nếu thiếu explicit user confirmation. Hiện chưa có `branded_voice.json` vì chưa có winner thật.

## Voice Lab UI

UI hiện có:

- Reference A/B/C độc lập, không bắt buộc đủ cả ba.
- File metadata gồm filename, format, duration nếu browser đọc được, size và status.
- Guidance 4-8 giây, một người nói, không nhạc nền, ít nhiễu, không clipping và giọng tự nhiên; WAV được ưu tiên nhưng clone WAV/MP3/M4A vẫn giữ nguyên.
- Evaluation sentence selector lấy từ backend corpus.
- Baseline và các round temperature/top_p/repetition được giới hạn theo kế hoạch controlled experiment.
- Generate one sample at a time, audio playback, rubric 1-5, notes, save evaluation và persistent history.
- Không có batch Cartesian grid, auto winner hoặc fake quality metric.

## Safety

- Backend đang chạy với `TTS_MAX_CONCURRENCY=1`.
- Voice Lab dùng lại clone endpoint và semaphore inference hiện tại.
- `speed` bị khóa ở 1.0 và `top_k` bị khóa ở 25 trong experiment đầu.
- Reference chỉ nằm trong browser memory khi generate; saved profile không lưu raw reference WAV.
- Experiment/report không chứa speaker embedding hoặc acoustic codes.
- Không có cloud ID, external API, network upload hay dependency mới.
- Không chạy real inference trong Phase 18 vì chưa có reference thật.

## Bugs found/fixed

- Sửa metadata health không đủ chính xác: field legacy `model` mô tả wrapper v2 được giữ để tương thích, đồng thời API nay report đúng engine library/version/runtime class/backend/device thực tế.
- Giữ nguyên fix clone identity Phase 17: native voice profile vẫn là `{speaker_emb, codes}` và không truyền sai `ref_codes` vào public infer call.
- Thêm validation để ngăn thay đổi speed/top_k ngoài methodology, score ngoài 1-5, round configuration không hợp lệ và manifest winner chưa được user xác nhận.

## Files created

- `backend/app/runtime_metadata.py`
- `backend/app/voice_lab.py`
- `data/voice_lab/evaluation_corpus.json`
- `tests/test_voice_lab.py`
- `diagnostics/phase18_manual_voice_lab_checklist.md`
- `diagnostics/phase18_work_report.md`

## Files modified

- `.gitignore`
- `backend/main.py`
- `frontend/index.html`
- `frontend/app.js`
- `frontend/styles.css`

Các thay đổi Phase 15-17 đang có trong worktree được giữ nguyên, không rollback/reset/restore.

## Tests

PASS:

```text
.venv/bin/python -m pytest -q tests/test_voice_lab.py tests/test_engine_reference.py
11 passed
```

Các test bao phủ runtime metadata, corpus load, pending persistence, parameter persistence, invalid score, evaluated record, speed/top_k/round validation, frontend contracts, manifest confirmation và native clone identity.

PASS thêm:

```text
python py_compile
node --check frontend/app.js
python -m json.tool data/voice_lab/evaluation_corpus.json
git diff --check
pytest --collect-only: 65 tests collected
```

Full/TestClient pytest vẫn gặp incompatibility đã biết giữa Python 3.14, Starlette TestClient và httpx trong environment này; lượt regression mở rộng được dừng khi không tạo output. Pure/direct tests và live HTTP contracts được dùng thay thế.

## Regression

Live backend sau reload:

```text
backend: 127.0.0.1:8000
frontend: 127.0.0.1:5173
TTS_MAX_CONCURRENCY=1
```

Đã xác nhận `/api/health`, `/api/voices`, Voice Lab corpus/experiments/branded-voice, frontend HTTP và CORS cho cả `localhost:5173` lẫn `127.0.0.1:5173`. Invalid legacy TTS sampling trả 422, upload thiếu file trả 422 và clone thiếu input trả 400 như kỳ vọng.

WAV/MP3/M4A clone, saved voice WAV, preview, advanced sampling và Blob history giữ architecture/test coverage Phase 17. Không chạy real clone regression để tránh CPU inference khi chưa có reference thật.

## Browser/manual verification

Browser automation không có instance khả dụng trong environment hiện tại. Checklist thao tác thực dụng đã được tạo tại `diagnostics/phase18_manual_voice_lab_checklist.md` để user xác minh bằng ba reference thật.

## Remaining issues

- Chưa thể đánh giá chất lượng, identity, prosody hoặc consistency nếu không có recording thật.
- Chưa có branded voice manifest vì user chưa nghe và chọn winner.
- Interactive browser/audio listening cần thực hiện thủ công theo checklist.
- Full TestClient suite còn phụ thuộc việc xử lý incompatibility environment đã biết; đây không phải blocker cho Voice Lab contracts đã test trực tiếp.

## What the user needs to provide next

```text
Reference A
Reference B
Reference C
```

Yêu cầu recording: 3 file WAV của cùng một speaker, mỗi file 4-8 giây, chỉ một người nói, giọng tự nhiên, không nhạc nền, ít tiếng ồn và không clipping.

## Recommended Phase 19

Sau khi user cung cấp reference thật, chạy Round 1 thủ công với baseline và tối đa 2 repeats/reference trên một tập câu ngắn. User nghe/chấm rubric và tự chọn reference tốt nhất trước khi lần lượt thử temperature, top_p và repetition penalty. Không chạy Phase 19 trong lượt này.
