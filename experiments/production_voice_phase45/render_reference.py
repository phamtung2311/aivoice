import argparse
from pathlib import Path
from backend.app.tts.engine import TTSEngine
from backend.app.tts.podcast_voices import resolve_podcast_voice,PODCAST_VOICES
p=argparse.ArgumentParser();p.add_argument('voice',choices=PODCAST_VOICES);a=p.parse_args()
text='Có những lúc, chúng ta chỉ cần chậm lại một chút, để lắng nghe chính mình và hiểu điều gì thật sự quan trọng.'
d=Path('assets/production_voices/reference_audio');d.mkdir(parents=True,exist_ok=True)
TTSEngine(backend='onnx').generate(text,voice=a.voice,voice_profile=resolve_podcast_voice(a.voice),out_path=d/(a.voice+'_reference.wav'),speed=1.0,temperature=.8,top_k=25,top_p=.95,repetition_penalty=1.2,repetition_window=64,denoise=True,use_ref_codes=True,max_new_frames=800,silence_p=.15,crossfade_p=.0,apply_watermark=True,batch_size=1,model_max_chars=800,expected_sample_rate=48000,preplanned_text=True)
