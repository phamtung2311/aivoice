#!/usr/bin/env python3
"""Protect Phase 30M finalists; no audio generation or processing."""
import hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parent; P=ROOT.parent/'phase30m'; K=ROOT.parent/'keepers'
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def valid(m):
 for k in m['keepers']:
  for a in k['files'].values():
   p=Path(a['path']); assert p.is_file() and p.stat().st_size==a['size_bytes'] and h(p)==a['sha256'],p
def main():
 mp=K/'KEEPERS_MANIFEST.json';m=json.loads(mp.read_text());valid(m);mapping=json.loads((P/'private_mapping.json').read_text());assert mapping['04']=='M-A' and mapping['02']=='M-C'
 prompts=json.loads((P/'prompts.json').read_text()); src=json.loads((P/'measurements/source_generation.json').read_text());vie=json.loads((P/'measurements/vieneu_generation.json').read_text())
 for blind,identity,status in [('04','M-A','PRIMARY_DISTINCTIVENESS_FINALIST'),('02','M-C','SECONDARY_DISTINCTIVENESS_FINALIST')]:
  kid=f'phase30m_{blind}';d=K/kid;assert not d.exists(),d;d.mkdir();suffix=identity[-1].lower();internal=P/'internal'/f'm_{suffix}'
  for s,n in [(P/'sources'/f'm_{identity[-1]}.wav','qwen_source.wav'),(internal/'speaker_emb.npy','speaker_emb.npy'),(internal/'reference_codes.npy','reference_codes.npy'),(internal/'test_01.wav','test_01.wav'),(internal/'test_02.wav','test_02.wav')]: shutil.copy2(s,d/n)
  sm=next(x for x in src['records'] if x['identity']==identity); vm=[x for x in vie['records'] if x['identity']==identity]
  (d/'source_measurements.json').write_text(json.dumps(sm,ensure_ascii=False,indent=2)+'\n');(d/'vieneu_measurements.json').write_text(json.dumps(vm,ensure_ascii=False,indent=2)+'\n')
  meta={'keeper_id':kid,'phase':'30M','blind_number':blind,'identity':identity,'keeper_status':status,'user_verdict':'primary selected; pause diagnosis pending controlled refinement' if blind=='04' else 'secondary selected','english_generation_text':prompts['english_reference_text'],'voicedesign_prompt':prompts['candidates'][identity],'audio_modified':False};(d/'metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
  files={p.name:{'path':str(p),'size_bytes':p.stat().st_size,'sha256':h(p)} for p in sorted(d.iterdir())};m['keepers'].append({'keeper_id':kid,'phase30m_blind_number':blind,'original_identity':identity,'keeper_status':status,'files':files})
 mp.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n');valid(m);print('Phase30M finalists protected')
if __name__=='__main__':main()
