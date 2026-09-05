import json,time
from pathlib import Path
import numpy as np,soundfile as sf,torch
from qwen_tts import Qwen3TTSModel
HERE=Path(__file__).resolve().parent;MODEL=HERE/'models/gwen-tts-0.6B';REF=HERE/'reference/candidate03_qwen_source.wav';OUT=HERE/'cpu_short_raw/gwen_vietnamese_corrected.wav';MET=HERE/'cpu_short_raw/gwen_vietnamese_corrected_metrics.json'
REF_TEXT='A quiet evening settles over the city. I speak clearly, naturally, and without rushing.'
TEXT='Một câu chuyện rõ ràng cần được kể liền mạch, có điểm nhấn đúng chỗ và kết thúc bằng một ý thật đáng nhớ.'
CFG={'temperature':.3,'top_k':20,'top_p':.9,'max_new_tokens':4096,'repetition_penalty':2.0,'subtalker_do_sample':True,'subtalker_temperature':.1,'subtalker_top_k':20,'subtalker_top_p':1.0}
if OUT.exists(): raise SystemExit('REFUSING_TO_OVERWRITE_CORRECTED_GWEN_OUTPUT')
t=time.perf_counter();model=Qwen3TTSModel.from_pretrained(str(MODEL),device_map='cpu',dtype=torch.bfloat16,attn_implementation='sdpa')
with torch.inference_mode(): w,sr=model.generate_voice_clone(text=TEXT,language='Vietnamese',ref_audio=str(REF),ref_text=REF_TEXT,**CFG)
sf.write(OUT,w[0],sr);d,r=sf.read(OUT,always_2d=True);x=d.mean(1);elapsed=time.perf_counter()-t
a={'duration_seconds':round(len(x)/r,3),'sample_rate':int(r),'channels':int(d.shape[1]),'peak':round(float(np.max(abs(x))),6),'rms':round(float(np.sqrt(np.mean(x*x))),6),'clipped_samples':int(np.count_nonzero(abs(x)>=.999))}
MET.write_text(json.dumps({'language':'Vietnamese','reference_text':REF_TEXT,'target_text_passed':TEXT,'normalization':'identity NFC','config':CFG,'generation_seconds':round(elapsed,3),'rtf':round(elapsed/a['duration_seconds'],3),'audio':a},ensure_ascii=False,indent=2)+'\n');print(json.dumps(a))
