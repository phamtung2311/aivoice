import json,random,sys
from pathlib import Path
import numpy as np,soundfile as sf
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT));RAW=HERE/'cpu_short_raw';AUD=HERE/'cpu_short_audition';MET=HERE/'cpu_short_comparison_metrics.json';MAP=HERE/'cpu_short_mapping.json';ANCHOR=ROOT/'experiments/brand_speaker_phase33c/baseline_anchor/BRAND_CANDIDATE_03_BASELINE'
TEXT='Một câu chuyện rõ ràng cần được kể liền mạch, có điểm nhấn đúng chỗ và kết thúc bằng một ý thật đáng nhớ.'
def m(p):
 d,r=sf.read(p,always_2d=True);x=d.mean(1);return {'duration_seconds':round(len(x)/r,3),'sample_rate':int(r),'channels':int(d.shape[1]),'peak':round(float(np.max(abs(x))),6),'rms':round(float(np.sqrt(np.mean(x*x))),6),'clipped_samples':int(np.count_nonzero(abs(x)>=.999))}
def main():
 from backend.app.tts.engine import TTSEngine
 g=RAW/'gwen.wav';v=RAW/'vieneu.wav';assert g.is_file() and m(g)['clipped_samples']==0
 emb=np.load(ANCHOR/'speaker_emb.npy');codes=np.load(ANCHOR/'reference_codes.npy');e=TTSEngine(backend='onnx');e.generate(TEXT,voice={'speaker_emb':emb,'codes':codes},speed=1.,out_path=str(v),max_chunk_chars=240,denoise=False,use_ref_codes=True,temperature=.82,top_k=25,top_p=.97,repetition_penalty=1.15);del e
 assert m(v)['clipped_samples']==0;AUD.mkdir(exist_ok=True);order=['gwen','vieneu'];random.Random(36101).shuffle(order);mapping={f'Clip_{chr(65+i)}.wav':x for i,x in enumerate(order)};MAP.write_text(json.dumps(mapping,indent=2)+'\n');present={}
 for n,k in mapping.items():
  d,sr=sf.read(g if k=='gwen' else v,dtype='float32');gain=min(.09/float(np.sqrt(np.mean(d*d))),.95/float(np.max(abs(d))));sf.write(AUD/n,d*gain,sr,subtype='PCM_16');present[n]=m(AUD/n)
 MET.write_text(json.dumps({'gwen':m(g),'vieneu':m(v),'audition':present},indent=2)+'\n')
if __name__=='__main__':main()
