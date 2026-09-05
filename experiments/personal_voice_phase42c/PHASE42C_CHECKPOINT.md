# Phase 42C checkpoint

Updated: 2026-09-05 (Asia/Ho_Chi_Minh)

## Completed

- Read all Phase 42A/42B reports, reviews and checkpoint. Both zero-shot paths
  are closed on the owner's human result: **“Tất cả đều chả ra gì.”**
- Confirmed Phase 41H's historical prosody carrier must remain untouched:
  `experiments/brand_voice_phase41h/audio/v2_natural.wav`, expected SHA256
  `66a51b4ccedccec6016cc778ddafceaf4c0d42fad741ad36f711a7d25ef8dce5`.
- Audited a small current upstream shortlist. RVC is conditionally selected for
  a future single-candidate CPU VC PoC. It is not installed or downloaded.
- Current private owner corpus remains 125.354667 seconds / SHA256
  `1bfc4f9b65b7babf028d0c79a3ef53ac838c979660844595a2b4f872e447c147`.
  It is insufficient for the documented RVC `>=10 min` low-noise recommendation.
- Created the local-only recording plan and reading script. Added Phase 42C
  private source, derived data, checkpoint, output, metadata and future venv
  paths to `.gitignore`.

## Selected candidate, pending data gate

- RVC repository: `RVC-Project/Retrieval-based-Voice-Conversion-WebUI`;
  audited remote HEAD `81eed5e8f68b6bed1789f682fe78cdd324495afc`.
- Code license MIT; base pretrained repository reports MIT. Exact weight files,
  commits and SHA256 must be pinned and verified only after enough local speech
  exists and before any install/download.
- CPU is documented for training, F0 extraction, HuBERT feature extraction and
  inference. No local CPU speed/RSS benchmark exists yet, so no duration/RAM
  claim has been made.

## Blocker and next exact action

**BLOCKED ON PRIVATE DATA COLLECTION, NOT ON MODEL FAILURE.** Do not install,
download, train, or render. The next exact action after 12 verified usable
minutes exist is to audit their local metadata/transcript status and create an
isolated `.venv-phase42c-rvc`; then pin/download only the selected RVC source
and required MIT-provenanced base weights, and run a bounded CPU benchmark.
