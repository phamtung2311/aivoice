# Phase 42A — Human listening gate

Status: **TECHNICAL PIPELINE PASS / HUMAN QUALITY FAIL**

## Phase 42A human result

The project owner uploaded a real long M4A source and listened to real VieNeu
candidates. Human result: **FAIL**.

- The newer candidate only sounded “ná ná” (roughly similar) to the real voice.
- It was worse than the older Voice Lab clone.
- A long source corpus did not solve the long-sentence prosody, rhythm or
  pronunciation problem.
- Do not continue investing in a VieNeu long-reference workaround. VieNeu's
  actual 8-second enrollment limit remains unchanged.

This is a human-quality result, not a failure of the local source-preservation,
decode, segmentation, or metadata pipeline.

Do not score a synthetic fixture. After uploading the owner's 30–180 second
recording and generating the fixed test set, record each candidate's exact path,
SHA256, engine, reference segment and test ID here before listening.

For each candidate, score the two dimensions separately:

## Speaker identity

- Does it sound like me?
- Are timbre, vocal texture and recognizable identity preserved?
- Are there pronunciation errors, missing words or unstable identity?

## Prosody and style

- Does it sound like the way I speak, rather than only sharing my timbre?
- Are pace, pitch contour, stress, comma rhythm and sentence endings natural?
- Do transitions and pauses support the meaning?
- Is the long passage expressive without sounding theatrical?
- Could I listen for 20 minutes without fatigue?
- Could this become the narrator voice for “Một khoảng tĩnh”?

Human listening is the final gate. Metrics must not select a winner.
