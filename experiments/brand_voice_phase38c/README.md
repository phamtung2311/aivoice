# Phase 38C — OpenVoice V2 CPU separation probe

This directory is isolated research work. It must not modify AIVoice production,
the main `.venv`, or the canonical Candidate 03 assets.

Frozen Vietnamese source text:

> Khi mọi thứ trở nên ồn ào, điều quan trọng nhất là giữ một nhịp suy nghĩ thật rõ ràng.

The source renderer is the installed VieNeu 3.3.0 ONNX CPU path using the exact
built-in preset ID `Minh Đức` and documented defaults. OpenVoice V2 is used only
for tone-colour conversion on CPU.

