# VC comparison

| technology | VC type | new identity without target | stable identity | Vietnamese | CPU / 16 GB | license risk | fit |
|---|---|---|---|---|---|---|---|
| Seed-VC | TYPE 1 | No | Target-dependent | Unknown | Possible but unbenchmarked | Weights review required | Target-reference only |
| OpenVoice V2 | TYPE 1 | No | Target-dependent | Official list excludes Vietnamese | Possible but unbenchmarked | Weights review required | Poor |
| RVC | TYPE 2 | No | After target training | Community/unknown | CPU inference, training risk | Weights/data vary | Poor |
| VoicePrivacy B1-style | TYPE 3-adjacent | Experimental | Not demonstrated by 2024 utterance baseline | English-oriented/unverified | Complex/RAM risk | Pool/assets review required | Research only |

All are PyTorch-centric; Python 3.14 is unverified. Any future PoC would require
an isolated Python 3.10/3.11 environment, never the production `.venv`.
