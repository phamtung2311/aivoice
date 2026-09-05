from pathlib import Path
import hashlib, json
from backend.app.tts.engine import TTSEngine
from backend.app.tts.podcast_voices import PODCAST_VOICES, resolve_podcast_voice
ROOT=Path(__file__).parent; OUT=ROOT/'outputs'; OUT.mkdir(parents=True,exist_ok=True)
texts={'A':'Có những lúc, điều khiến chúng ta mệt mỏi nhất\nkhông phải là công việc quá nhiều,\nmà là cảm giác mình đã đi rất lâu nhưng vẫn chưa biết\ncon đường phía trước sẽ dẫn đến đâu.\n\nTa cố gắng tìm một câu trả lời thật nhanh,\ntrong khi có những điều chỉ có thể hiểu được\nsau khi đã sống cùng nó đủ lâu.\n\nVà đôi khi,\nviệc cần làm không phải là bước nhanh hơn,\nmà chỉ là cho mình một chút thời gian để nhìn lại.', 'B':'Buổi sáng, quán cà phê vẫn đông như mọi ngày.\n\nNgười phục vụ đặt tách trà xuống bàn,\nngoài cửa kính là dòng xe đang chậm rãi đi qua.\n\nAnh mở cuốn sổ đã mang theo từ lâu,\nnhưng hôm nay lại không viết gì cả.\n\nCó lẽ không phải ngày nào cũng cần tạo ra một điều gì đó.\n\nĐôi khi,\nchỉ cần ngồi yên và nhận ra mình đang có mặt ở đây\ncũng đã là một cách để nghỉ ngơi.'}
engine=TTSEngine(backend='onnx')
rows=[]
for ident,meta in PODCAST_VOICES.items():
 for suffix,text in texts.items():
  p=OUT/f"voice{meta['phase43a_voice']}_unseen_{suffix}.wav"
  if not p.exists(): engine.generate(text,voice=ident,voice_profile=resolve_podcast_voice(ident),out_path=p,speed=1.0,temperature=.8,top_k=25,top_p=.95,repetition_penalty=1.2,repetition_window=64,denoise=True,use_ref_codes=True,max_new_frames=800,silence_p=.15,crossfade_p=.0,apply_watermark=True,batch_size=1,model_max_chars=800,expected_sample_rate=48000,preplanned_text=True)
  rows.append({'id':ident,'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(ROOT/'metadata').mkdir(exist_ok=True); (ROOT/'metadata'/'smoke_manifest.json').write_text(json.dumps(rows,indent=2)+'\n')
