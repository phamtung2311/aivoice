import gc, json, random, sys, time
from pathlib import Path
import numpy as np, soundfile as sf
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT));ANCHOR=ROOT/'experiments/brand_speaker_phase33c/baseline_anchor/BRAND_CANDIDATE_03_BASELINE';RAW=HERE/'raw_outputs';AUD=HERE/'audition';MET=HERE/'metrics/metrics.json';MAP=HERE/'private_mapping.json';SEED=35001;P={'temperature':.82,'top_k':25,'top_p':.97,'repetition_penalty':1.15}
TEXT='Khi một ý tưởng có nhiều chi tiết, người dẫn không cần ngắt sau mọi dấu phẩy, bởi người nghe vẫn có thể theo kịp nếu câu được giữ liền mạch và trọng tâm được đặt đúng chỗ. Đây là một câu ngắn. Trong phần giải thích tiếp theo, chúng ta nêu mục tiêu, đưa một ví dụ cụ thể, rồi kết lại bằng hành động có thể làm ngay để nội dung vừa rõ ràng vừa tự nhiên.'
def m(p):
 d,r=sf.read(p,always_2d=True);x=d.mean(1);return {'duration_seconds':round(len(x)/r,3),'sample_rate':int(r),'channels':int(d.shape[1]),'peak':round(float(np.max(abs(x))),6),'rms':round(float(np.sqrt(np.mean(x*x))),6),'clipped_samples':int(np.count_nonzero(abs(x)>=.999))}
def main():
 from backend.app.tts.engine import TTSEngine
 from backend.app.tts.text import split_into_sentences,preprocess_text
 emb=np.load(ANCHOR/'speaker_emb.npy',allow_pickle=False);codes=np.load(ANCHOR/'reference_codes.npy',allow_pickle=False);voice={'speaker_emb':emb,'codes':codes};RAW.mkdir(parents=True,exist_ok=True);AUD.mkdir(parents=True,exist_ok=True);MET.parent.mkdir(parents=True,exist_ok=True);e=TTSEngine(backend='onnx');rows=[]
 try:
  for k in 'ABC':
   out=RAW/f'{k}.wav';t=time.perf_counter();np.random.seed(SEED);print(k,flush=True)
   if k=='A': e.generate(TEXT,voice=voice,speed=1.,out_path=str(out),max_chunk_chars=240,denoise=False,use_ref_codes=True,quality_diagnostics=True,**P);diag=e.last_generation_diagnostics;calls=diag['outer_chunk_count']
   elif k=='B':
    parts=[]
    for s in split_into_sentences(preprocess_text(TEXT)):
     parts.append(np.asarray(e._model.infer(s,voice=voice,max_chars=1000,denoise=False,use_ref_codes=True,**P),dtype=np.float32))
    sf.write(out,np.concatenate(parts),48000,subtype='PCM_16');diag={'mode':'one direct VieNeu call per grammatical sentence','sentence_calls':len(parts)};calls=len(parts)
   else:
    wav=np.asarray(e._model.infer(TEXT,voice=voice,max_chars=1000,denoise=False,use_ref_codes=True,**P),dtype=np.float32);sf.write(out,wav,48000,subtype='PCM_16');diag={'mode':'one direct VieNeu call for full passage','max_chars':1000};calls=1
   rows.append({'strategy':k,'calls':calls,'generation_seconds':round(time.perf_counter()-t,3),'audio':m(out),'diagnostics':diag})
 finally:del e;gc.collect()
 order=list('ABC');random.Random(SEED).shuffle(order);mapping={f'Clip_{chr(65+i)}.wav':x for i,x in enumerate(order)};MAP.write_text(json.dumps(mapping,indent=2)+'\n')
 pres={}
 for name,k in mapping.items():
  d,sr=sf.read(RAW/f'{k}.wav',dtype='float32');r=float(np.sqrt(np.mean(d*d)));p=float(np.max(abs(d)));g=min(.09/r,.95/p);sf.write(AUD/name,d*g,sr,subtype='PCM_16');pres[name]={'gain':round(g,6),'audio':m(AUD/name)}
 MET.write_text(json.dumps({'text':TEXT,'params':P,'outputs':rows,'audition':pres},ensure_ascii=False,indent=2)+'\n');print('PHASE35_READY')
if __name__=='__main__':main()
