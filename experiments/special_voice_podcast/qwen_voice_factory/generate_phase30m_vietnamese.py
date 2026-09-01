#!/usr/bin/env python3
"""Phase 30M finite, resumable VieNeu bridge; never loads Qwen."""
import gc,hashlib,json,os,random,resource,shutil,sys,time
from pathlib import Path
import numpy as np, soundfile as sf
ROOT=Path(__file__).resolve().parent; PROJECT=ROOT.parents[2]; PHASE=ROOT.parent/"phase30m"; KEEPERS=ROOT.parent/"keepers"
TEXTS={"test_01":"Có những điều nghe qua tưởng như rất đơn giản, nhưng khi dành thêm một chút thời gian để suy nghĩ, chúng ta lại thấy phía sau đó là cả một câu chuyện dài. Và có lẽ điều thú vị nhất không nằm ở việc tìm ra câu trả lời thật nhanh, mà ở cách mỗi người tự nhìn lại trải nghiệm của mình, rồi nhận ra một điều mà trước đây mình chưa từng chú ý.","test_02":"Một giọng nói phù hợp với podcast không nhất thiết phải là giọng gây ấn tượng mạnh ngay từ câu đầu tiên. Điều quan trọng hơn là người nghe cảm thấy tự nhiên, dễ chịu và vẫn muốn tiếp tục nghe sau nhiều phút. Khi chất giọng có một nét riêng vừa đủ, nó có thể trở thành dấu hiệu nhận biết của cả một kênh nội dung mà không cần phải cố tình phô trương."}
IDS=("CONTROL","M-A","M-B","M-C")
def say(x): print(x,flush=True)
def met(p):
 d,r=sf.read(p,always_2d=True); m=d.mean(1); c=int(np.count_nonzero(np.abs(m)>=.999)); return {"duration_seconds":round(len(m)/r,3),"sample_rate":int(r),"channels":int(d.shape[1]),"peak":round(float(np.max(np.abs(m))),6) if m.size else 0.,"rms":round(float(np.sqrt(np.mean(m*m))),6) if m.size else 0.,"clipped_samples":c,"clipping_ratio":round(c/max(1,len(m)),8),"finite":bool(np.isfinite(d).all())}
def valid(x): return x["duration_seconds"]>0 and x["channels"]==1 and x["finite"] and x["clipping_ratio"]<=.01
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 sys.path.insert(0,str(PROJECT)); from backend.app.tts.engine import TTSEngine
 refs={"CONTROL":KEEPERS/"phase30k_04/qwen_source.wav",**{f"M-{x}":PHASE/"sources"/f"m_{x}.wav" for x in "ABC"}}
 if not all(p.is_file() and valid(met(p)) for p in refs.values()): raise SystemExit("SOURCE_VALIDATION_FAILED")
 cond={"CONTROL":(KEEPERS/"phase30k_04/speaker_emb.npy",KEEPERS/"phase30k_04/reference_codes.npy")}; out=PHASE/"internal"; measure=PHASE/"measurements/vieneu_generation.json"; audition=PHASE/"audition"; out.mkdir(parents=True,exist_ok=True); (ROOT/".vieneu_runtime_home/.cache/vieneu/tmp").mkdir(parents=True,exist_ok=True)
 engine=TTSEngine(backend="onnx"); os.environ["HOME"]=str(ROOT/".vieneu_runtime_home"); records=[]
 try:
  for i in IDS:
   d=out/("control" if i=="CONTROL" else "m_"+i[-1].lower()); d.mkdir(parents=True,exist_ok=True); ep,cp=cond.get(i,(d/"speaker_emb.npy",d/"reference_codes.npy"))
   if ep.exists() and cp.exists(): emb,codes=np.load(ep,allow_pickle=False),np.load(cp,allow_pickle=False); enc=None
   else:
    t=time.perf_counter(); emb,codes=engine._model.encode_reference(str(refs[i]),denoise=False,use_ref_codes=True); enc=round(time.perf_counter()-t,3); np.save(ep,emb);np.save(cp,codes)
   for test,text in TEXTS.items():
    target=d/f"{test}.wav"
    if target.is_file() and valid(met(target)): records.append({"identity":i,"test":test,"preserved_existing":True,"audio":met(target),"technical_status":"valid"}); continue
    for attempt in (1,2):
     tmp=target.with_name(f".{target.stem}.attempt{attempt}.tmp.wav"); t=time.perf_counter()
     try:
      np.random.seed(30109); engine.generate(text,voice={"speaker_emb":emb,"codes":codes},speed=1.0,out_path=str(tmp),denoise=False,use_ref_codes=True,quality_diagnostics=True); a=met(tmp)
      if valid(a): tmp.replace(target); records.append({"identity":i,"test":test,"attempt":attempt,"encode_seconds":enc,"generation_seconds":round(time.perf_counter()-t,3),"speaker_emb_shape":list(emb.shape),"reference_codes_shape":list(codes.shape),"audio":a,"peak_process_rss_mb":round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,2),"technical_status":"valid"}); say(f"[{i}] {test} saved"); break
     except Exception as e: say(f"[{i}] {test} technical failure: {e!r}")
     if attempt==2: raise RuntimeError(f"{i} {test} failed")
 finally: del engine;gc.collect()
 if len(records)!=8: raise RuntimeError("PARTIAL")
 mapping_path=PHASE/"private_mapping.json"
 if mapping_path.exists():
  mapping=json.loads(mapping_path.read_text())
  if set(mapping)!=set(f"{n:02d}" for n in range(1,5)) or set(mapping.values())!=set(IDS): raise RuntimeError("invalid existing private mapping; refusing to remap")
 else:
  shuffled=list(IDS);random.Random(30109).shuffle(shuffled);mapping={f"{n:02d}":i for n,i in enumerate(shuffled,1)};mapping_path.write_text(json.dumps(mapping,indent=2)+"\n")
 audition.mkdir(exist_ok=True)
 for test in TEXTS:
  a=audition/test;a.mkdir(exist_ok=True)
  for n,i in mapping.items():
   source=out/("control" if i=="CONTROL" else "m_"+i[-1].lower())/f"{test}.wav";target=a/f"voice_{n}.wav"
   if not target.is_file() or digest(target)!=digest(source): shutil.copy2(source,target)
 measure.parent.mkdir(parents=True,exist_ok=True);measure.write_text(json.dumps({"settings":{"speed":1.0,"denoise":False,"numpy_seed":30109},"records":records},ensure_ascii=False,indent=2)+"\n");say("[Phase30M] PHASE30M_DISTINCTIVENESS_AUDITION_READY")
if __name__=="__main__": main()
