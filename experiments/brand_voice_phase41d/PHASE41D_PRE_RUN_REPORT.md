# Phase 41D Pre-Run Report

## Current Phase 41D status
- Phase 41D status: static preflight only; NO TTS inference was run.
- Canonical Synthetic Candidate 03 embedding and reference codes remain unchanged.
- Candidate B remains untouched.
- Inference config remains unchanged.
- Low-memory streaming architecture remains in place with hash-safe resume validation.
- No audio, no generated WAVs, and no candidate mutation were performed.

## Frozen canonical assets
- Candidate 03 canonical voice root: /home/tung/ai voice/experiments/brand_voice_phase41b/baseline/PODCAST_SYNTHETIC_CANDIDATE_03
- Canonical embed file: /home/tung/ai voice/experiments/brand_voice_phase41b/baseline/PODCAST_SYNTHETIC_CANDIDATE_03/speaker_emb.npy
- Canonical reference file: /home/tung/ai voice/experiments/brand_voice_phase41b/baseline/PODCAST_SYNTHETIC_CANDIDATE_03/reference_codes.npy
- Canonical voice identity is intentionally frozen and not modified.

## Canonical integrity verification
A. raw speaker_emb.npy file SHA256 = c763159d8ed6ed4b0f1916f8b0762d1902743d293fcd7874541966d7f9ee10a1
B. loaded speaker_emb array SHA256 = 980d5856f58a8619b6abf0c3935de74ddfb5c333b9b8fae2fd5c3b6ef7067771
C. raw reference_codes.npy file SHA256 = fe8f8e3e1766a7954595fa3a355e46aca8c3e27be4aba4bb1db8d9b60a960aa5

The earlier report values 28d42..., 25d3..., and 3e6d... do not match the frozen Phase 41B files. They were stale, not canonical. The actual immutable files above are the verified canonical values.

## Duration gate targets
- Test 1: 50–65s, target ~55–60s
- Test 2: 100–130s, target ~110–120s
- Test 3: 210–270s, target ~230–250s

## Static text set

### 01_short_monologue_final.wav
Text SHA256: 9390506182bdcfcc3433ae6c96e09228e1454abc3e583939063d6fe5cb7a4fda
Character count: 1103
Word count: 244
Chunk count: 4
Estimated duration: 58.56s
Gate: (50.0, 65.0)

```text
Từ rất sớm, ta đã thấy rằng sống đúng nghĩa không phải là làm nhiều nhất, mà là biết mình đang đi về đâu. Mỗi ngày đều có những lựa chọn nhỏ: nói chuyện với sự bình tĩnh hay vội vàng, giữ im lặng hay bám theo tiếng ồn, tin vào sự thật hay chạy theo cảm giác. Những quyết định ấy không lớn, nhưng chúng tạo hình cho con người ta. Một người có chiều sâu không cần phải gào thét để được nghe. Họ chỉ cần một giọng nói rõ, một nhịp thở chậm, và một sự ổn định mà người khác cảm thấy an tâm. Đó là điều đáng quý trong một thế giới luôn thúc giục ta phản ứng nhanh hơn, nói nhiều hơn, và so sánh mình với người khác. Khi ta học được cách dừng lại, ta không phải từ bỏ năng lượng mà là rèn luyện sự kiểm soát. Ta biết khi nào nên giữ bình tĩnh, khi nào nên lắng nghe, và khi nào nên nói lên điều thật. Chính từ những khoảnh khắc không ai nhìn thấy ấy, một cuộc sống bắt đầu có trọng lượng. Họ không cần khoe khoang; họ chỉ cần đứng vững. Và đó là một dạng trí tuệ rất thầm lặng: biết dừng lại trước những cơn bực bội, biết chọn lời nói đúng lúc, và biết đặt mình vào nhịp của đời sống thay vì lao theo mọi thứ.
```

### 02_explanatory_section_final.wav
Text SHA256: 1332c34e15c0e2a1beb6e5f2dbef0bc76a630ca6d1cd1a5cacee2cca5dc8652b
Character count: 2163
Word count: 484
Chunk count: 8
Estimated duration: 114.84s
Gate: (100.0, 130.0)

```text
Để giải thích một nguyên tắc sống, điều quan trọng nhất là phải hỏi đúng câu hỏi: điều này có ý nghĩa gì trong thực tế? Nếu người nghe không thấy được giá trị của nó, cả bài nói sẽ trở nên thiếu sức sống và rơi vào lý thuyết. Một cách truyền đạt hiệu quả thường có bốn bước: mở đầu ngắn gọn, nêu giá trị cốt lõi, cho ví dụ thực tế, rồi kết thúc bằng một lời nhắc để áp dụng ngay. Điều ấy chỉ thực sự hiệu quả khi người nói giữ nhịp, chọn trọng tâm, và không biến ý tưởng thành những câu dài rời rạc. Khi ta nói về lòng trắc ẩn, ta không nên dừng ở định nghĩa. Ta cần cho người nghe cảm thấy điều đó trong đời sống: một người chậm lại để nghe người khác, một sự kiên nhẫn nhỏ trong lúc mọi thứ đang vội, một cái gật đầu thay cho sự chỉ trích. Người ta thường nhớ cảm giác được hiểu hơn là những câu văn hoa. Họ nhớ sự tĩnh lặng trong giọng nói, họ nhớ sự thật được đặt đúng nhịp thở, và họ nhớ rằng thông điệp đó không ép buộc họ, mà dẫn họ đi cùng nhau. Vì vậy, một giọng nói tốt không phải là giọng nói nhiều câu phức tạp, mà là giọng nói biết chốt ý, biết nhấn đúng điểm, và biết để người nghe có chỗ để suy nghĩ. Khi ta nói rõ, ta cho người ta không gian để tiếp nhận. Khi ta nói chậm nhưng có trọng tâm, ta giúp họ thấy rằng sự yên bình trong đầu óc vẫn là một nguồn lực. Một câu thật sự sâu sắc không cần ai giật mình mới nghe thấy. Nó đến rất tự nhiên, như một suy nghĩ đã được sống qua nhiều lần trước khi được nói ra. Trong podcast, điều ấy rất quan trọng vì người ta không chỉ nghe lời nói, họ còn nghe nhịp tư duy. Nếu ta muốn người nghe ở lại lâu hơn, ta phải cho họ cảm giác mình đi cùng hướng, không lạc trong vòng lặp của những câu dài vô ích. Một người trò chuyện giỏi biết khi nào nên dừng, khi nào nên nhấn mạnh, và khi nào nên để khoảng trống cho người nghe tự mình hồi tỉnh. Đó là cách sinh ra sự thấu hiểu mà không cần áp đặt. Một người có thể giải thích rõ nhưng không làm cho người nghe cảm thấy được hiểu. Sự sâu sắc không nằm ở độ dài của cách nói; nó nằm ở khả năng khiến người nghe cảm thấy mình không bị bỏ lại phía sau. Điều ấy đặc biệt quan trọng khi ta đang nói về sự thay đổi, về cảm giác mất phương hướng, và về việc học cách đứng.
```

### 03_longform_stress_test_final.wav
Text SHA256: 852cc7a86095ef42ed3931de8d941b3d5f6debdc101242913f8c1ca38f56aee1
Character count: 4356
Word count: 961
Chunk count: 16
Estimated duration: 231.27s
Gate: (210.0, 270.0)

```text
Hôm nay tôi muốn kể một câu chuyện dài hơn, không phải để làm ồn lên, mà để cho ta thấy tầm quan trọng của những quyết định nhỏ trong cuộc đời. Có một người sống trong một ngõ nhỏ, mỗi sáng dậy sớm, anh ta dành vài phút để sắp xếp lại hàng hóa trong cửa hàng, nhắc nhở con mình về sự kỷ luật, và lặng lẽ chào hỏi những người hàng xóm già đi qua. Những việc ấy không lớn lao, nhưng chúng khiến cuộc sống quanh anh ta trôi chậm đi đúng nhịp. Chúng khiến những ngày tẻ nhạt không trở nên vô nghĩa. Chúng cho thấy rằng sự bền vững của một con người không được xây dựng trong những khoảnh khắc ngắn ngủi của vinh quang, mà trong những thói quen không ai nhìn thấy. Một ngày nào đó, khi người ta bị thất bại, chán nản, và thấy mình không còn đường đi, họ bắt đầu nhận ra rằng chính những quyết định nhỏ ấy đã trở thành nền tảng. Họ đã học cách giữ lời hứa với bản thân. Họ biết khi nào nên chậm lại. Họ biết khi nào cần bình tĩnh trước sự mệt mỏi, và khi nào không nên bị cuốn theo sự giận dữ của thế giới. Đó là điều rất quan trọng: một con người không trở nên lớn lao nhờ những khoảnh khắc nổi bật, mà nhờ những cách ứng xử mà họ lặp đi lặp lại khi không ai quan sát. Câu chuyện này có thể áp dụng cho mọi khía cạnh của sự trưởng thành. Ta không cần một lời tuyên ngôn hùng hồn để trở thành người đáng tin cậy. Đôi khi điều quan trọng nhất là biết giữ lời hứa, biết cẩn trọng trong cách nói, và biết lắng nghe người khác khi mình đang muốn phản bác. Sự trưởng thành không phải là luôn đúng, mà là biết nhận ra mình có thể sai và vẫn chọn bước tiếp. Đó là lý do vì sao một giọng nói sâu có thể mang lại cảm giác an tâm cho người nghe: nó có trọng lượng, nhưng không ép buộc. Nó khiến người ta cảm thấy có thể dừng lại, suy ngẫm, và đi cùng với những ý nghĩ của mình cho đến khi chúng thực sự thấm sâu. Suy cho cùng, ngay cả những cuộc đối thoại dài nhất cũng không thành công nếu nó không cho người nghe thời gian để thở. Một cuộc trò chuyện tốt không phải là cuộc trò chuyện luôn nói nhiều và nói nhanh; nó là cuộc trò chuyện cho phép người nghe có chỗ để suy ngẫm, có chỗ để tiếp nhận, và có chỗ để quyết định liệu mình muốn đi cùng người nói thêm một đoạn nữa hay không. Chính vì vậy, tính bền vững của một giọng văn không nằm ở vẻ ngoài của nó, mà ở khả năng đi cùng người nghe trong những câu chuyện chưa được giải đáp ngay từ đầu, những câu hỏi chưa được trả lời ngay lập tức, và những khoảng lặng khiến con người quay lại với chính mình. Khi ta nghe một giọng nói chậm và rõ, ta cảm thấy như mình được đặt vào một không gian an toàn hơn. Không ai bị ép phải vội vàng. Không ai bị lừa bởi những lời phô trương. Họ chỉ được dẫn dắt bằng sự thật, nhịp điệu, và sự tôn trọng đối với thời gian của người nghe. Đó là kiểu nói chuyện mà qua rất nhiều năm, người ta vẫn nhớ. Nó không cần lớn tiếng, không cần lặp đi lặp lại, không cần giật mình trước mọi thứ. Nó chỉ cần biết cách đứng im trong một khoảnh khắc để người nghe có thể nghe thấu sự chân thành của mình. Mỗi người trong chúng ta đều có một chiều sâu, nhưng không phải ai cũng biết cách để nó hiện lên. Có những người luôn xô bồ và lao vào cuộc sống, nhưng rồi một ngày họ nhận ra rằng họ đã quen với sự ồn ào đến mức không còn nghe rõ tiếng lòng mình. Đó là lúc họ cần một giọng nói chậm, một câu hỏi rõ ràng, và một chút yên lòng để họ quay đầu lại và bắt đầu từ nơi đúng đắn. Câu chuyện này không phải để khuyên người ta làm tốt hơn, mà để nhắc nhở rằng sự trưởng thành thật sự không đến từ sự lộng lẫy ngắn ngủi, mà từ sự can đảm để tiếp tục đi, hoặc dừng lại khi cần thiết. Một người biết mình cần giữ bình tĩnh thường không khoe khoang. Họ bình thản, giữ lời hứa, và tạo ra sự an tâm rất cụ thể cho những người sống bên cạnh họ. Đó là một dạng trí tuệ rất tĩnh lặng, nhưng nó có tác động rất mạnh đến cách chúng ta đối diện với thời gian, với nỗi lo, và với những thay đổi không thể kiểm soát. Khi ai đó có thể giữ được nhịp điệu ấy trong từng câu chữ, người ta cũng đang giữ được một mảnh sự rõ ràng trong chính mình. Một người không cần phải hùng hồn mỗi ngày mới chứng minh mình đang sống. Sự ổn định lớn nhất không đến từ những lời nói lớn, mà từ cách ta vẫn giữ được sự thật và sự điềm tĩnh ngay cả khi mọi thứ xung quanh đang biến động. Đó là cách một đời người có thể trở nên trong sáng: không giành giật, không vội vàng, và không đánh mất chính mình giữa những đường thẳng của cuộc sống.
```

## Duration gate check (external run results)
- 01_short_monologue_final.wav: 56.72s PASS (required 50.0–65.0)
- 02_explanatory_section_final.wav: 135.84s FAIL (required 100.0–130.0)
- Execution stopped before Test 3; no Test 3 audio was generated.

## Canonical hashes (verified)
- canonical_speaker_emb_sha256: 980d5856f58a8619b6abf0c3935de74ddfb5c333b9b8fae2fd5c3b6ef7067771
- canonical_speaker_emb_npy_sha256: c763159d8ed6ed4b0f1916f8b0762d1902743d293fcd7874541966d7f9ee10a1
- reference_codes_sha256: fe8f8e3e1766a7954595fa3a355e46aca8c3e27be4aba4bb1db8d9b60a960aa5

## Inference config verification
The previous config hash 1968f0a6c59d9d4d98d6c3f0f4d8d30644643c6e4c44f7d4319692d9f8423d3d is stale and not the current canonical config hash. The actual deterministic config hash for the frozen Phase 41B config is 5517fe2334e73d740d3ad8ffc3243b525286689538621518b78469cd87d29320.

Values included in the hash (sorted JSON):
- temperature: 0.8
- top_k: 25
- top_p: 0.95
- repetition_penalty: 1.2
- repetition_window: 64
- denoise: true
- use_ref_codes: true
- silence_p: 0.15
- crossfade_p: 0.0
- apply_watermark: true
- sample_rate: 48000
- max_new_frames: 600
- max_chars: 800
- max_chars_chunk: 350

Voice/prosody settings are preserved exactly:
- temperature 0.8
- top_k 25
- top_p 0.95
- repetition_penalty 1.2
- repetition_window 64
- denoise True
- use_ref_codes True
- silence_p 0.15
- crossfade_p 0.0
- apply_watermark True
- sample_rate 48000

Capacity/chunking settings differ only in documentation and were not changed for the canonical frozen runtime.

## Checkpoint / hash-safe resume policy
- Text changes invalidate stale chunk hashes because chunk reuse requires current chunk text hash, current inference config hash, and current canonical hashes to match exactly.
- Legacy or index-only resume entries are archived and rejected unless they match the current canonical and config hashes.
- No chunk reuse is allowed across text revisions.

### Checkpoint serialization fix

- External failure: a previous run attempted to persist Python `set()` objects into `resume_state.json`, causing `TypeError: Object of type set is not JSON serializable` when saving runtime state.
- Fix implemented: `run_longform_validation.py` now converts any `set` values stored under `done_chunks` into deterministic sorted lists before JSON serialization, and `load_resume_state()` rehydrates those lists back into Python `set` objects at load time. This avoids TypeError while keeping on-disk state deterministic.
- Archived the preexisting resume state to: experiments/brand_voice_phase41d/superseded/resume_state_serialization_test_20260903_161343.json
- New clean checkpoint written to: experiments/brand_voice_phase41d/resume_state.json

New clean checkpoint summary:

- `version`: 2
- `canonical_speaker_emb_sha256`: 980d5856f58a8619b6abf0c3935de74ddfb5c333b9b8fae2fd5c3b6ef7067771
- `canonical_speaker_emb_npy_sha256`: c763159d8ed6ed4b0f1916f8b0762d1902743d293fcd7874541966d7f9ee10a1
- `reference_codes_sha256`: fe8f8e3e1766a7954595fa3a355e46aca8c3e27be4aba4bb1db8d9b60a960aa5
- `inference_config_sha256`: 5517fe2334e73d740d3ad8ffc3243b525286689538621518b78469cd87d29320
- `completed_tests`: []
- `chunks`: {}
- `done_chunks`: {}

- Notes: No existing chunks were marked completed; existing chunk WAVs and recovery evidence were left untouched on disk. All future serialization/unit tests use temporary test JSON files and do not touch the real `resume_state.json`.

## Low-memory architecture
- The project remains on the chunked low-memory validation pipeline.
- Audio generation is streamed in chunks and finalized incrementally.
- No refinement, promotion, or mutation of Candidate 03 or Candidate B occurred.

## Exact external terminal command
```bash
cd "/home/tung/ai voice" && /home/tung/ai voice/.venv/bin/python experiments/brand_voice_phase41d/run_longform_validation.py
```

## Exact memory-monitor command
```bash
watch -n 2 'free -h; echo; ps -eo pid,comm,%mem,rss --sort=-rss | head -12'
```

## Verification status
- Python parse OK: static checks were performed without TTS inference.
- TTS inference executed: no.
- Final verdict: static preflight FAIL (external run): Test 2 exceeded the required duration gate. See "Duration gate check (external run results)" above for details.
