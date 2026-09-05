# Phase 41D Final Report

## 1) Phase 41D final technical result

Phase 41D is a static, hash-safe validation package for frozen Synthetic Candidate 03. The final persisted evidence shows that all three long-form validation tests met their duration gates, and the canonical voice assets remained unchanged.

Status summary:
- Candidate 03 status: candidate
- Candidate 03 is_final_brand_voice: false
- Candidate B: untouched and preserved
- TTS inference was not rerun during this read-only audit
- Final runtime evidence is taken from the verified manifest and checkpoint artifacts on disk

## 2) Canonical Candidate 03 hashes

Canonical voice identity is frozen to the Phase 41B baseline under:
- /home/tung/ai voice/experiments/brand_voice_phase41b/baseline/PODCAST_SYNTHETIC_CANDIDATE_03

Verified canonical hashes:
- canonical_speaker_emb_sha256: 980d5856f58a8619b6abf0c3935de74ddfb5c333b9b8fae2fd5c3b6ef7067771
- canonical_speaker_emb_npy_sha256: c763159d8ed6ed4b0f1916f8b0762d1902743d293fcd7874541966d7f9ee10a1
- reference_codes_sha256: fe8f8e3e1766a7954595fa3a355e46aca8c3e27be4aba4bb1db8d9b60a960aa5
- inference_config_sha256: 5517fe2334e73d740d3ad8ffc3243b525286689538621518b78469cd87d29320

These values are the authoritative canonical values for the frozen runtime identity and deterministic config.

## 3) Exact inference config

The frozen deterministic config used for the validated runtime is:

```json
{
  "temperature": 0.8,
  "top_k": 25,
  "top_p": 0.95,
  "repetition_penalty": 1.2,
  "repetition_window": 64,
  "denoise": true,
  "use_ref_codes": true,
  "silence_p": 0.15,
  "crossfade_p": 0.0,
  "apply_watermark": true,
  "sample_rate": 48000,
  "max_new_frames": 600,
  "max_chars": 800,
  "max_chars_chunk": 350
}
```

Config hash:
- 5517fe2334e73d740d3ad8ffc3243b525286689538621518b78469cd87d29320

## 4) Final texts and text hashes

### Test 1 — 01_short_monologue_final.wav
- Text SHA256: 9390506182bdcfcc3433ae6c96e09228e1454abc3e583939063d6fe5cb7a4fda
- Character count: 1103
- Word count: 244
- Chunk count: 4
- Estimated duration: 58.56s
- Gate: (50.0, 65.0)

```text
Từ rất sớm, ta đã thấy rằng sống đúng nghĩa không phải là làm nhiều nhất, mà là biết mình đang đi về đâu. Mỗi ngày đều có những lựa chọn nhỏ: nói chuyện với sự bình tĩnh hay vội vàng, giữ im lặng hay bám theo tiếng ồn, tin vào sự thật hay chạy theo cảm giác. Những quyết định ấy không lớn, nhưng chúng tạo hình cho con người ta. Một người có chiều sâu không cần phải gào thét để được nghe. Họ chỉ cần một giọng nói rõ, một nhịp thở chậm, và một sự ổn định mà người khác cảm thấy an tâm. Đó là điều đáng quý trong một thế giới luôn thúc giục ta phản ứng nhanh hơn, nói nhiều hơn, và so sánh mình với người khác. Khi ta học được cách dừng lại, ta không phải từ bỏ năng lượng mà là rèn luyện sự kiểm soát. Ta biết khi nào nên giữ bình tĩnh, khi nào nên lắng nghe, và khi nào nên nói lên điều thật. Chính từ những khoảnh khắc không ai nhìn thấy ấy, một cuộc sống bắt đầu có trọng lượng. Họ không cần khoe khoang; họ chỉ cần đứng vững. Và đó là một dạng trí tuệ rất thầm lặng: biết dừng lại trước những cơn bực bội, biết chọn lời nói đúng lúc, và biết đặt mình vào nhịp của đời sống thay vì lao theo mọi thứ.
```

### Test 2 — 02_explanatory_section_final.wav
- Text SHA256: 1332c34e15c0e2a1beb6e5f2dbef0bc76a630ca6d1cd1a5cacee2cca5dc8652b
- Character count: 2163
- Word count: 484
- Chunk count: 8
- Estimated duration: 114.84s
- Gate: (100.0, 130.0)

```text
Để giải thích một nguyên tắc sống, điều quan trọng nhất là phải hỏi đúng câu hỏi: điều này có ý nghĩa gì trong thực tế? Nếu người nghe không thấy được giá trị của nó, cả bài nói sẽ trở nên thiếu sức sống và rơi vào lý thuyết. Một cách truyền đạt hiệu quả thường có bốn bước: mở đầu ngắn gọn, nêu giá trị cốt lõi, cho ví dụ thực tế, rồi kết thúc bằng một lời nhắc để áp dụng ngay. Điều ấy chỉ thực sự hiệu quả khi người nói giữ nhịp, chọn trọng tâm, và không biến ý tưởng thành những câu dài rời rạc. Khi ta nói về lòng trắc ẩn, ta không nên dừng ở định nghĩa. Ta cần cho người nghe cảm thấy điều đó trong đời sống: một người chậm lại để nghe người khác, một sự kiên nhẫn nhỏ trong lúc mọi thứ đang vội, một cái gật đầu thay cho sự chỉ trích. Người ta thường nhớ cảm giác được hiểu hơn là những câu văn hoa. Họ nhớ sự tĩnh lặng trong giọng nói, họ nhớ sự thật được đặt đúng nhịp thở, và họ nhớ rằng thông điệp đó không ép buộc họ, mà dẫn họ đi cùng nhau. Vì vậy, một giọng nói tốt không phải là giọng nói nhiều câu phức tạp, mà là giọng nói biết chốt ý, biết nhấn đúng điểm, và biết để người nghe có chỗ để suy nghĩ. Khi ta nói rõ, ta cho người ta không gian để tiếp nhận. Khi ta nói chậm nhưng có trọng tâm, ta giúp họ thấy rằng sự yên bình trong đầu óc vẫn là một nguồn lực. Một câu thật sự sâu sắc không cần ai giật mình mới nghe thấy. Nó đến rất tự nhiên, như một suy nghĩ đã được sống qua nhiều lần trước khi được nói ra. Trong podcast, điều ấy rất quan trọng vì người ta không chỉ nghe lời nói, họ còn nghe nhịp tư duy. Nếu ta muốn người nghe ở lại lâu hơn, ta phải cho họ cảm giác mình đi cùng hướng, không lạc trong vòng lặp của những câu dài vô ích. Một người trò chuyện giỏi biết khi nào nên dừng, khi nào nên nhấn mạnh, và khi nào nên để khoảng trống cho người nghe tự mình hồi tỉnh. Đó là cách sinh ra sự thấu hiểu mà không cần áp đặt. Một người có thể giải thích rõ nhưng không làm cho người nghe cảm thấy được hiểu. Sự sâu sắc không nằm ở độ dài của cách nói; nó nằm ở khả năng khiến người nghe cảm thấy mình không bị bỏ lại phía sau. Điều ấy đặc biệt quan trọng khi ta đang nói về sự thay đổi, về cảm giác mất phương hướng, và về việc học cách đứng.
```

### Test 3 — 03_longform_stress_test_final.wav
- Text SHA256: 852cc7a86095ef42ed3931de8d941b3d5f6debdc101242913f8c1ca38f56aee1
- Character count: 4356
- Word count: 961
- Chunk count: 16
- Estimated duration: 231.27s
- Gate: (210.0, 270.0)

```text
Hôm nay tôi muốn kể một câu chuyện dài hơn, không phải để làm ồn lên, mà để cho ta thấy tầm quan trọng của những quyết định nhỏ trong cuộc đời. Có một người sống trong một ngõ nhỏ, mỗi sáng dậy sớm, anh ta dành vài phút để sắp xếp lại hàng hóa trong cửa hàng, nhắc nhở con mình về sự kỷ luật, và lặng lẽ chào hỏi những người hàng xóm già đi qua. Những việc ấy không lớn lao, nhưng chúng khiến cuộc sống quanh anh ta trôi chậm đi đúng nhịp. Chúng khiến những ngày tẻ nhạt không trở nên vô nghĩa. Chúng cho thấy rằng sự bền vững của một con người không được xây dựng trong những khoảnh khắc ngắn ngủi của vinh quang, mà trong những thói quen không ai nhìn thấy. Một ngày nào đó, khi người ta bị thất bại, chán nản, và thấy mình không còn đường đi, họ bắt đầu nhận ra rằng chính những quyết định nhỏ ấy đã trở thành nền tảng. Họ đã học cách giữ lời hứa với bản thân. Họ biết khi nào nên chậm lại. Họ biết khi nào cần bình tĩnh trước sự mệt mỏi, và khi nào không nên bị cuốn theo sự giận dữ của thế giới. Đó là điều rất quan trọng: một con người không trở nên lớn lao nhờ những khoảnh khắc nổi bật, mà nhờ những cách ứng xử mà họ lặp đi lặp lại khi không ai quan sát. Câu chuyện này có thể áp dụng cho mọi khía cạnh của sự trưởng thành. Ta không cần một lời tuyên ngôn hùng hồn để trở thành người đáng tin cậy. Đôi khi điều quan trọng nhất là biết giữ lời hứa, biết cẩn trọng trong cách nói, và biết lắng nghe người khác khi mình đang muốn phản bác. Sự trưởng thành không phải là luôn đúng, mà là biết nhận ra mình có thể sai và vẫn chọn bước tiếp. Đó là lý do vì sao một giọng nói sâu có thể mang lại cảm giác an tâm cho người nghe: nó có trọng lượng, nhưng không ép buộc. Nó khiến người ta cảm thấy có thể dừng lại, suy ngẫm, và đi cùng với những ý nghĩ của mình cho đến khi chúng thực sự thấm sâu. Suy cho cùng, ngay cả những cuộc đối thoại dài nhất cũng không thành công nếu nó không cho người nghe thời gian để thở. Một cuộc trò chuyện tốt không phải là cuộc trò chuyện luôn nói nhiều và nói nhanh; nó là cuộc trò chuyện cho phép người nghe có chỗ để suy ngẫm, có chỗ để tiếp nhận, và có chỗ để quyết định liệu mình muốn đi cùng người nói thêm một đoạn nữa hay không. Chính vì vậy, tính bền vững của một giọng văn không nằm ở vẻ ngoài của nó, mà ở khả năng đi cùng người nghe trong những câu chuyện chưa được giải đáp ngay từ đầu, những câu hỏi chưa được trả lời ngay lập tức, và những khoảng lặng khiến con người quay lại với chính mình. Khi ta nghe một giọng nói chậm và rõ, ta cảm thấy như mình được đặt vào một không gian an toàn hơn. Không ai bị ép phải vội vàng. Không ai bị lừa bởi những lời phô trương. Họ chỉ được dẫn dắt bằng sự thật, nhịp điệu, và sự tôn trọng đối với thời gian của người nghe. Đó là kiểu nói chuyện mà qua rất nhiều năm, người ta vẫn nhớ. Nó không cần lớn tiếng, không cần lặp đi lặp lại, không cần giật mình trước mọi thứ. Nó chỉ cần biết cách đứng im trong một khoảnh khắc để người nghe có thể nghe thấu sự chân thành của mình. Mỗi người trong chúng ta đều có một chiều sâu, nhưng không phải ai cũng biết cách để nó hiện lên. Có những người luôn xô bồ và lao vào cuộc sống, nhưng rồi một ngày họ nhận ra rằng họ đã quen với sự ồn ào đến mức không còn nghe rõ tiếng lòng mình. Đó là lúc họ cần một giọng nói chậm, một câu hỏi rõ ràng, và một chút yên lòng để họ quay đầu lại và bắt đầu từ nơi đúng đắn. Câu chuyện này không phải để khuyên người ta làm tốt hơn, mà để nhắc nhở rằng sự trưởng thành thật sự không đến từ sự lộng lẫy ngắn ngủi, mà từ sự can đảm để tiếp tục đi, hoặc dừng lại khi cần thiết. Một người biết mình cần giữ bình tĩnh thường không khoe khoang. Họ bình thản, giữ lời hứa, và tạo ra sự an tâm rất cụ thể cho những người sống bên cạnh họ. Đó là một dạng trí tuệ rất tĩnh lặng, nhưng nó có tác động rất mạnh đến cách chúng ta đối diện với thời gian, với nỗi lo, và với những thay đổi không thể kiểm soát. Khi ai đó có thể giữ được nhịp điệu ấy trong từng câu chữ, người ta cũng đang giữ được một mảnh sự rõ ràng trong chính mình. Một người không cần phải hùng hồn mỗi ngày mới chứng minh mình đang sống. Sự ổn định lớn nhất không đến từ những lời nói lớn, mà từ cách ta vẫn giữ được sự thật và sự điềm tĩnh ngay cả khi mọi thứ xung quanh đang biến động. Đó là cách một đời người có thể trở nên trong sáng: không giành giật, không vội vàng, và không đánh mất chính mình giữa những đường thẳng của cuộc sống.
```

## 5) Chunk counts and final durations

Final validated durations from the manifest:
- Test 1: 56.16s, chunk count 4
- Test 2: 115.36s, chunk count 8
- Test 3: 225.60s, chunk count 16

Gate PASS for all three:
- 01_short_monologue_final.wav: 56.16s in (50.0, 65.0)
- 02_explanatory_section_final.wav: 115.36s in (100.0, 130.0)
- 03_longform_stress_test_final.wav: 225.60s in (210.0, 270.0)

## 6) Final WAV SHA256 values

Manifest SHA256 values:
- 01_short_monologue_final.wav: 03a659f11b183a1af96d1ec7835ad1804202161a5fe6cddba806257ea813905c
- 02_explanatory_section_final.wav: 30d64de666b69e0834d99143a162163ff258e94cdc417b93fbe5276cab3d5463
- 03_longform_stress_test_final.wav: 3b8aef4b1678ce29bdab42f1d880653bf8820feb7747dd8c0d7bc5e725f49aaa

## 7) Low-memory streaming architecture

The project stays on the chunked low-memory validation pipeline:
- text is split into bounded chunk segments using max_chars_chunk = 350
- each chunk is synthesized independently through the Vieneu runtime
- each chunk is saved as a WAV, with a per-chunk metadata record including SHA256, duration, and boundary signal diagnostics
- final long-form audio is assembled by concatenating the validated chunk streams
- checkpoint state records completed chunk IDs and reuse constraints

This architecture keeps memory usage bounded and allows deterministic validation, resume safety, and recovery without mutating the underlying canonical candidate voice.

## 8) Checkpoint and resume implementation

The checkpoint was implemented in run_longform_validation.py and persisted in resume_state.json.

Key policy points:
- canonical embedding hash, canonical npy hash, reference codes hash, and inference config hash are stored in the checkpoint
- chunk reuse is accepted only if the chunk text hash and all canonical hashes match exactly
- legacy index-only resume entries are archived and rejected
- set values are converted to deterministic sorted lists before JSON serialization
- on load, those lists are rehydrated back to Python sets for runtime logic

Current checkpoint summary:
- version: 2
- canonical_speaker_emb_sha256: 980d5856f58a8619b6abf0c3935de74ddfb5c333b9b8fae2fd5c3b6ef7067771
- canonical_speaker_emb_npy_sha256: c763159d8ed6ed4b0f1916f8b0762d1902743d293fcd7874541966d7f9ee10a1
- reference_codes_sha256: fe8f8e3e1766a7954595fa3a355e46aca8c3e27be4aba4bb1db8d9b60a960aa5
- inference_config_sha256: 5517fe2334e73d740d3ad8ffc3243b525286689538621518b78469cd87d29320
- completed_tests: []
- chunks: {}
- done_chunks: {"01_short_monologue":["0","1","2","3"], ...}

## 9) Memory / RSS evidence

No numeric memory capture is available in the final manifest. The manifest fields for peak RSS are explicitly null:
- peak_rss_mb: null

This means there is no persisted RSS evidence from the final validated run. The project therefore contains no verified numeric memory snapshot beyond the low-memory design and chunked generation pattern itself.

## 10) Continuity and boundary evidence

Boundary continuity evidence is available from the per-chunk metadata in the manifest. The relevant values are low-magnitude absolute means at chunk boundaries, which suggests that the chunk boundaries remained smooth enough for the observed validation outputs:
- boundary_start_mean_abs values clustered around 1e-6 to 1e-4
- boundary_end_mean_abs values clustered around 5e-7 to 8.5e-5

This is consistent with the low-memory chunk pipeline preserving continuity without artificial discontinuity artifacts in the final assembled audio manifests.

## 11) Candidate B preservation

Candidate B was intentionally not modified and remains preserved as a separate artifact outside the canonical frozen Candidate 03 path. This report does not promote Candidate B, and there is no mutation or replacement of its stored files.

## 12) Candidate 03 status

Candidate 03 remains:
- status = candidate
- is_final_brand_voice = false

This preserves the project requirement that Candidate 03 is a frozen validation candidate, not the final brand voice decision.

## 13) Changed files and git status

The git working tree shows a mix of tracked modifications and newly generated untracked experiment directories, but no direct mutation of the canonical Candidate 03 voice root or Candidate B assets. Notable tracked changes at the time of the audit included:
- modified: backend/app/tts/model.py
- modified: backend/app/tts/special_voices.py
- modified: backend/app/tts/voice_store.py
- modified: backend/main.py
- deleted historical diagnostics reports
- numerous untracked experiment directories and reports under experiments/ and diagnostics/

The Phase 41D validation package itself was created as read-only evidence around the frozen candidate and manifest artifacts, and no additional TTS generation was initiated during this final audit pass.

## 14) Anomalies and recovery history

### Anomaly A: stale canonical hashes in earlier reports
The earlier report values did not match the frozen Phase 41B files. They were stale values and were superseded by verified canonical values from the actual frozen files.

### Anomaly B: `TypeError: Object of type set is not JSON serializable`
A runtime checkpoint save path attempted to serialize Python set objects directly into resume_state.json. This was corrected by:
- converting `done_chunks` values to deterministic sorted lists before JSON writing
- rehydrating those lists back into sets on load

Result: deterministic JSON-safe checkpoint state without losing runtime semantics.

### Anomaly C: obsolete Test 2 duration overshoot
The pre-run static external validation showed Test 2 exceeding the gate. The text was shortened to bring it within the desired range, and the final manifest reflects the corrected static text set and final pass.

### Recovery history
- stale resume state archived to superseded files
- clean checkpoint written to resume_state.json
- recovery/original audio and superseded final audio were preserved for evidence
- no mutation of canonical Candidate 03 assets occurred

## 15) Test 1 discrepancy analysis

Previous run: 56.72s
Final run: 56.16s

This discrepancy is explained by the preserved artifact evidence rather than by a fresh TTS rerun during this audit:
- the archived superseded final WAV for Test 1 has SHA256 925627a3340b818dc1475410792a38e4a6e6bddc79897e60296d914e23f689e4 and duration 56.72s
- the current final manifest uses the validated final WAV with SHA256 03a659f11b183a1af96d1ec7835ad1804202161a5fe6cddba806257ea813905c and duration 56.16s
- the current manifest chunk entries for Test 1 are exactly the preserved chunk records:
  - chunk 0 = f036d87fa8f18fcda292352ec767fb379973cc9da41a92e561e0ef8026f78c07 (16.96s)
  - chunk 1 = 6c95cb6e86b8f00bdc28bd2802de881a238cc5adaf33930a3422f13d5734cd5f (14.32s)
  - chunk 2 = 431fa7b96d2359b3b2f7663b8ef46fdcc300cd4666f4e13896f3d7a4401b55a1 (15.76s)
  - chunk 3 = c290aaf63e57899ee9d9054188b74c358b161ab4511293d29deeec06e6ba2ddd (9.12s)
- the checkpoint state explicitly records those chunk IDs as completed for Test 1, and the code path validates reuse only when the current text hash and canonical hashes match

Conclusion: Test 1 was not freshly regenerated during this audit. The evidence supports a reused and reassembled final audio from the preserved chunk evidence and the finalized manifest/checkpoint state. The 56.72s archived file is an earlier superseded artifact; the authoritative current final file is the 56.16s manifest result.

## 16) Final verification statement

The final manifest and checkpoint evidence were read directly from disk and are consistent with the canonical frozen assets and the validated low-memory chunk pipeline. No new TTS generation was run during the final read-only audit.

SYNTHETIC CANDIDATE 03 LONG-FORM VALIDATION:
PENDING HUMAN QA
