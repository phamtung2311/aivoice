# AIVoice Phase 28 — Kaggle IndexTTS Emotion PoC

This is an isolated research package. It is **not** part of AIVoice production and does not integrate IndexTTS with VieNeu.

Budget rule: **0 VND only.** Use a normal Kaggle free-GPU notebook. Do not use paid accelerators, paid credits, account automation, or quota bypasses.

## Before Kaggle

1. Create a Kaggle Notebook normally and enable its free GPU in Notebook Settings.
2. Upload this experiment directory as a small Kaggle Dataset, then attach it to the notebook. Copy it into `/kaggle/working/index_emotion_kaggle/`; it contains no model weights or private audio.
3. Import `kaggle_poc.ipynb`, set its `POC_ROOT` cell to that copied directory, and run cells in numerical order.
4. Do not run asset download until cell `00` has passed its GPU/RAM/disk checks.
5. Upload only deliberately selected, permissioned files to `references/` when cell `06` asks for them.

The notebook will install the pinned community source revision in a separate Kaggle working directory, fetch only the approved model subset, run the three-file smoke test, and stop. It cannot run the matrix until `poc_config.json` is manually changed to set `smoke_test_approved` to `true` after human listening.

## Expected reference filenames

```text
references/
  speakers/speaker_A.wav
  speakers/speaker_B.wav
  speakers/speaker_C.wav
  emotions/emotion_happy.wav
  emotions/emotion_sad.wav
  emotions/emotion_angry.wav
```

Read [reference_checklist.md](reference_checklist.md) before upload. Do not upload AIVoice code, saved voices, databases, credentials, or unrelated recordings.

## Execution order

1. `00` Environment check
2. `01` Install minimal runtime and pinned community source
3. `02` Configure approved assets
4. `03` Download and verify assets
5. `04` Upload references
6. `05` Load low-VRAM engine
7. `06` Run smoke test only
8. Listen to the three smoke WAVs and complete the evaluation sheet.
9. If and only if they pass, manually set `smoke_test_approved` to `true` in `poc_config.json`.
10. Run `09` matrix and `10` packaging.

The resulting `aivoice_phase28_poc.zip` contains outputs, manifest, environment details, logs, and the evaluation template. It never contains model weights or input reference audio.

## Source boundaries

- Community source is pinned to commit `f63b1879d4b46aac456bd00640a4833a2ae071f4`.
- The notebook does not patch that source. It avoids its optional Qwen text-emotion model by not downloading the configured Qwen directory and by never passing `use_emo_text=True`.
- The shared-audio and vector mechanisms are research hypotheses. Human listening decides success; a successful PoC does not authorize migration from VieNeu.
