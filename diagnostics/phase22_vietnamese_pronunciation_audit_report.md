# PHASE 22 VIETNAMESE PRONUNCIATION AUDIT REPORT

## Status

PARTIAL → code audit + empirical library probe complete; conservative normalization fix shipped; final root-cause confirmation requires the user's controlled listening test (the agent cannot hear audio and ran no model inference).

## User symptom

Vietnamese “người” is sometimes pronounced with a broken syllable, heard as “ngờ i” / missing vowel nucleus. Occurrence: intermittent.

## Text path

Verified end-to-end; no text mutation before G2P:

```text
frontend textarea (charset="utf-8")
→ JSON.stringify UTF-8 payload — text is never URI-encoded (no encodeURIComponent(text) anywhere)
→ FastAPI pydantic str (TTSRequest / CloneForm — plain str fields, untouched)
→ preprocess_text()  [NOW: normalize_vi_input first — Phase 22]
→ split_into_sentences() → chunk_sentences(max_chars=240, Phase 20)
→ TTSEngine.generate: one {speaker_emb, codes} profile reused for EVERY chunk (Phase 17 fix intact)
→ ModelLoader.infer → vieneu.v3turbo.V3Turbo.infer
→ per chunk: phonemize_text_with_emotions(chunk)  [no pre-transform inside Vieneu]
→ sea_g2p 0.9.0 SEAPipeline.run → Normalizer(Rust) + G2P(Rust) → phonemes
```

No user text is logged anywhere in this path; the new probe script uses only fixed corpus words.

## Unicode findings

- Repo layers contained NO Unicode normalization before Phase 22.
- Library stack has zero `unicodedata`/NFC/NFD usage: `vieneu/`, `vieneu_utils/`, `sea_g2p/` (Rust core `sea_g2p_rs` + binary dict; not modified).
- Empirical probe (no model load): for 11 corpus words + 2 sentences, sea_g2p 0.9.0 produces IDENTICAL normalized text and phonemes for NFC vs NFD. “người” → `ŋˈyə2j.` in both forms. NFD-at-G2P hypothesis: RULED OUT for these inputs. NFC composition still added upstream as safety/predictability.
- Measured invisible-character behavior (the real find):
  - `ng\u200Bười` (ZWSP inside word) → sea_g2p normalizes to `ng ười` (REAL SPACE) → phonemes `ˌɛndʒˈiː ˈyə2j.` — the orphan `ng` is read with the ENGLISH G letter sound. This is exactly the reported “ngờ i” failure pattern.
  - Soft hyphen U+00AD inside word: same split behavior.
  - NBSP / narrow-NBSP between words: safely converted to plain space.
  - ZWJ inside word: silently dropped (safe).
  - `Normalizer.audit()` reports NOTHING for any of these — silent loss; audit alone cannot guard this case.
- Pre-patch, our `preprocess_text()` passed ZWSP/soft-hyphen/zero-width characters through untouched.

## Preprocessing findings

Pre-fix `preprocess_text()` only collapsed `\t\r` and ASCII space runs; it did not map NBSP-family characters or remove zero-width/soft-hyphen artifacts. No regex touched diacritics; no `.encode/.decode` or case-transform side effects exist in the TTS text path.

## Chunking findings

`split_into_sentences()`/`chunk_sentences()` cut on whitespace/punctuation only; `str.split()` cannot split inside a word and combining sequences stay attached to their base character. Regression test added: a 30×“mọi người” sentence chunked at `max_chars=12` reassembles identically with every token intact. Outer 240-char limit and Phase 20 semantics unchanged. For the single-sentence user test exactly one chunk is produced, so chunk boundaries are not the current symptom path; a theoretical mid-syllable risk exists only inside Vieneu’s phoneme-space splitter for very long inputs — noted as observation, not a defect claim.

## VieNeu phonemizer findings

- `vieneu.v3turbo` calls `phonemize_text_with_emotions(chunk)`; no text transformation inside Vieneu before phonemization.
- `vieneu_utils/phonemize_text.py` delegates entirely to `sea_g2p` (`SEAPipeline`, `G2P`, `Normalizer`, always-on `punc_norm`, LRU cache per exact string).
- sea_g2p core is compiled Rust + `sea_g2p.bin`; behavior probed empirically (above). No package modifications.
- Direct evidence: `Mọi người đang ở đây.` → `mˌɔ6j ŋˈyə2j ɗˌaːŋ ˈəː4 ɗˈəɪ.` — every syllable has a proper vowel nucleus; the phonemizer is CORRECT for clean NFC/NFD text.

## Preset vs saved voice diagnostic readiness

Protocol prepared (corpus + exact sentences), not executed — agent generated no audio:

- Same sentence `Mọi người đang ở đây.`: preset control (any entry under “Giọng mặc định” — installed model presets, e.g. “Trúc Ly”; the prompt template said “Adam”, use whatever preset your build lists) vs saved cloned voice, plus one repeat run on the saved voice, then two more saved-voice sentences.
- Decision rule: preset wrong ⇒ text/phonemizer/model side; preset right + saved wrong ⇒ conditioning/reference/sampling side; wrong on repeat 1 but right on repeat 2 ⇒ stochastic contribution.

## Root cause candidates

Ranked by evidence:

1. **Invisible zero-width/soft-hyphen separators in input, split by sea_g2p into real spaces** — REPRODUCED OFFLINE (`ng\u200Bười` → `ng ười` → English-letter “ng” phonemes). Strongest match to the symptom; our layer previously passed these through. Fix shipped this phase.
2. **Model stochasticity on the saved voice** — symptom is intermittent; phoneme stream verified correct, so AR sampling during acoustic decoding can still render an imperfect syllable. Discriminated by the repeat-run listening test.
3. **Saved-voice reference conditioning breadth** — identity from 4–8 s clips is phonetically narrow by design; same `{speaker_emb, codes}` is provably reused per chunk (Phase 17 path re-verified). Documented, no change made.
4. **Unicode NFD decomposition** — RULED OUT empirically at G2P (identical outputs); NFC still applied upstream as hygiene.
5. **Our chunker splitting tokens** — RULED OUT (reassembly regression test).

## Fixes made

- **New** `backend/app/tts/normalize_vi.py` — conservative input hygiene, no new dependency:
  - NBSP / FIGURE / narrow-NBSP → plain space;
  - ZWSP / ZWNJ / ZWJ / WORD JOINER / BOM / SOFT HYPHEN → removed;
  - Unicode NFC composition;
  - `audit_invisible_characters()` dev/test helper;
  - idempotent; never folds diacritics (`người` stays `người`), never alters letters/numbers/case.
- `backend/app/tts/text.py` — `preprocess_text()` calls `normalize_vi_input()` FIRST, then the unchanged whitespace cleanup (regexes pre-compiled). Pipeline order and Phase 20 semantics preserved.
- Dev-only probe `scripts/phase22_pronunciation_probe.py` kept for future rounds (controlled words only; no model load).
- No hard-coded “người” replacement anywhere; no pronunciation dictionary added (clean-text phonemization is verified correct; evidence does not prove a library defect).

## Pronunciation corpus

`data/voice_lab/pronunciation_corpus.json` — focus word `người`; 15 words (rhyme family -ươi/-ười, ượu patterns, dense-diacritic set nguyễn/nghiêng/khuỷu/thuở); fixed probe settings `speed=1.0, temperature=0.8, top_k=25, top_p=0.95, repetition_penalty=1.2`; manual-listening protocol with report fields. Diagnostics only — never auto-submitted to history/experiments.

## Files modified

- `backend/app/tts/text.py`

## Files created

- `backend/app/tts/normalize_vi.py`
- `data/voice_lab/pronunciation_corpus.json`
- `tests/test_phase22_vietnamese_text_audit.py`
- `scripts/phase22_pronunciation_probe.py`
- `diagnostics/phase22_vietnamese_pronunciation_audit_report.md`

(Phase 21.1 workspace changes from the previous phase remain present, uncommitted, untouched.)

## Tests

```text
python -m py_compile backend/app/tts/text.py backend/app/tts/normalize_vi.py: PASS
PYTHONPATH=. .venv/bin/pytest -q tests/test_phase22_vietnamese_text_audit.py → 11 passed
PYTHONPATH=. .venv/bin/pytest -q tests/ → 112 passed, 1 warning (pre-existing Starlette deprecation)
```

New coverage: NFC idempotence; NFD→NFC composition; accents never folded; zero-width/soft-hyphen removal inside words; NBSP→plain space; chunker token integrity with combining sequences (`người` never split); sentence splitter accent preservation; corpus load + fixed probe settings; frontend UTF-8 contract (charset meta + JSON.stringify payload, no URI-encoding); sea_g2p NFD≡NFC phonemizer equivalence + expected `ŋ…` syllable representation (skipped if sea_g2p is unavailable); proof that sea_g2p audit is blind to the ZWSP case while the new app-layer fix neutralizes it before G2P.

## Regression

```text
History replay: PASS (untouched) · Voice Lab: PASS · Save Voice WAV/MP3/M4A: PASS
Clone endpoint /api/tts/clone: PASS · speaker_emb + codes per-chunk reuse: PASS (Phase 17)
Phase 20 chunk fixes: PASS (240-char outer, token-safe boundaries retained)
Phase 21 temperature workflow + preferred-candidate config: PASS
CORS + TTS_MAX_CONCURRENCY=1: PASS · Phase 21.1 UI cleanup: intact
```

No dependency changed. No model/phonemizer package modified. Nothing committed/pushed/reset.

## USER MUST TEST

```text
1. Restart backend (backend code changed), hard reload localhost:5173.
2. Preset voice: “Mọi người đang ở đây.” → correct/wrong
3. Saved voice run 1: same sentence → correct/wrong
4. Saved voice run 2: same sentence → correct/wrong
5. Saved voice: “Người Việt Nam luôn yêu tiếng Việt.” → correct/wrong
6. Saved voice: “Tôi cười với mọi người.” → correct/wrong
Report which exact word is wrong in each wrong run.
```

## Remaining issues

- Root-cause confirmation is gated on the listening results above (stochastic vs conditioning vs residual text issue).
- sea_g2p remains a black-box Rust binary: no lower-level fix is possible inside it; only upstream input hygiene (now in place) or an override dictionary if a clean-text defect is ever proven.
- If the user’s saved-voice runs are wrong while the preset is right, next phase targets saved-voice conditioning/reference quality, not text.

## Recommended next step

```text
SAVED-VOICE PRONUNCIATION QUALITY TUNING
```

— primary, because the text/phonemizer layer is now verified correct end-to-end and the fix for the only reproduced text-side defect is shipped; the remaining open variable is the saved-voice acoustic path. If the user reports the PRESET voice also mispronounces “người” after this fix, switch to:

```text
UNICODE/TEXT NORMALIZATION CONTINUATION
```

Do not auto-start.


