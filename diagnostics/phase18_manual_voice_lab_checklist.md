# Phase 18 Manual Voice Lab Checklist

- [ ] Mở `http://127.0.0.1:5173` và xác nhận Health hiển thị màu xanh.
- [ ] Xác nhận runtime hiển thị VieNeu 3.3.0, V3TurboVieNeuTTS, ONNX và CPU.
- [ ] Chọn Reference A là WAV thật: cùng speaker, dài 4-8 giây, một người nói, không nhạc, ít nhiễu và không clipping.
- [ ] Chọn một câu trong evaluation corpus và giữ cấu hình Baseline: speed 1.0, temperature 0.8, top_k 25, top_p 0.95, repetition_penalty 1.2.
- [ ] Nhấn Generate sample đúng một lần và chờ hoàn tất trước khi thao tác tiếp.
- [ ] Nghe toàn bộ sample trong Voice Lab player.
- [ ] Chấm đủ 6 tiêu chí từ 1-5, nhập notes nếu cần, rồi nhấn Save evaluation.
- [ ] Reload trang và xác nhận experiment vẫn xuất hiện trong history với đúng điểm, notes và parameters.
- [ ] Nếu dùng saved voice, chọn lại voice đó ở workflow chính và xác nhận history Blob vẫn replay được mà không generate lại.
- [ ] Lặp lại thủ công với Reference B/C khi có file thật; không chọn winner nếu chưa nghe và so sánh các sample.
