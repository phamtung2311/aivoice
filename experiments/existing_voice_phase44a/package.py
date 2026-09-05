import json,hashlib
from pathlib import Path
import numpy as np, soundfile as sf
R=Path(__file__).parent; O=R/'outputs'; L=R/'listening_package'; L.mkdir(exist_ok=True)
for n in range(1,9):
 a=[]; sr=48000
 for k in 'ABC':
  x,sr=sf.read(O/f'existing{n:02d}_{k}.wav',dtype='float32'); a.extend([x, np.zeros(int(1.2*sr),dtype='float32')] if k!='C' else [x])
 y=np.concatenate(a); peak=np.max(np.abs(y)); y=y*(10**(-1/20)/peak) if peak else y; p=L/f'existing_voice_{n:02d}_ABC.wav'; sf.write(p,y,sr,subtype='PCM_16')
