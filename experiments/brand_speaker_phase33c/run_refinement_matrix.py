#!/usr/bin/env python3
"""Finite Phase 33C Candidate 03 matrix; never alters the frozen anchor."""
from __future__ import annotations
import gc, hashlib, json, random, resource, sys, time
from pathlib import Path
import numpy as np
import soundfile as sf

HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[1]; sys.path.insert(0,str(ROOT))
ANCHOR=HERE/'baseline_anchor/BRAND_CANDIDATE_03_BASELINE'; RAW=HERE/'raw_outputs'; AUDITION=HERE/'audition'; METRICS=HERE/'metrics/metrics.json'; MAP=HERE/'private_mapping.json'
SEED=33131; TARGET_RMS=.09; PEAK=.95
PASSAGES={
 'Passage_1': 'Có những buổi sáng, điều ta cần nhất chỉ là một câu chuyện mở đầu thật gần gũi. Hôm nay, chúng ta sẽ bắt đầu từ một điều nhỏ, rồi cùng đi chậm rãi qua phần còn lại của ngày.',
 'Passage_2': 'Một kênh nội dung đáng nhớ không nhất thiết phải nói điều thật lớn lao trong mọi tập phát. Đôi khi giá trị nằm ở cách một ý tưởng quen thuộc được kể lại rõ ràng, có nhịp điệu và có khoảng để người nghe tự liên hệ với trải nghiệm của mình. Khi giọng nói giữ được sự tự nhiên, câu chuyện có thể đi xa hơn mà không cần cố gắng gây ấn tượng.',
 'Passage_3': 'Trong bản tổng kết tháng 9 năm 2026, nhóm nội dung của Minh, Hương và Quốc ghi nhận ba thay đổi đơn giản. Thứ nhất, lịch đăng được chia theo từng chủ đề để mọi người biết việc nào cần hoàn thành trước. Thứ hai, mỗi video đều có một phần mở đầu ngắn, sau đó mới đến ví dụ và phần giải thích dài hơn. Thứ ba, phản hồi của khán giả được đọc vào chiều thứ Sáu, không phải để chạy theo mọi ý kiến, mà để nhận ra câu hỏi nào xuất hiện nhiều lần. Ví dụ, khi người nghe hỏi về chi phí 250 nghìn đồng, thời gian 3,5 giờ, hoặc cách phát âm tên Nguyễn Thị Ánh, người viết cần đưa chi tiết đó vào đúng ngữ cảnh. Cách làm này giúp câu chuyện rõ hơn, giảm việc sửa lại từ đầu, và giữ cho những tập tiếp theo có cùng một chất giọng quen thuộc.',
}
# No identity control exists beyond the paired anchor. These are deliberately small
# sampling-only render hypotheses; speed, text, conditioning and join policy are fixed.
VARIANTS={
 'A': {'label':'baseline','temperature':.80,'top_k':25,'top_p':.95,'repetition_penalty':1.20},
 'B': {'label':'natural','temperature':.72,'top_k':25,'top_p':.95,'repetition_penalty':1.20},
 'C': {'label':'stable','temperature':.65,'top_k':20,'top_p':.90,'repetition_penalty':1.25},
 'D': {'label':'signature','temperature':.82,'top_k':25,'top_p':.97,'repetition_penalty':1.15},
}
def met(p):
 d,r=sf.read(p,always_2d=True); x=d.mean(1); clip=int(np.count_nonzero(abs(x)>=.999)); return {'duration_seconds':round(len(x)/r,3),'sample_rate':int(r),'channels':int(d.shape[1]),'peak':round(float(np.max(abs(x))),6),'rms':round(float(np.sqrt(np.mean(x*x))),6),'clipped_samples':clip,'clipping_ratio':round(clip/max(1,len(x)),8),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def valid(x): return x['duration_seconds']>0 and x['sample_rate']==48000 and x['channels']==1 and x['clipping_ratio']<=.01
def main():
 from backend.app.tts.engine import TTSEngine
 manifest=json.loads((ANCHOR/'manifest.json').read_text());
 for name,item in manifest['files'].items():
  p=ANCHOR/name
  if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=item['sha256']: raise SystemExit('BASELINE_ANCHOR_INTEGRITY_FAILED')
 emb=np.load(ANCHOR/'speaker_emb.npy',allow_pickle=False); codes=np.load(ANCHOR/'reference_codes.npy',allow_pickle=False)
 if emb.shape!=(192,) or codes.ndim!=2: raise SystemExit('ANCHOR_CONDITIONING_INVALID')
 for d in (RAW,AUDITION,METRICS.parent): d.mkdir(parents=True,exist_ok=True)
 engine=TTSEngine(backend='onnx'); rows=[]
 try:
  for passage,text in PASSAGES.items():
   for key,params in VARIANTS.items():
    target=RAW/passage/f'variant_{key}.wav'; target.parent.mkdir(parents=True,exist_ok=True)
    if target.is_file() and valid(met(target)):
     rows.append({'passage':passage,'variant':key,'preserved_existing':True,'audio':met(target),'parameters':params});continue
    tmp=target.with_name('.'+target.stem+'.tmp.wav'); started=time.perf_counter(); np.random.seed(SEED)
    print(f'[{passage} {key}] generating',flush=True)
    engine.generate(text,voice={'speaker_emb':emb,'codes':codes},speed=1.0,out_path=str(tmp),max_chunk_chars=240,denoise=False,use_ref_codes=True,quality_diagnostics=True,**{k:v for k,v in params.items() if k!='label'})
    a=met(tmp)
    if not valid(a): raise RuntimeError(f'INVALID_OUTPUT {passage} {key}: {a}')
    tmp.replace(target); rows.append({'passage':passage,'variant':key,'generation_seconds':round(time.perf_counter()-started,3),'rtf':round((time.perf_counter()-started)/a['duration_seconds'],4),'audio':met(target),'parameters':params,'diagnostics':engine.last_generation_diagnostics,'peak_process_rss_mb':round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,2)})
 finally: del engine;gc.collect()
 if len(rows)!=12: raise RuntimeError('PHASE33C_INCOMPLETE')
 if MAP.exists(): mapping=json.loads(MAP.read_text());
 else:
  order=list(VARIANTS);random.Random(SEED).shuffle(order);mapping={f'Clip_{chr(65+i)}.wav':v for i,v in enumerate(order)};MAP.write_text(json.dumps(mapping,indent=2)+'\n')
 if set(mapping)!=set(f'Clip_{x}.wav' for x in 'ABCD') or set(mapping.values())!=set(VARIANTS): raise SystemExit('PRIVATE_MAPPING_INVALID')
 audition={}
 for passage in PASSAGES:
  dest=AUDITION/passage;dest.mkdir(exist_ok=True)
  for public,key in mapping.items():
   data,sr=sf.read(RAW/passage/f'variant_{key}.wav',dtype='float32',always_2d=False);rms=float(np.sqrt(np.mean(data*data)));peak=float(np.max(abs(data)));gain=TARGET_RMS/rms if rms>1e-9 else 1.;gain=min(gain,PEAK/peak) if peak>1e-9 else gain
   out=dest/public;sf.write(out,data*gain,sr,subtype='PCM_16'); a=met(out)
   if a['clipped_samples']: raise RuntimeError('AUDITION_CLIPPED')
   audition.setdefault(passage,{})[public]={'gain':round(gain,6),'audio':a}
 METRICS.write_text(json.dumps({'phase':'33C','anchor':'BRAND_CANDIDATE_03_BASELINE','settings_common':{'speed':1.0,'max_chunk_chars':240,'denoise':False,'use_ref_codes':True,'seed':SEED},'variants':VARIANTS,'passages':PASSAGES,'outputs':rows,'audition_presentation':audition},ensure_ascii=False,indent=2)+'\n')
 print('PHASE33C_REFINEMENT_AUDITION_READY',flush=True)
if __name__=='__main__': raise SystemExit(main())
