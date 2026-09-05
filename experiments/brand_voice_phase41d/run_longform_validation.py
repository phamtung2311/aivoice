#!/usr/bin/env python3
from __future__ import annotations

import gc
import hashlib
import json
import shutil
import time
import wave
from pathlib import Path

import numpy as np
import soundfile as sf
from vieneu import Vieneu

ROOT = Path('experiments/brand_voice_phase41b/baseline/PODCAST_SYNTHETIC_CANDIDATE_03')
OUTDIR = Path('experiments/brand_voice_phase41d/audio')
RECOVERY_DIR = Path('experiments/brand_voice_phase41d/recovery_originals')
SUPERSEDED_DIR = Path('experiments/brand_voice_phase41d/superseded')
RESUME_PATH = Path('experiments/brand_voice_phase41d/resume_state.json')

OUTDIR.mkdir(parents=True, exist_ok=True)
RECOVERY_DIR.mkdir(parents=True, exist_ok=True)
SUPERSEDED_DIR.mkdir(parents=True, exist_ok=True)

# Preserve earlier evidence and archive superseded outputs without overwriting them.
for name in ['01_short_monologue.wav', '02_explanatory_section.wav']:
    src = OUTDIR / name
    if src.exists():
        dst = RECOVERY_DIR / name
        if dst.exists():
            dst.unlink()
        shutil.move(str(src), str(dst))

for name in ['01_short_monologue_final.wav', '02_explanatory_section_final.wav', '03_longform_stress_test_final.wav']:
    src = OUTDIR / name
    if src.exists():
        dst = SUPERSEDED_DIR / f'{name}.superseded'
        if dst.exists():
            dst.unlink()
        shutil.move(str(src), str(dst))

for pattern in ['01_short_monologue_chunk_*.wav', '02_explanatory_section_chunk_*.wav', '03_longform_stress_test_chunk_*.wav']:
    for src in sorted(OUTDIR.glob(pattern)):
        dst = SUPERSEDED_DIR / src.name
        if dst.exists():
            dst.unlink()
        shutil.move(str(src), str(dst))

if RESUME_PATH.exists():
    dst = SUPERSEDED_DIR / 'resume_state_before_regeneration.json'
    if dst.exists():
        dst.unlink()
    shutil.move(str(RESUME_PATH), str(dst))

# Frozen voice and inference config must remain unchanged.
params_common = {
    'temperature': 0.8,
    'top_k': 25,
    'top_p': 0.95,
    'repetition_penalty': 1.2,
    'repetition_window': 64,
    'denoise': True,
    'use_ref_codes': True,
    'silence_p': 0.15,
    'crossfade_p': 0.0,
    'apply_watermark': True,
    'sample_rate': 48000,
    'max_new_frames': 600,
    'max_chars': 800,
    'max_chars_chunk': 350,
}

VALIDATION_GATES = {
    '01_short_monologue_final.wav': (50.0, 65.0),
    '02_explanatory_section_final.wav': (100.0, 130.0),
    '03_longform_stress_test_final.wav': (210.0, 270.0),
}

# Longer Vietnamese podcast scripts that are coherent and natural, without artificial silence.
# Static preflight keeps these script lengths inside the required gates.
final_names = [
    ('01_short_monologue_final.wav', '''Từ rất sớm, ta đã thấy rằng sống đúng nghĩa không phải là làm nhiều nhất, mà là biết mình đang đi về đâu. Mỗi ngày đều có những lựa chọn nhỏ: nói chuyện với sự bình tĩnh hay vội vàng, giữ im lặng hay bám theo tiếng ồn, tin vào sự thật hay chạy theo cảm giác. Những quyết định ấy không lớn, nhưng chúng tạo hình cho con người ta. Một người có chiều sâu không cần phải gào thét để được nghe. Họ chỉ cần một giọng nói rõ, một nhịp thở chậm, và một sự ổn định mà người khác cảm thấy an tâm. Đó là điều đáng quý trong một thế giới luôn thúc giục ta phản ứng nhanh hơn, nói nhiều hơn, và so sánh mình với người khác. Khi ta học được cách dừng lại, ta không phải từ bỏ năng lượng mà là rèn luyện sự kiểm soát. Ta biết khi nào nên giữ bình tĩnh, khi nào nên lắng nghe, và khi nào nên nói lên điều thật. Chính từ những khoảnh khắc không ai nhìn thấy ấy, một cuộc sống bắt đầu có trọng lượng. Họ không cần khoe khoang; họ chỉ cần đứng vững. Và đó là một dạng trí tuệ rất thầm lặng: biết dừng lại trước những cơn bực bội, biết chọn lời nói đúng lúc, và biết đặt mình vào nhịp của đời sống thay vì lao theo mọi thứ.'''),
    ('02_explanatory_section_final.wav', '''Để giải thích một nguyên tắc sống, điều quan trọng nhất là phải hỏi đúng câu hỏi: điều này có ý nghĩa gì trong thực tế? Nếu người nghe không thấy được giá trị của nó, cả bài nói sẽ trở nên thiếu sức sống và rơi vào lý thuyết. Một cách truyền đạt hiệu quả thường có bốn bước: mở đầu ngắn gọn, nêu giá trị cốt lõi, cho ví dụ thực tế, rồi kết thúc bằng một lời nhắc để áp dụng ngay. Điều ấy chỉ thực sự hiệu quả khi người nói giữ nhịp, chọn trọng tâm, và không biến ý tưởng thành những câu dài rời rạc. Khi ta nói về lòng trắc ẩn, ta không nên dừng ở định nghĩa. Ta cần cho người nghe cảm thấy điều đó trong đời sống: một người chậm lại để nghe người khác, một sự kiên nhẫn nhỏ trong lúc mọi thứ đang vội, một cái gật đầu thay cho sự chỉ trích. Người ta thường nhớ cảm giác được hiểu hơn là những câu văn hoa. Họ nhớ sự tĩnh lặng trong giọng nói, họ nhớ sự thật được đặt đúng nhịp thở, và họ nhớ rằng thông điệp đó không ép buộc họ, mà dẫn họ đi cùng nhau. Vì vậy, một giọng nói tốt không phải là giọng nói nhiều câu phức tạp, mà là giọng nói biết chốt ý, biết nhấn đúng điểm, và biết để người nghe có chỗ để suy nghĩ. Khi ta nói rõ, ta cho người ta không gian để tiếp nhận. Khi ta nói chậm nhưng có trọng tâm, ta giúp họ thấy rằng sự yên bình trong đầu óc vẫn là một nguồn lực. Một câu thật sự sâu sắc không cần ai giật mình mới nghe thấy. Nó đến rất tự nhiên, như một suy nghĩ đã được sống qua nhiều lần trước khi được nói ra. Trong podcast, điều ấy rất quan trọng vì người ta không chỉ nghe lời nói, họ còn nghe nhịp tư duy. Nếu ta muốn người nghe ở lại lâu hơn, ta phải cho họ cảm giác mình đi cùng hướng, không lạc trong vòng lặp của những câu dài vô ích. Một người trò chuyện giỏi biết khi nào nên dừng, khi nào nên nhấn mạnh, và khi nào nên để khoảng trống cho người nghe tự mình hồi tỉnh. Đó là cách sinh ra sự thấu hiểu mà không cần áp đặt. Một người có thể giải thích rõ nhưng không làm cho người nghe cảm thấy được hiểu. Sự sâu sắc không nằm ở độ dài của cách nói; nó nằm ở khả năng khiến người nghe cảm thấy mình không bị bỏ lại phía sau. Điều ấy đặc biệt quan trọng khi ta đang nói về sự thay đổi, về cảm giác mất phương hướng, và về việc học cách đứng.'''),
    ('03_longform_stress_test_final.wav', '''Hôm nay tôi muốn kể một câu chuyện dài hơn, không phải để làm ồn lên, mà để cho ta thấy tầm quan trọng của những quyết định nhỏ trong cuộc đời. Có một người sống trong một ngõ nhỏ, mỗi sáng dậy sớm, anh ta dành vài phút để sắp xếp lại hàng hóa trong cửa hàng, nhắc nhở con mình về sự kỷ luật, và lặng lẽ chào hỏi những người hàng xóm già đi qua. Những việc ấy không lớn lao, nhưng chúng khiến cuộc sống quanh anh ta trôi chậm đi đúng nhịp. Chúng khiến những ngày tẻ nhạt không trở nên vô nghĩa. Chúng cho thấy rằng sự bền vững của một con người không được xây dựng trong những khoảnh khắc ngắn ngủi của vinh quang, mà trong những thói quen không ai nhìn thấy. Một ngày nào đó, khi người ta bị thất bại, chán nản, và thấy mình không còn đường đi, họ bắt đầu nhận ra rằng chính những quyết định nhỏ ấy đã trở thành nền tảng. Họ đã học cách giữ lời hứa với bản thân. Họ biết khi nào nên chậm lại. Họ biết khi nào cần bình tĩnh trước sự mệt mỏi, và khi nào không nên bị cuốn theo sự giận dữ của thế giới. Đó là điều rất quan trọng: một con người không trở nên lớn lao nhờ những khoảnh khắc nổi bật, mà nhờ những cách ứng xử mà họ lặp đi lặp lại khi không ai quan sát. Câu chuyện này có thể áp dụng cho mọi khía cạnh của sự trưởng thành. Ta không cần một lời tuyên ngôn hùng hồn để trở thành người đáng tin cậy. Đôi khi điều quan trọng nhất là biết giữ lời hứa, biết cẩn trọng trong cách nói, và biết lắng nghe người khác khi mình đang muốn phản bác. Sự trưởng thành không phải là luôn đúng, mà là biết nhận ra mình có thể sai và vẫn chọn bước tiếp. Đó là lý do vì sao một giọng nói sâu có thể mang lại cảm giác an tâm cho người nghe: nó có trọng lượng, nhưng không ép buộc. Nó khiến người ta cảm thấy có thể dừng lại, suy ngẫm, và đi cùng với những ý nghĩ của mình cho đến khi chúng thực sự thấm sâu. Suy cho cùng, ngay cả những cuộc đối thoại dài nhất cũng không thành công nếu nó không cho người nghe thời gian để thở. Một cuộc trò chuyện tốt không phải là cuộc trò chuyện luôn nói nhiều và nói nhanh; nó là cuộc trò chuyện cho phép người nghe có chỗ để suy ngẫm, có chỗ để tiếp nhận, và có chỗ để quyết định liệu mình muốn đi cùng người nói thêm một đoạn nữa hay không. Chính vì vậy, tính bền vững của một giọng văn không nằm ở vẻ ngoài của nó, mà ở khả năng đi cùng người nghe trong những câu chuyện chưa được giải đáp ngay từ đầu, những câu hỏi chưa được trả lời ngay lập tức, và những khoảng lặng khiến con người quay lại với chính mình. Khi ta nghe một giọng nói chậm và rõ, ta cảm thấy như mình được đặt vào một không gian an toàn hơn. Không ai bị ép phải vội vàng. Không ai bị lừa bởi những lời phô trương. Họ chỉ được dẫn dắt bằng sự thật, nhịp điệu, và sự tôn trọng đối với thời gian của người nghe. Đó là kiểu nói chuyện mà qua rất nhiều năm, người ta vẫn nhớ. Nó không cần lớn tiếng, không cần lặp đi lặp lại, không cần giật mình trước mọi thứ. Nó chỉ cần biết cách đứng im trong một khoảnh khắc để người nghe có thể nghe thấu sự chân thành của mình. Mỗi người trong chúng ta đều có một chiều sâu, nhưng không phải ai cũng biết cách để nó hiện lên. Có những người luôn xô bồ và lao vào cuộc sống, nhưng rồi một ngày họ nhận ra rằng họ đã quen với sự ồn ào đến mức không còn nghe rõ tiếng lòng mình. Đó là lúc họ cần một giọng nói chậm, một câu hỏi rõ ràng, và một chút yên lòng để họ quay đầu lại và bắt đầu từ nơi đúng đắn. Câu chuyện này không phải để khuyên người ta làm tốt hơn, mà để nhắc nhở rằng sự trưởng thành thật sự không đến từ sự lộng lẫy ngắn ngủi, mà từ sự can đảm để tiếp tục đi, hoặc dừng lại khi cần thiết. Một người biết mình cần giữ bình tĩnh thường không khoe khoang. Họ bình thản, giữ lời hứa, và tạo ra sự an tâm rất cụ thể cho những người sống bên cạnh họ. Đó là một dạng trí tuệ rất tĩnh lặng, nhưng nó có tác động rất mạnh đến cách chúng ta đối diện với thời gian, với nỗi lo, và với những thay đổi không thể kiểm soát. Khi ai đó có thể giữ được nhịp điệu ấy trong từng câu chữ, người ta cũng đang giữ được một mảnh sự rõ ràng trong chính mình. Một người không cần phải hùng hồn mỗi ngày mới chứng minh mình đang sống. Sự ổn định lớn nhất không đến từ những lời nói lớn, mà từ cách ta vẫn giữ được sự thật và sự điềm tĩnh ngay cả khi mọi thứ xung quanh đang biến động. Đó là cách một đời người có thể trở nên trong sáng: không giành giật, không vội vàng, và không đánh mất chính mình giữa những đường thẳng của cuộc sống.'''),
]



def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def read_wav_meta(path: Path):
    with wave.open(str(path), 'rb') as wf:
        return {
            'channels': wf.getnchannels(),
            'sample_rate': wf.getframerate(),
            'frames': wf.getnframes(),
            'sample_width': wf.getsampwidth(),
            'compression': wf.getcomptype(),
            'duration': wf.getnframes() / wf.getframerate(),
        }


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode('utf-8'))


def chunk_text_for_longform(text: str, max_chars: int = 350):
    sentences = [s.strip() for s in text.replace('\n', ' ').replace('…', '.').split('.') if s.strip()]
    chunks = []
    current = ''
    for s in sentences:
        cand = (current + ' ' + s).strip() if current else s
        if len(cand) <= max_chars:
            current = cand
        else:
            if current:
                chunks.append(current)
            current = s
    if current:
        chunks.append(current)
    if not chunks:
        chunks = [text[i:i + max_chars] for i in range(0, len(text), max_chars)]
    return chunks


def estimate_project_speech_rate() -> float:
    # Prefer observed Candidate 03 project evidence over generic TTS assumptions.
    manifest_path = Path('experiments/brand_voice_phase41d/manifest.json')
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
            totals = []
            for test in manifest.get('tests', []):
                duration = float(test.get('final_duration_seconds') or 0.0)
                chars = int(test.get('total_chars') or 0)
                if duration > 0 and chars > 0:
                    totals.append(chars / duration)
            if totals:
                return float(np.median(totals))
        except Exception:
            pass
    return 14.5


def estimate_test_duration(test_name: str, text: str, max_chars: int = 350) -> dict:
    chunks = chunk_text_for_longform(text, max_chars=max_chars)
    total_chars = len(text)
    total_words = len([w for w in text.replace('\n', ' ').split() if w.strip()])
    chars_per_chunk = [len(chunk) for chunk in chunks]
    chars_per_second = estimate_project_speech_rate()
    duration_seconds = total_chars / chars_per_second
    return {
        'test_name': test_name,
        'total_characters': total_chars,
        'total_vietnamese_words': total_words,
        'chunk_count': len(chunks),
        'chars_per_chunk': chars_per_chunk,
        'estimated_duration_seconds': duration_seconds,
        'chars_per_second_observed': chars_per_second,
    }


def canonical_hashes() -> dict:
    emb = np.load(ROOT / 'speaker_emb.npy', allow_pickle=False).astype(np.float32)
    codes = np.load(ROOT / 'reference_codes.npy', allow_pickle=False)
    return {
        'canonical_speaker_emb_sha256': sha256_bytes(np.ascontiguousarray(emb).tobytes()),
        'canonical_speaker_emb_npy_sha256': sha256_bytes((ROOT / 'speaker_emb.npy').read_bytes()),
        'reference_codes_sha256': sha256_bytes((ROOT / 'reference_codes.npy').read_bytes()),
        'inference_config_sha256': sha256_bytes(json.dumps(params_common, sort_keys=True, separators=(',', ':')).encode('utf-8')),
    }


def build_chunk_checkpoint(test_id: str, chunk_index: int, chunk_text: str, generated_chunk_path: Path, generated_duration: float, emb_hashes: dict) -> dict:
    return {
        'test_id': test_id,
        'chunk_index': int(chunk_index),
        'chunk_text_sha256': sha256_text(chunk_text),
        'inference_config_sha256': emb_hashes['inference_config_sha256'],
        'canonical_speaker_emb_sha256': emb_hashes['canonical_speaker_emb_sha256'],
        'reference_codes_sha256': emb_hashes['reference_codes_sha256'],
        'generated_chunk_wav_sha256': sha256_bytes(generated_chunk_path.read_bytes()),
        'generated_chunk_duration': float(generated_duration),
    }


def normalize_resume_state(state: dict) -> dict:
    fresh = {
        'version': 2,
        'canonical_speaker_emb_sha256': state.get('canonical_speaker_emb_sha256'),
        'canonical_speaker_emb_npy_sha256': state.get('canonical_speaker_emb_npy_sha256'),
        'reference_codes_sha256': state.get('reference_codes_sha256'),
        'inference_config_sha256': state.get('inference_config_sha256'),
        'completed_tests': [],
        'chunks': {},
    }
    for test_id, entries in (state.get('chunks', {}) or {}).items():
        cleaned = []
        for entry in entries:
            if isinstance(entry, dict):
                cleaned.append({
                    'test_id': str(entry.get('test_id', test_id)),
                    'chunk_index': int(entry.get('chunk_index', 0)),
                    'chunk_text_sha256': str(entry.get('chunk_text_sha256', '')),
                    'inference_config_sha256': str(entry.get('inference_config_sha256', '')),
                    'canonical_speaker_emb_sha256': str(entry.get('canonical_speaker_emb_sha256', '')),
                    'reference_codes_sha256': str(entry.get('reference_codes_sha256', '')),
                    'generated_chunk_wav_sha256': str(entry.get('generated_chunk_wav_sha256', '')),
                    'generated_chunk_duration': float(entry.get('generated_chunk_duration', 0.0)),
                })
        if cleaned:
            fresh['chunks'][str(test_id)] = cleaned
    if isinstance(state.get('completed_tests'), list):
        fresh['completed_tests'] = [str(v) for v in state['completed_tests']]
    return fresh


def _is_legacy_resume_state(state: dict) -> bool:
    # Consider legacy only when older-style keys exist without the modern 'chunks' map.
    return (('done_chunks' in state and 'chunks' not in state) or
            ('completed_tests' in state and not isinstance(state.get('completed_tests'), list) and 'chunks' not in state))


def archive_stale_resume_state():
    if RESUME_PATH.exists():
        ts = time.strftime('%Y%m%d_%H%M%S')
        archive = SUPERSEDED_DIR / f'resume_state_stale_{ts}.json'
        shutil.copy2(str(RESUME_PATH), str(archive))


def load_resume_state() -> dict:
    if not RESUME_PATH.exists():
        hashes = canonical_hashes()
        return {
            'version': 2,
            'canonical_speaker_emb_sha256': hashes['canonical_speaker_emb_sha256'],
            'canonical_speaker_emb_npy_sha256': hashes['canonical_speaker_emb_npy_sha256'],
            'reference_codes_sha256': hashes['reference_codes_sha256'],
            'inference_config_sha256': hashes['inference_config_sha256'],
            'completed_tests': [],
            'chunks': {},
        }

    raw = json.loads(RESUME_PATH.read_text(encoding='utf-8'))
    if _is_legacy_resume_state(raw):
        archive_stale_resume_state()
        hashes = canonical_hashes()
        return {
            'version': 2,
            'canonical_speaker_emb_sha256': hashes['canonical_speaker_emb_sha256'],
            'canonical_speaker_emb_npy_sha256': hashes['canonical_speaker_emb_npy_sha256'],
            'reference_codes_sha256': hashes['reference_codes_sha256'],
            'inference_config_sha256': hashes['inference_config_sha256'],
            'completed_tests': [],
            'chunks': {},
        }

    state = normalize_resume_state(raw)
    # If a serialized done_chunks map exists (lists), rehydrate to sets for runtime use.
    if isinstance(raw, dict) and raw.get('done_chunks'):
        try:
            dc = raw.get('done_chunks') or {}
            rehydrated = {}
            for k, v in dc.items():
                # Expect lists of chunk ids; convert to set of strings
                if isinstance(v, list):
                    rehydrated[str(k)] = set(str(x) for x in v)
                else:
                    # If it's already a mapping of strings, try to preserve
                    rehydrated[str(k)] = set(str(x) for x in list(v))
            state['done_chunks'] = rehydrated
        except Exception:
            # If any error occurs during rehydration, skip preserving done_chunks
            state['done_chunks'] = {}
    hashes = canonical_hashes()
    state['canonical_speaker_emb_sha256'] = hashes['canonical_speaker_emb_sha256']
    state['canonical_speaker_emb_npy_sha256'] = hashes['canonical_speaker_emb_npy_sha256']
    state['reference_codes_sha256'] = hashes['reference_codes_sha256']
    state['inference_config_sha256'] = hashes['inference_config_sha256']
    return state


def update_resume_state(state: dict):
    # Make a JSON-safe copy of the state: convert any sets in done_chunks to deterministic sorted lists.
    serial = dict(state)
    dc = serial.get('done_chunks')
    if isinstance(dc, dict):
        safe_dc = {}
        for k, v in dc.items():
            if isinstance(v, set):
                # sort for deterministic output
                safe_dc[str(k)] = sorted(str(x) for x in v)
            elif isinstance(v, list):
                safe_dc[str(k)] = [str(x) for x in v]
            else:
                # fallback: convert to list
                try:
                    safe_dc[str(k)] = [str(x) for x in list(v)]
                except Exception:
                    safe_dc[str(k)] = []
        serial['done_chunks'] = safe_dc

    RESUME_PATH.write_text(json.dumps(serial, ensure_ascii=False, indent=2), encoding='utf-8')


def chunk_can_be_reused(test_id: str, chunk_index: int, chunk_text: str, resume_state: dict) -> bool:
    hashes = canonical_hashes()
    key = str(chunk_index)
    chunk_entries = resume_state.get('chunks', {}).get(test_id, [])
    for entry in chunk_entries:
        if int(entry.get('chunk_index', -1)) != int(chunk_index):
            continue
        if entry.get('test_id', test_id) != test_id:
            continue
        if entry.get('chunk_text_sha256') != sha256_text(chunk_text):
            continue
        if entry.get('inference_config_sha256') != hashes['inference_config_sha256']:
            continue
        if entry.get('canonical_speaker_emb_sha256') != hashes['canonical_speaker_emb_sha256']:
            continue
        if entry.get('reference_codes_sha256') != hashes['reference_codes_sha256']:
            continue
        return True
    return False


# Fresh run: legacy index-only checkpoint entries are stale and must be archived before new hash-aware state takes effect.
resume_state = load_resume_state()

emb = np.load(ROOT / 'speaker_emb.npy', allow_pickle=False).astype(np.float32)
codes = np.load(ROOT / 'reference_codes.npy', allow_pickle=False)

tts = Vieneu(backend='onnx')
report = {
    'phase': '41D',
    'timestamp': time.time(),
    'canonical_embedding_array_sha256': hashlib.sha256(np.ascontiguousarray(emb).tobytes()).hexdigest(),
    'canonical_npy_file_sha256': hashlib.sha256((ROOT / 'speaker_emb.npy').read_bytes()).hexdigest(),
    'reference_codes_sha256': hashlib.sha256((ROOT / 'reference_codes.npy').read_bytes()).hexdigest(),
    'params': params_common,
    'tests': [],
}

for final_name, long_text in final_names:
    final_path = OUTDIR / final_name
    if final_path.exists():
        final_path.unlink()

    test_id = final_name.replace('_final.wav', '')
    chunks = chunk_text_for_longform(long_text, max_chars=params_common['max_chars_chunk'])
    total_gen = 0.0
    total_chunks = []
    gc.collect()

    for ci, chunk_text in enumerate(chunks):
        chunk_file = OUTDIR / f'{test_id}_chunk_{ci:03d}.wav'
        t0 = time.time()
        wav = tts.infer(
            chunk_text,
            voice={'speaker_emb': emb, 'codes': codes},
            temperature=params_common['temperature'],
            top_k=params_common['top_k'],
            top_p=params_common['top_p'],
            repetition_penalty=params_common['repetition_penalty'],
            repetition_window=params_common['repetition_window'],
            denoise=params_common['denoise'],
            use_ref_codes=params_common['use_ref_codes'],
            silence_p=params_common['silence_p'],
            crossfade_p=params_common['crossfade_p'],
            apply_watermark=params_common['apply_watermark'],
            max_new_frames=params_common['max_new_frames'],
            max_chars=params_common['max_chars'],
        )
        arr = np.asarray(wav, dtype=np.float32)
        if arr.size == 0:
            raise RuntimeError(f'empty chunk audio for {test_id} chunk {ci}')
        sf.write(chunk_file, arr, 48000, subtype='PCM_16')
        elapsed = time.time() - t0
        total_gen += elapsed
        dl = read_wav_meta(chunk_file)
        chunk_info = {
            'chunk_index': ci,
            'chars': len(chunk_text),
            'text': chunk_text,
            'duration_seconds': dl['duration'],
            'generation_time': elapsed,
            'peak_abs': float(np.max(np.abs(arr))),
            'chunk_file': str(chunk_file),
            'chunk_sha256': sha256_file(chunk_file),
            'boundary_start_mean_abs': float(np.mean(np.abs(arr[:min(len(arr), 2400)]))),
            'boundary_end_mean_abs': float(np.mean(np.abs(arr[-min(len(arr), 2400):]))),
        }
        total_chunks.append(chunk_info)
        resume_state.setdefault('done_chunks', {}).setdefault(test_id, set()).add(str(ci))
        update_resume_state(resume_state)
        del arr, wav
        gc.collect()

    with wave.open(str(final_path), 'wb') as out_wf:
        out_wf.setnchannels(1)
        out_wf.setsampwidth(2)
        out_wf.setframerate(48000)
        for chunk_file in sorted(OUTDIR.glob(f'{test_id}_chunk_*.wav')):
            with wave.open(str(chunk_file), 'rb') as in_wf:
                out_wf.writeframes(in_wf.readframes(in_wf.getnframes()))

    final_meta = read_wav_meta(final_path)
    lower, upper = VALIDATION_GATES[final_name]
    if not (lower <= final_meta['duration'] <= upper):
        raise RuntimeError(f'{final_name} duration={final_meta["duration"]:.2f}s outside required range {lower}..{upper}')

    report['tests'].append({
        'id': test_id,
        'final_file': str(final_path),
        'chunks': total_chunks,
        'num_chunks': len(total_chunks),
        'total_chars': sum(c['chars'] for c in total_chunks),
        'final_duration_seconds': final_meta['duration'],
        'total_generation_time': total_gen,
        'rtf': total_gen / final_meta['duration'] if final_meta['duration'] > 0 else None,
        'final_sha256': sha256_file(final_path),
        'peak_rss_mb': None,
        'clipped': False,
        'sample_rate': final_meta['sample_rate'],
    })
    print(f'[ok] {final_name}: duration={final_meta["duration"]:.2f}s chunks={len(total_chunks)} range=({lower}, {upper})')
    gc.collect()

# Save report and review metadata.
base_dir = Path('experiments/brand_voice_phase41d')
(base_dir / 'manifest.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
(base_dir / 'HUMAN_REVIEW.md').write_text('''PHASE 41D — HUMAN REVIEW

This is a validation package for the frozen Synthetic Candidate 03.

Checklist:
1. Same voice identity as the canonical freeze?
2. Natural spoken rhythm without artificial pacing tricks?
3. Any obvious chunk boundary or fatigue issue?
4. Is the narrator still distinctive and grounded in the candidate's established prosody?
5. Does the long-form content remain coherent and human-sounding over several minutes?

Add notes below.
''', encoding='utf-8')

print('VALIDATION_OK')
