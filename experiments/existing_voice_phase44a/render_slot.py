"""Render exactly one Phase 44A released VieNeu preset/text slot."""
import argparse, hashlib, json, os, time
from pathlib import Path
import numpy as np, soundfile as sf
from vieneu import Vieneu
ROOT=Path(__file__).parent; OUT=ROOT/'outputs'; META=ROOT/'metadata'; OUT.mkdir(exist_ok=True); META.mkdir(exist_ok=True)
VOICES={'01':'Phạm Tuyên','02':'Minh Đức','03':'Thanh Bình','04':'Quang Sơn','05':'Xuân Vĩnh','06':'Thái Sơn','07':'Minh Triết','08':'Đức Trí'}
TEXTS={'A':'Có những ngày, chúng ta không thật sự buồn,\nnhưng cũng chẳng cảm thấy vui.\n\nMọi thứ vẫn diễn ra như bình thường,\ncông việc vẫn còn đó,\nnhững cuộc trò chuyện vẫn tiếp tục,\nnhưng trong lòng lại có một khoảng trống rất khó gọi tên.\n\nCó lẽ,\nđó là lúc chúng ta cần chậm lại một chút.\n\nKhông phải để tìm ngay một câu trả lời,\nmà chỉ để lắng nghe xem mình đang thực sự cần điều gì.', 'B':'Chiều hôm ấy, con đường trước nhà yên tĩnh hơn mọi ngày.\n\nMột cơn gió nhẹ đi qua,\nlàm những chiếc lá khô trên vỉa hè khẽ chuyển động.\n\nAnh ngồi bên cửa sổ,\ncầm tách trà đã nguội từ lúc nào,\nrồi bất giác nhớ lại những chuyện đã xảy ra trong vài năm vừa qua.\n\nCó những điều khi đang sống trong đó,\nta nghĩ rằng mình sẽ chẳng bao giờ quên.\n\nNhưng thời gian luôn có một cách rất riêng\nđể khiến mọi thứ dần trở nên nhẹ hơn.', 'C':'Đôi khi, điều khiến con người mệt mỏi không nằm ở việc phải đi quá xa,\nmà nằm ở cảm giác đã cố gắng rất lâu,\nđã thay đổi rất nhiều,\nnhưng vẫn chưa chắc rằng nơi mình đang hướng tới\ncó thực sự là nơi mình muốn đến hay không.'}
p=argparse.ArgumentParser(); p.add_argument('--voice',choices=VOICES); p.add_argument('--text',choices=TEXTS); a=p.parse_args(); dst=OUT/f'existing{a.voice}_{a.text}.wav'
if dst.exists() and dst.stat().st_size:
 i=sf.info(dst)
 if i.samplerate>0 and i.channels>0: print('REUSED',dst); raise SystemExit
t=time.perf_counter(); e=Vieneu(backend='onnx'); audio=np.asarray(e.infer(TEXTS[a.text],voice=VOICES[a.voice],denoise=True,use_ref_codes=True,temperature=.8,top_k=25,top_p=.95,repetition_penalty=1.2,repetition_window=64,max_new_frames=800,silence_p=.15,crossfade_p=.0,apply_watermark=True,batch_size=1),dtype=np.float32); tmp=dst.with_suffix('.tmp.wav'); sf.write(tmp,audio,e.sample_rate,subtype='PCM_16'); os.replace(tmp,dst); i=sf.info(dst)
if i.frames<=0 or i.samplerate!=48000 or i.channels!=1 or i.subtype!='PCM_16': raise RuntimeError('invalid WAV')
d=json.loads((META/'render_manifest.json').read_text()) if (META/'render_manifest.json').exists() else {}; d[f'{a.voice}_{a.text}']={'preset':VOICES[a.voice],'path':str(dst.relative_to(ROOT)),'sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'duration_seconds':i.frames/i.samplerate,'sample_rate':i.samplerate,'channels':i.channels,'attempts':1,'generation_seconds':time.perf_counter()-t}; q=META/'render_manifest.tmp'; q.write_text(json.dumps(d,ensure_ascii=False,indent=2)); os.replace(q,META/'render_manifest.json'); print('OK',dst)
