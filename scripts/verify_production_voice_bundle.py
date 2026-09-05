import hashlib,json,sys
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1]; m=json.loads((R/'assets/production_voices/production_voice_manifest.json').read_text())
def h(a): return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
for v in m['voices']:
 a=np.load(R/v['embedding'],allow_pickle=False); assert a.shape==(192,) and a.dtype==np.float32 and h(a)==v['embedding_array_sha256'],v['stable_id']
p=R/m['anchor']['artifact']; assert p.exists() and hashlib.sha256(p.read_bytes()).hexdigest()==m['anchor']['file_sha256']
from backend.app.tts.podcast_voices import resolve_podcast_voice
for v in m['voices']: resolve_podcast_voice(v['stable_id'])
print('AIVOICE PODCAST VOICE SET v1: VERIFIED')
