#!/usr/bin/env python3
"""Manual, resumable Phase 30M Qwen VoiceDesign source generator."""
import gc, json, os, resource, time
from pathlib import Path
os.environ.setdefault("HF_HUB_OFFLINE", "1"); os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
import numpy as np, psutil, soundfile as sf, torch
from qwen_tts import Qwen3TTSModel
ROOT=Path(__file__).resolve().parent; PHASE=ROOT.parent/"phase30m"; MODEL=ROOT/"models/Qwen3-TTS-12Hz-1.7B-VoiceDesign"; PROMPTS=json.loads((PHASE/"prompts.json").read_text(encoding="utf-8")); OUT=PHASE/"sources"; MEASURE=PHASE/"measurements/source_generation.json"; IDS=("M-A","M-B","M-C")
def say(x): print(x,flush=True)
def mem():
 v,s=psutil.virtual_memory(),psutil.swap_memory(); return {"ram_available_bytes":v.available,"swap_used_bytes":s.used}
def audio(p):
 d,r=sf.read(p,always_2d=True); m=d.mean(axis=1); peak=float(np.max(np.abs(m))) if m.size else 0.; rms=float(np.sqrt(np.mean(m*m))) if m.size else 0.; clip=int(np.count_nonzero(np.abs(m)>=.999)); return {"duration_seconds":round(len(m)/r,3),"sample_rate":int(r),"channels":int(d.shape[1]),"peak":round(peak,6),"rms":round(rms,6),"clipped_samples":clip,"clipping_ratio":round(clip/max(1,len(m)),8)}
def valid(x): return x["duration_seconds"]>0 and x["clipping_ratio"]<=.01
def main():
 if not MODEL.is_dir() or not (MODEL/"model.safetensors").is_file() or not (MODEL/"speech_tokenizer/model.safetensors").is_file(): raise SystemExit("LOCAL_MODEL_REQUIRED")
 if set(PROMPTS["candidates"])!=set(IDS): raise SystemExit("exactly three M prompts required")
 before=mem(); say(f"[Phase30M] MemAvailable: {before['ram_available_bytes']/2**30:.2f} GiB; swap used: {before['swap_used_bytes']/2**30:.2f} GiB.")
 if before["ram_available_bytes"]<7*2**30: raise SystemExit("QWEN_RAM_BLOCKED")
 if before["ram_available_bytes"]<8*2**30: say("[Phase30M] WARNING: below preferred 8 GiB.")
 OUT.mkdir(parents=True,exist_ok=True); MEASURE.parent.mkdir(parents=True,exist_ok=True); say("[Phase30M] Loading local CPU Qwen..."); model=Qwen3TTSModel.from_pretrained(str(MODEL),device_map="cpu",dtype=torch.bfloat16,attn_implementation="eager"); records=[]
 try:
  for n,i in enumerate(IDS,1):
   target=OUT/f"m_{i[-1]}.wav"
   if target.is_file() and valid(audio(target)): records.append({"identity":i,"preserved_existing":True,"prompt":PROMPTS["candidates"][i],"audio":audio(target)}); say(f"[{n}/3] {i} preserved."); continue
   for attempt in (1,2):
    tmp=target.with_name(f".{target.stem}.attempt{attempt}.tmp.wav"); started=time.perf_counter()
    try:
     with torch.inference_mode(): wavs,rate=model.generate_voice_design(text=PROMPTS["english_reference_text"],language="English",instruct=PROMPTS["candidates"][i])
     sf.write(tmp,wavs[0],rate); a=audio(tmp)
     if valid(a): tmp.replace(target); records.append({"identity":i,"attempt":attempt,"generation_seconds":round(time.perf_counter()-started,3),"prompt":PROMPTS["candidates"][i],"audio":a,"peak_process_rss_mb":round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,2)}); say(f"[{n}/3] {i} saved."); break
    except Exception as e: say(f"[{i}] technical failure: {e!r}")
    if attempt==2: raise RuntimeError(f"{i} failed after one retry")
 finally: del model; gc.collect()
 MEASURE.write_text(json.dumps({"model":"Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign","offline":True,"device":"cpu","dtype":"torch.bfloat16","memory_before_load":before,"records":records},ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); say("[Phase30M] all sources finished.")
if __name__=="__main__": main()
