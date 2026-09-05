# Phase 19 Manual Round 1 Checklist

- [ ] Hard reload `http://localhost:5173` once so the current frontend assets and IndexedDB schema migration run.
- [ ] In Voice Lab, select Reference A, Reference B, and Reference C (4–8 seconds, same speaker).
- [ ] Select Reference A and generate one sample with the visible Round 1 baseline.
- [ ] Confirm the current-sample line identifies Reference A and Run 1; listen to it.
- [ ] Save an evaluation for A, then select Reference B and generate/listen/save an evaluation.
- [ ] In **Lịch sử thử nghiệm**, play A again after B exists; it must replay from stored audio without generating.
- [ ] Reload the page; confirm experiment scores/notes remain and replay A/B again from the experiment history.
- [ ] Generate a sample from a WAV reference, enter a unique voice name (and optional description), and click **Lưu giọng này**.
- [ ] Confirm the saved voice appears immediately in **Giọng đọc**, the preview list, and **Giọng đã lưu**; select it for main TTS.
- [ ] Try an MP3 reference, then an M4A reference: **Lưu giọng này** must remain disabled and explain that WAV is required.
- [ ] Create a main TTS result with the saved voice, then use main **Lịch sử → Nghe lại**. Confirm it plays without another generation request.
- [ ] Confirm older metadata-only main-history entries show **Chỉ lưu nội dung** and a readable disabled **Nghe lại** button.
- [ ] Toggle dark/light theme and verify all history text, active buttons, disabled labels, borders, and hover states remain clearly readable.
