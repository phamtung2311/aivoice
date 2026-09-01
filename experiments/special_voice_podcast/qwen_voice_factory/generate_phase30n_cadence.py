#!/usr/bin/env python3
"""Manual Phase 30N cadence experiment; M-A identity is never regenerated."""
import hashlib,json,os,random,shutil,sys,tempfile
from pathlib import Path
import numpy as np, soundfile as sf
ROOT=Path(__file__).resolve().parent; PROJECT=ROOT.parents[2]; PHASE=ROOT.parent/'phase30n'; KEEPERS=ROOT.parent/'keepers'
CACHE=Path('/home/tung/.cache/huggingface'); SNAPSHOT=CACHE/'hub/models--pnnbao-ump--VieNeu-TTS-v3-Turbo/snapshots/2da0efab622a1722125991736524f080b751ef5b'
TEXT='Có những điều nghe qua tưởng như rất đơn giản, nhưng khi dành thêm một chút thời gian để suy nghĩ, chúng ta lại thấy phía sau đó là cả một câu chuyện dài. Và có lẽ điều thú vị nhất không nằm ở việc tìm ra câu trả lời thật nhanh, mà ở cách mỗi người tự nhìn lại trải nghiệm của mình, rồi nhận ra một điều mà trước đây mình chưa từng chú ý.'
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def metrics(p):
 d,r=sf.read(p,always_2d=True);m=d[:,0];return {'duration_seconds':round(len(m)/r,3),'sample_rate':int(r),'channels':int(d.shape[1]),'peak':round(float(np.max(abs(m))),6),'rms':round(float(np.sqrt(np.mean(m*m))),6),'clipped_samples':int(np.count_nonzero(abs(m)>=.999))}
def valid(p):
 try: return p.is_file() and sf.info(str(p)).frames>0 and sf.info(str(p)).channels==1
 except Exception:return False
def boundary_trim(x,sr,leading_ms,trailing_ms):
 threshold=.002;active=np.flatnonzero(np.abs(x)>threshold)
 if not active.size:return x
 start=max(0,int(active[0]-leading_ms*sr/1000));end=min(len(x),int(active[-1]+1+trailing_ms*sr/1000));return x[start:end]
def main():
 # Create and verify every experiment output location before any model load.
 for directory in (PHASE,PHASE/'internal',PHASE/'audition',PHASE/'measurements',PHASE/'chunks'):
  directory.mkdir(parents=True,exist_ok=True)
 try:
  probe=PHASE/'internal'/'.write_preflight';probe.write_bytes(b'phase30n');probe.unlink()
 except OSError as exc: raise SystemExit(f'PHASE30N_OUTPUT_NOT_WRITABLE: {exc}')
 required=('config.json','denoiser.onnx','speaker_encoder.onnx','onnx_int8/tokenizer.json','onnx_int8/vieneu_acoustic_cached.onnx','onnx_int8/vieneu_backbone_shared.data','onnx_int8/vieneu_decode_step.onnx','onnx_int8/vieneu_prefill.onnx','onnx_int8/vieneu_v3_heads.npz')
 missing=[str(SNAPSHOT/item) for item in required if not (SNAPSHOT/item).is_file()]
 if missing: raise SystemExit('LOCAL_VIENEU_CACHE_MISSING: '+', '.join(missing))
 # Must precede importing/loading Hub-dependent runtime code. HF_HOME points to
 # the already complete local cache; HOME isolates only VieNeu scratch writes.
 os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1';os.environ['HF_HOME']=str(CACHE);os.environ['HOME']=str(ROOT/'.vieneu_runtime_home')
 sys.path.insert(0,str(PROJECT));from backend.app.tts.text import preprocess_text,split_into_sentences,chunk_sentences;from backend.app.tts.audio import edge_silence_samples,join_audios,save_wav;from backend.app.tts.engine import TTSEngine
 m=json.loads((KEEPERS/'KEEPERS_MANIFEST.json').read_text())
 for k in m['keepers']:
  for a in k['files'].values():
   p=Path(a['path']);assert p.is_file() and p.stat().st_size==a['size_bytes'] and h(p)==a['sha256'], 'KEEPER_INTEGRITY_FAILED'
 d=PHASE/'chunks';(ROOT/'.vieneu_runtime_home/.cache/vieneu/tmp').mkdir(parents=True,exist_ok=True)
 chunks=chunk_sentences(split_into_sentences(preprocess_text(TEXT)),max_chars=240);emb=np.load(KEEPERS/'phase30m_04/speaker_emb.npy',allow_pickle=False);codes=np.load(KEEPERS/'phase30m_04/reference_codes.npy',allow_pickle=False)
 engine=TTSEngine(backend='onnx')
 try:
  for n,text in enumerate(chunks):
   p=d/f'chunk_{n:02d}.wav'
   if not valid(p):
    np.random.seed(30109);raw=np.asarray(engine._model.infer(text,voice={'speaker_emb':emb,'codes':codes},denoise=False,use_ref_codes=True));raw=raw.astype(np.float32)/np.iinfo(raw.dtype).max if np.issubdtype(raw.dtype,np.integer) else raw.astype(np.float32);save_wav(str(p),raw,engine._model.sample_rate)
 finally: del engine
 aud=[];sr=sf.info(str(d/'chunk_00.wav')).samplerate
 for n in range(len(chunks)): aud.append(sf.read(d/f'chunk_{n:02d}.wav')[0].astype(np.float32))
 variants={'N-CONTROL':(130,False),'N-A':(85,False),'N-B':(130,True),'N-C':(85,True)};internal=PHASE/'internal';records=[]
 for name,(gap,trim) in variants.items():
  out=internal/f'{name}.wav';
  if not valid(out):
   pieces=[boundary_trim(a,sr,50,80) if trim else a for a in aud];gaps=[max(0,int(gap*sr/1000))];save_wav(str(out),join_audios(pieces,sr,gap_samples=gaps),sr)
  records.append({'variant':name,'explicit_join_target_ms':gap,'boundary_normalization':trim,'audio':metrics(out)})
 amap=PHASE/'private_mapping.json';
 if amap.exists(): mapping=json.loads(amap.read_text());assert set(mapping.values())==set(variants)
 else:
  ids=list(variants);random.Random(30109).shuffle(ids);mapping={f'{i:02d}':v for i,v in enumerate(ids,1)};amap.write_text(json.dumps(mapping,indent=2)+'\n')
 audition=PHASE/'audition';audition.mkdir(parents=True,exist_ok=True)
 for n,v in mapping.items():
  s=internal/f'{v}.wav';t=audition/f'voice_{n}.wav'
  if not t.is_file() or h(t)!=h(s):shutil.copy2(s,t)
 (PHASE/'measurements').mkdir(exist_ok=True);(PHASE/'measurements/pause_analysis.json').write_text(json.dumps({'text':TEXT,'chunk_lengths':[len(x) for x in chunks],'records':records},ensure_ascii=False,indent=2)+'\n')
 print('PHASE30N_CADENCE_AUDITION_READY')
if __name__=='__main__':main()
