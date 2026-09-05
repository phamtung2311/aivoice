import hashlib,json,random,shutil,sys,time
from pathlib import Path
import numpy as np,soundfile as sf
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT));SRC=ROOT/'experiments/brand_voice_phase34';ANCHOR=HERE/'BEST_KNOWN_BRAND_VOICE_CHECKPOINT';RAW=HERE/'raw_outputs';AUD=HERE/'audition';MET=HERE/'metrics/metrics.json';MAP=HERE/'private_mapping.json';SEED=34001;P={'temperature':.82,'top_k':25,'top_p':.97,'repetition_penalty':1.15}
TEXT='Khi một nội dung có nhiều chi tiết, người dẫn cần giữ câu chuyện liền mạch để người nghe theo kịp, nhưng vẫn phải dừng đúng chỗ khi ý chính đã rõ. Đây là điều quan trọng. Sau đó, một ví dụ cụ thể giúp thông tin bớt trừu tượng, và một bước nhỏ có thể làm ngay sẽ giúp khán giả biết mình nên bắt đầu từ đâu.'
def m(p):
 d,r=sf.read(p,always_2d=True);x=d.mean(1);return {'duration_seconds':round(len(x)/r,3),'sample_rate':int(r),'channels':int(d.shape[1]),'peak':round(float(np.max(abs(x))),6),'rms':round(float(np.sqrt(np.mean(x*x))),6),'clipped_samples':int(np.count_nonzero(abs(x)>=.999))}
def freeze():
 files={'phase34_clip_c.wav':SRC/'audition/Clip_C.wav','speaker_emb.npy':ROOT/'experiments/brand_speaker_phase33c/baseline_anchor/BRAND_CANDIDATE_03_BASELINE/speaker_emb.npy','reference_codes.npy':ROOT/'experiments/brand_speaker_phase33c/baseline_anchor/BRAND_CANDIDATE_03_BASELINE/reference_codes.npy','phase34_metrics.json':SRC/'metrics/metrics.json'}
 if not ANCHOR.exists():
  ANCHOR.mkdir(parents=True)
  for n,p in files.items():shutil.copy2(p,ANCHOR/n)
  (ANCHOR/'manifest.json').write_text(json.dumps({n:hashlib.sha256((ANCHOR/n).read_bytes()).hexdigest() for n in files},indent=2)+'\n')
def main():
 from backend.app.tts.engine import TTSEngine
 freeze();emb=np.load(ANCHOR/'speaker_emb.npy',allow_pickle=False);codes=np.load(ANCHOR/'reference_codes.npy',allow_pickle=False);voice={'speaker_emb':emb,'codes':codes};RAW.mkdir(parents=True,exist_ok=True);AUD.mkdir(parents=True,exist_ok=True);MET.parent.mkdir(parents=True,exist_ok=True);e=TTSEngine(backend='onnx');rows=[]
 strategies={'A':('current_240',None),'B':('one_sentence_per_call','sentence'),'C':('two_related_sentence_group','group'),'D':('adaptive_single_350','single')}
 for k,(label,mode) in strategies.items():
  out=RAW/f'{k}.wav';np.random.seed(SEED);t=time.perf_counter();print(k,flush=True)
  if mode is None:e.generate(TEXT,voice=voice,speed=1.,out_path=str(out),max_chunk_chars=240,denoise=False,use_ref_codes=True,quality_diagnostics=True,**P);diag=e.last_generation_diagnostics;calls=diag['outer_chunk_count']
  else:
   s=['Khi một nội dung có nhiều chi tiết, người dẫn cần giữ câu chuyện liền mạch để người nghe theo kịp, nhưng vẫn phải dừng đúng chỗ khi ý chính đã rõ.','Đây là điều quan trọng.','Sau đó, một ví dụ cụ thể giúp thông tin bớt trừu tượng, và một bước nhỏ có thể làm ngay sẽ giúp khán giả biết mình nên bắt đầu từ đâu.']
   units=s if mode=='sentence' else [s[0]+' '+s[1],s[2]] if mode=='group' else [TEXT]
   parts=[np.asarray(e._model.infer(u,voice=voice,max_chars=350,denoise=False,use_ref_codes=True,**P),dtype=np.float32) for u in units];sf.write(out,np.concatenate(parts),48000,subtype='PCM_16');calls=len(units);diag={'mode':mode,'units':units}
  rows.append({'strategy':k,'label':label,'calls':calls,'generation_seconds':round(time.perf_counter()-t,3),'audio':m(out),'diagnostics':diag})
 order=list(strategies);random.Random(SEED).shuffle(order);mapping={f'Clip_{chr(65+i)}.wav':x for i,x in enumerate(order)};MAP.write_text(json.dumps(mapping,indent=2)+'\n');pres={}
 for n,k in mapping.items():
  d,sr=sf.read(RAW/f'{k}.wav',dtype='float32');g=min(.09/float(np.sqrt(np.mean(d*d))),.95/float(np.max(abs(d))));sf.write(AUD/n,d*g,sr,subtype='PCM_16');pres[n]={'gain':round(g,6),'audio':m(AUD/n)}
 MET.write_text(json.dumps({'text':TEXT,'params':P,'outputs':rows,'audition':pres},ensure_ascii=False,indent=2)+'\n');print('PHASE35B_READY')
if __name__=='__main__':main()
