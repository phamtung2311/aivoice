import gc,json,random,resource,sys,time
from pathlib import Path
import numpy as np,soundfile as sf,torch
from qwen_tts import Qwen3TTSModel
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT));MODEL=HERE/'models/gwen-tts-0.6B';REF=HERE/'reference/candidate03_qwen_source.wav';CONTROL_REF=ROOT/'experiments/brand_speaker_phase33c/baseline_anchor/BRAND_CANDIDATE_03_BASELINE';RAW=HERE/'cpu_short_raw';AUD=HERE/'cpu_short_audition';MET=HERE/'cpu_short_metrics.json';MAP=HERE/'cpu_short_mapping.json'
TEXT='Một câu chuyện rõ ràng cần được kể liền mạch, có điểm nhấn đúng chỗ và kết thúc bằng một ý thật đáng nhớ.';REF_TEXT='A quiet evening settles over the city. I speak clearly, naturally, and without rushing.';CFG={'temperature':.3,'top_k':20,'top_p':.9,'max_new_tokens':4096,'repetition_penalty':2.0,'subtalker_do_sample':True,'subtalker_temperature':.1,'subtalker_top_k':20,'subtalker_top_p':1.0}
def m(p):
 d,r=sf.read(p,always_2d=True);x=d.mean(1);return {'duration_seconds':round(len(x)/r,3),'sample_rate':int(r),'channels':int(d.shape[1]),'peak':round(float(np.max(abs(x))),6),'rms':round(float(np.sqrt(np.mean(x*x))),6),'clipped_samples':int(np.count_nonzero(abs(x)>=.999))}
def main():
 from backend.app.tts.engine import TTSEngine
 RAW.mkdir(exist_ok=True);AUD.mkdir(exist_ok=True);out=RAW/'gwen.wav';t=time.perf_counter();model=Qwen3TTSModel.from_pretrained(str(MODEL),device_map='cpu',dtype=torch.bfloat16,attn_implementation='sdpa')
 with torch.inference_mode():w,sr=model.generate_voice_clone(text=TEXT,ref_audio=str(REF),ref_text=REF_TEXT,**CFG)
 sf.write(out,w[0],sr);elapsed=time.perf_counter()-t;g=m(out);del model;gc.collect();emb=np.load(CONTROL_REF/'speaker_emb.npy');codes=np.load(CONTROL_REF/'reference_codes.npy');e=TTSEngine(backend='onnx');control=RAW/'vieneu.wav';e.generate(TEXT,voice={'speaker_emb':emb,'codes':codes},speed=1.,out_path=str(control),max_chunk_chars=240,denoise=False,use_ref_codes=True,temperature=.82,top_k=25,top_p=.97,repetition_penalty=1.15);del e;order=['gwen','vieneu'];random.Random(36101).shuffle(order);mapping={f'Clip_{chr(65+i)}.wav':x for i,x in enumerate(order)};MAP.write_text(json.dumps(mapping,indent=2)+'\n');pres={}
 for n,k in mapping.items():
  d,s=sf.read(out if k=='gwen' else control,dtype='float32');gain=min(.09/float(np.sqrt(np.mean(d*d))),.95/float(np.max(abs(d))));sf.write(AUD/n,d*gain,s,subtype='PCM_16');pres[n]=m(AUD/n)
 MET.write_text(json.dumps({'text':TEXT,'gwen':{'audio':g,'generation_seconds':round(elapsed,3),'rtf':round(elapsed/g['duration_seconds'],3),'peak_rss_mb':round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,2),'device':'cpu','dtype':'bf16','config':CFG},'vieneu':m(control),'audition':pres},ensure_ascii=False,indent=2)+'\n');print('READY')
if __name__=='__main__':main()
