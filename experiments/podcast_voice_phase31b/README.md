# Phase 31B — Podcast Voice Distinctiveness Experiment

This R&D experiment does not touch the `podcast_brand_beta` production profile.
It creates four blind files in `outputs/`, one using each purposeful direction:
intimate conversation, deep reflection, natural storytelling and clean long-form.
Every candidate uses the same identity, the same 35–50 second Vietnamese text,
the same sampling controls and speed 1.0. The variable is segmentation plus an
insertion-only pause profile.

The label mapping is separate under `mappings/private_mapping.json`. Do not
inspect it before listening. Each candidate chunk list is logged in `chunk_logs/`
and technical checks are written to `metrics/`.

## Listening questions

1. Có nghe thấy bốn bản khác nhau rõ không?
2. Bản nào giống người nói Podcast nhất?
3. Có bản nào quá công nghiệp, robot hoặc đọc bài không?

If the directions remain perceptually indistinguishable, stop parameter search:
the evidence points to the current reference/model conditioning rather than a
missing minor inference setting.
