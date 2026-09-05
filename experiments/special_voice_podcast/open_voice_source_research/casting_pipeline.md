# Future casting pipeline (not executed)

Prerequisite: written approval of the exact release and intended commercial/synthetic use.

```text
approved official dataset
  → enumerate anonymous source IDs
  → technical quality filter
  → relevant broad metadata filters (never region label alone)
  → optional broad F0/acoustic prefilter
  → make clean 6–8 second reference candidates
  → encode each reference once in VieNeu
  → synthesize the same audition script
  → blind human listening and scorecard
  → direct-consent gate for any production voice
```

1. Preserve source release, license/terms snapshot, permitted purpose, retention/deletion owner, and pseudonymous ID in a provenance ledger.
2. Start with 20–50 IDs with adequate duration; reduce to about 10 only on technical/acoustic grounds.
3. Measure duration, decodability, clipping, silence, RMS/loudness, basic SNR/noise proxy, sample rate, and optional broad F0 range/stability. Reject technical failures only—metrics cannot establish warmth, trustworthiness, neutrality, or brandability.
4. Construct one continuous 6–8 second clean reference: no music, overlap, clipping, or excessive silence.
5. Use a fixed Vietnamese audition script, fixed synthesis settings and loudness, randomized blind labels, and listener scores for clarity, warmth, authority, naturalness, fatigue, and perceived neutrality.
6. Listener preference never resolves rights. Do not create a public/permanent contributor-derived brand voice without explicit documented permission; use contracted voice talent for production.

Local processing is ordinary CPU batch work. No GPU or hosted service is needed for inventory and signal filtering. F0 must remain a broad queue-reduction measure, never a proxy for gender, region, or quality.

