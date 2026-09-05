"""One approved Gwen-TTS CPU clone probe; no variants, no production writes."""
import gc,hashlib,json,os,random,resource,shutil,sys,time
from pathlib import Path
os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
import numpy as np,soundfile as sf,torch
from qwen_tts import Qwen3TTSModel
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];MODEL=HERE/'models/gwen-tts-0.6B';ANCHOR=ROOT/'experiments/brand_speaker_phase33c/baseline_anchor/BRAND_CANDIDATE_03_BASELINE';CONTROL=ROOT/'experiments/brand_voice_phase35b/BEST_KNOWN_BRAND_VOICE_CHECKPOINT/phase34_clip_c.wav';REF=HERE/'reference';RAW=HERE/'raw_gwen';AUD=HERE/'audition';MET=HERE/'metrics/metrics.json';MAP=HERE/'private_mapping.json'
TEXT='Trong một video tốt, điều quan trọng không phải là nói thật nhiều, mà là giúp người nghe hiểu đúng điều cần nhớ. Hôm nay, chúng ta đi qua ba điểm: mục tiêu rõ ràng, ví dụ cụ thể và một bước tiếp theo có thể làm ngay. Không cần nói to. Chỉ cần nói chắc, đúng chỗ, đúng lúc. Khi thông tin có con số 250 nghìn đồng, thời gian 3,5 giờ và tên Nguyễn Thị Ánh, người dẫn cần đặt từng chi tiết vào câu chuyện để khán giả theo kịp. Nhờ vậy, phần giải thích dài hơn vẫn giữ được trọng tâm, người nghe biết vì sao việc này quan trọng, và sau khi video kết thúc, họ có thể bắt đầu bằng một hành động nhỏ nhưng rõ ràng. Đó là cách một thông điệp trở nên đáng tin và có sức nặng.'
REF_TEXT='A quiet evening settles over the city. I speak clearly, naturally, and without rushing.'
CFG={'temperature':.3,'top_k':20,'top_p':.9,'max_new_tokens':4096,'repetition_penalty':2.0,'subtalker_do_sample':True,'subtalker_temperature':.1,'subtalker_top_k':20,'subtalker_top_p':1.0}
def m(p):
 d,r=sf.read(p,always_2d=True);x=d.mean(1);return {'duration_seconds':round(len(x)/r,3),'sample_rate':int(r),'channels':int(d.shape[1]),'peak':round(float(np.max(abs(x))),6),'rms':round(float(np.sqrt(np.mean(x*x))),6),'clipped_samples':int(np.count_nonzero(abs(x)>=.999))}
def main():
 for d in (REF,RAW,AUD,MET.parent):d.mkdir(parents=True,exist_ok=True)
 shutil.copy2(ANCHOR/'qwen_source.wav',REF/'candidate03_qwen_source.wav');(REF/'reference_transcript.txt').write_text(REF_TEXT+'\n')
 out=RAW/'gwen_candidate03.wav';t=time.perf_counter();model=Qwen3TTSModel.from_pretrained(str(MODEL),device_map='cpu',dtype=torch.bfloat16,attn_implementation='sdpa')
 with torch.inference_mode():w,sr=model.generate_voice_clone(text=TEXT,ref_audio=str(REF/'candidate03_qwen_source.wav'),ref_text=REF_TEXT,**CFG)
 sf.write(out,w[0],sr);a=m(out)
 if a['clipped_samples'] or a['channels']!=1:raise RuntimeError('GWEN_INVALID_OUTPUT')
 elapsed=round(time.perf_counter()-t,3);del model;gc.collect();order=['control','gwen'];random.Random(36001).shuffle(order);mapping={f'Clip_{chr(65+i)}.wav':x for i,x in enumerate(order)};MAP.write_text(json.dumps(mapping,indent=2)+'\n')
 presentation={}
 for name,kind in mapping.items():
  src=CONTROL if kind=='control' else out;d,s=sf.read(src,dtype='float32');g=min(.09/float(np.sqrt(np.mean(d*d))),.95/float(np.max(abs(d))));sf.write(AUD/name,d*g,s,subtype='PCM_16');presentation[name]={'gain':round(g,6),'audio':m(AUD/name)}
 MET.write_text(json.dumps({'engine':'g-group-ai-lab/gwen-tts-0.6B','device':'cpu','dtype':'torch.bfloat16','attention':'sdpa','reference':'Candidate 03 pristine Qwen source + exact English transcript','input_text':TEXT,'normalization':'none beyond already-NFC Phase 34 text','config':CFG,'gwen':{'audio':a,'generation_seconds':elapsed,'rtf':round(elapsed/a['duration_seconds'],3),'peak_rss_mb':round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,2)},'audition':presentation},ensure_ascii=False,indent=2)+'\n');print('PHASE36B_READY')
if __name__=='__main__':main()
