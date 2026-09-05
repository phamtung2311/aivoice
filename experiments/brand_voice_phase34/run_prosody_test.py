#!/usr/bin/env python3
"""Phase 34: four finite Candidate 03 prosody strategies, CPU sequential."""
import gc,hashlib,json,random,resource,sys,time
from pathlib import Path
import numpy as np, soundfile as sf
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT))
ANCHOR=ROOT/'experiments/brand_speaker_phase33c/baseline_anchor/BRAND_CANDIDATE_03_BASELINE';RAW=HERE/'raw_outputs';AUD=HERE/'audition';MET=HERE/'metrics/metrics.json';MAP=HERE/'private_mapping.json';SEED=34001
TEXT='Trong một video tốt, điều quan trọng không phải là nói thật nhiều, mà là giúp người nghe hiểu đúng điều cần nhớ. Hôm nay, chúng ta đi qua ba điểm: mục tiêu rõ ràng, ví dụ cụ thể và một bước tiếp theo có thể làm ngay. Không cần nói to. Chỉ cần nói chắc, đúng chỗ, đúng lúc. Khi thông tin có con số 250 nghìn đồng, thời gian 3,5 giờ và tên Nguyễn Thị Ánh, người dẫn cần đặt từng chi tiết vào câu chuyện để khán giả theo kịp. Nhờ vậy, phần giải thích dài hơn vẫn giữ được trọng tâm, người nghe biết vì sao việc này quan trọng, và sau khi video kết thúc, họ có thể bắt đầu bằng một hành động nhỏ nhưng rõ ràng. Đó là cách một thông điệp trở nên đáng tin và có sức nặng.'
# Exact Clip A / Phase 33C Signature decoding baseline for every strategy.
P={'temperature':.82,'top_k':25,'top_p':.97,'repetition_penalty':1.15};TARGET=.09;CEILING=.95
# Markers are never passed to VieNeu; they become explicit joins. B preserves the
# text exactly. C changes punctuation only in the internal TTS representation.
PAUSE_SCRIPT='Trong một video tốt, điều quan trọng không phải là nói thật nhiều, mà là giúp người nghe hiểu đúng điều cần nhớ. || Hôm nay, chúng ta đi qua ba điểm: mục tiêu rõ ràng, ví dụ cụ thể và một bước tiếp theo có thể làm ngay. || Không cần nói to. | Chỉ cần nói chắc, đúng chỗ, đúng lúc. || Khi thông tin có con số 250 nghìn đồng, thời gian 3,5 giờ và tên Nguyễn Thị Ánh, người dẫn cần đặt từng chi tiết vào câu chuyện để khán giả theo kịp. || Nhờ vậy, phần giải thích dài hơn vẫn giữ được trọng tâm, người nghe biết vì sao việc này quan trọng, và sau khi video kết thúc, họ có thể bắt đầu bằng một hành động nhỏ nhưng rõ ràng. || Đó là cách một thông điệp trở nên đáng tin và có sức nặng.'
AUTH_TEXT='Trong một video tốt. Điều quan trọng không phải là nói thật nhiều. Mà là giúp người nghe hiểu đúng điều cần nhớ. Hôm nay, chúng ta đi qua ba điểm: mục tiêu rõ ràng, ví dụ cụ thể và một bước tiếp theo có thể làm ngay. Không cần nói to. Chỉ cần nói chắc, đúng chỗ, đúng lúc. Khi thông tin có con số 250 nghìn đồng, thời gian 3,5 giờ và tên Nguyễn Thị Ánh, người dẫn cần đặt từng chi tiết vào câu chuyện để khán giả theo kịp. Nhờ vậy, phần giải thích dài hơn vẫn giữ được trọng tâm. Người nghe biết vì sao việc này quan trọng. Sau khi video kết thúc, họ có thể bắt đầu bằng một hành động nhỏ nhưng rõ ràng. Đó là cách một thông điệp trở nên đáng tin và có sức nặng.'
COMBINED_SCRIPT='Trong một video tốt. || Điều quan trọng không phải là nói thật nhiều. | Mà là giúp người nghe hiểu đúng điều cần nhớ. || Hôm nay, chúng ta đi qua ba điểm: mục tiêu rõ ràng, ví dụ cụ thể và một bước tiếp theo có thể làm ngay. || Không cần nói to. | Chỉ cần nói chắc, đúng chỗ, đúng lúc. || Khi thông tin có con số 250 nghìn đồng, thời gian 3,5 giờ và tên Nguyễn Thị Ánh, người dẫn cần đặt từng chi tiết vào câu chuyện để khán giả theo kịp. || Nhờ vậy, phần giải thích dài hơn vẫn giữ được trọng tâm. | Người nghe biết vì sao việc này quan trọng. | Sau khi video kết thúc, họ có thể bắt đầu bằng một hành động nhỏ nhưng rõ ràng. || Đó là cách một thông điệp trở nên đáng tin và có sức nặng.'
STRATEGIES={'A':('baseline',TEXT,False),'B':('pause_aware',PAUSE_SCRIPT,True),'C':('authority_aware',AUTH_TEXT,False),'D':('combined',COMBINED_SCRIPT,True)}
def m(p):
 d,r=sf.read(p,always_2d=True);x=d.mean(1);c=int(np.count_nonzero(abs(x)>=.999));return {'duration_seconds':round(len(x)/r,3),'sample_rate':int(r),'channels':int(d.shape[1]),'peak':round(float(np.max(abs(x))),6),'rms':round(float(np.sqrt(np.mean(x*x))),6),'clipped_samples':c,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def main():
 from backend.app.tts.engine import TTSEngine
 emb=np.load(ANCHOR/'speaker_emb.npy',allow_pickle=False);codes=np.load(ANCHOR/'reference_codes.npy',allow_pickle=False)
 if emb.shape!=(192,) or codes.shape!=(87,16):raise SystemExit('ANCHOR_INVALID')
 RAW.mkdir(parents=True,exist_ok=True);AUD.mkdir(parents=True,exist_ok=True);MET.parent.mkdir(parents=True,exist_ok=True);e=TTSEngine(backend='onnx');rows=[]
 try:
  for k,(label,text,prosody) in STRATEGIES.items():
   out=RAW/f'{k}.wav';tmp=out.with_name('.'+out.stem+'.tmp.wav');t=time.perf_counter();np.random.seed(SEED);print(k,flush=True)
   if prosody:e.generate_prosody(text,voice={'speaker_emb':emb,'codes':codes},speed=1.,out_path=str(tmp),denoise=False,use_ref_codes=True,quality_diagnostics=True,**P)
   else:e.generate(text,voice={'speaker_emb':emb,'codes':codes},speed=1.,out_path=str(tmp),max_chunk_chars=240,denoise=False,use_ref_codes=True,quality_diagnostics=True,**P)
   a=m(tmp)
   if a['sample_rate']!=48000 or a['channels']!=1 or a['clipped_samples']:raise RuntimeError('INVALID '+k)
   tmp.replace(out);rows.append({'strategy':k,'label':label,'prosody_api':prosody,'generation_seconds':round(time.perf_counter()-t,3),'rtf':round((time.perf_counter()-t)/a['duration_seconds'],3),'audio':m(out),'diagnostics':e.last_generation_diagnostics})
 finally:del e;gc.collect()
 order=list(STRATEGIES);random.Random(SEED).shuffle(order);mapping={f'Clip_{chr(65+i)}.wav':x for i,x in enumerate(order)};MAP.write_text(json.dumps(mapping,indent=2)+'\n')
 pres={}
 for name,k in mapping.items():
  d,sr=sf.read(RAW/f'{k}.wav',dtype='float32');r=float(np.sqrt(np.mean(d*d)));p=float(np.max(abs(d)));g=min(TARGET/r,CEILING/p);sf.write(AUD/name,d*g,sr,subtype='PCM_16');pres[name]={'gain':round(g,6),'audio':m(AUD/name)}
 MET.write_text(json.dumps({'baseline_params':P,'identity_anchor':'Candidate 03 / D','strategies':{k:{'label':v[0],'prosody_api':v[2]} for k,v in STRATEGIES.items()},'outputs':rows,'audition':pres},ensure_ascii=False,indent=2)+'\n');print('PHASE34_READY')
if __name__=='__main__':main()
