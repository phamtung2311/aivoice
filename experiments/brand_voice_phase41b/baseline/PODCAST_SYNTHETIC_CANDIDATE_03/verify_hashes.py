#!/usr/bin/env python3
import hashlib, numpy as np, json
from pathlib import Path
p=Path(__file__).resolve().parent
arr=np.load(p/'speaker_emb.npy')
print('speaker_emb shape', arr.shape)
print('speaker_emb array sha256', hashlib.sha256(arr.tobytes()).hexdigest())
print('speaker_emb file sha256', hashlib.sha256(open(p/'speaker_emb.npy','rb').read()).hexdigest())
print('wav file sha256', hashlib.sha256(open(p/('candidate_01.wav'),'rb').read()).hexdigest())
