# Phase 42C — Validated vs production plan diff

This is a static, text-only comparison. No TTS inference or audio transformation was run.

## Verdict

- Validated Phase 41G chunks: **55**
- Production-planner chunks: **54**
- Exact same-index chunk-text matches: **0/54**
- Matching inter-chunk lexical boundary positions: **47**
- Validated-only boundary positions: **7**
- Production-only boundary positions: **6**

The zero exact-text-match count is not merely a numbering artifact: production retains terminal sentence punctuation, while the validated Phase 41G spoken chunk strings deliberately remove it. Six local regroupings also move, add, or remove boundaries.

## Every nonmatching lexical boundary

Positions are cumulative whitespace-token offsets in the reconstructed spoken text. A dash means that plan has no boundary at that position.

| Token position | VALIDATED | PRODUCTION |
|---:|---|---|
| 61 | V01 after: Điện thoại báo tin mới, công việc nhắc hạn, người khác kể về những bước tiến của họ, và mọi thứ tạo thàn… | — |
| 72 | — | P01 after: Điện thoại báo tin mới, công việc nhắc hạn, người khác kể về những bước tiến của họ, và mọi thứ tạo thàn… |
| 596 | V17 after: Không phải mọi sự chậm lại đều là trì hoãn, mà có những lúc chậm lại chính là hành động có trách nhiệm n… | — |
| 614 | — | P17 after: Không phải mọi sự chậm lại đều là trì hoãn, mà có những lúc chậm lại chính là hành động có trách nhiệm n… |
| 633 | V18 after: Một bác sĩ dừng vài giây trước khi đưa ra kết luận không phải vì thiếu năng lực Một người cha im lặng để… | — |
| 653 | — | P18 after: Một người cha im lặng để nghe hết câu chuyện của con không phải vì không biết nói gì. Một người lãnh đạo… |
| 861 | V25 after: Trong khoảng ấy, ta chỉ đọc, chỉ viết, chỉ lắng nghe, hoặc chỉ giải quyết một vấn đề cho đến khi nó đạt … | — |
| 879 | — | P25 after: Trong khoảng ấy, ta chỉ đọc, chỉ viết, chỉ lắng nghe, hoặc chỉ giải quyết một vấn đề cho đến khi nó đạt … |
| 1082 | — | P31 after: Sự ổn định không nằm ở việc bắt cuộc đời tuân theo lịch của mình. |
| 1687 | V48 after: Nếu hôm nay mọi thứ đều có vẻ gấp, hãy thử dừng lại và chọn một việc thật sự quan trọng Làm việc ấy bằng… | — |
| 1695 | — | P49 after: Nếu hôm nay mọi thứ đều có vẻ gấp, hãy thử dừng lại và chọn một việc thật sự quan trọng. Làm việc ấy bằn… |
| 1707 | V49 after: Sau đó mới bước sang việc tiếp theo Ta không cần chứng minh giá trị bằng cách luôn vội vàng | — |
| 1792 | V52 after: Sự trưởng thành hiếm khi là một đường thẳng; nó giống việc nhiều lần quay về với điều mình biết là đúng | — |

## Every same-index text mismatch

All 54 comparable indexes differ exactly. The table below records each mismatch; rows near regrouping points diverge by more than terminal punctuation.

| Index | VALIDATED snippet | PRODUCTION snippet |
|---:|---|---|
| 00 | Có những giai đoạn trong đời, ta thức dậy với một danh sách rất dài nhưng lại không biết việc nào thật s… | Có những giai đoạn trong đời, ta thức dậy với một danh sách rất dài nhưng lại không biết việc nào thật s… |
| 01 | Điện thoại báo tin mới, công việc nhắc hạn, người khác kể về những bước tiến của họ, và mọi thứ tạo thàn… | Điện thoại báo tin mới, công việc nhắc hạn, người khác kể về những bước tiến của họ, và mọi thứ tạo thàn… |
| 02 | Cảm giác ấy không hẳn là lười biếng hay yếu đuối Nó thường xuất hiện khi tâm trí phải tiếp nhận quá nhiề… | Nó thường xuất hiện khi tâm trí phải tiếp nhận quá nhiều tín hiệu nhưng chưa kịp phân biệt điều gì quan … |
| 03 | Vì thế, câu hỏi đầu tiên không phải là làm sao để chạy nhanh hơn, mà là làm sao để biết mình đang chạy v… | Vì thế, câu hỏi đầu tiên không phải là làm sao để chạy nhanh hơn, mà là làm sao để biết mình đang chạy v… |
| 04 | Nhiều người cố giải quyết sự quá tải bằng cách nhồi thêm kỷ luật vào một ngày vốn đã chật kín Họ dậy sớm… | Nhiều người cố giải quyết sự quá tải bằng cách nhồi thêm kỷ luật vào một ngày vốn đã chật kín. Họ dậy sớ… |
| 05 | Cách ấy đôi khi tạo ra kết quả ngắn hạn, nhưng nó cũng có thể khiến con người sống như đang liên tục chấ… | Cách ấy đôi khi tạo ra kết quả ngắn hạn, nhưng nó cũng có thể khiến con người sống như đang liên tục chấ… |
| 06 | Kỷ luật vốn là một công cụ để bảo vệ điều có ý nghĩa, không phải một chiếc roi để trừng phạt mọi giới hạ… | Kỷ luật vốn là một công cụ để bảo vệ điều có ý nghĩa, không phải một chiếc roi để trừng phạt mọi giới hạ… |
| 07 | Hãy hình dung một người làm việc tại cửa hàng nhỏ ở cuối phố Mỗi sáng, chị mở cửa, kiểm tra hàng hóa, tr… | Hãy hình dung một người làm việc tại cửa hàng nhỏ ở cuối phố. Mỗi sáng, chị mở cửa, kiểm tra hàng hóa, t… |
| 08 | Có hôm khách đông, một đơn giao chậm, con chị lại sốt, còn tin nhắn công việc vẫn đến liên tục Nếu nhìn … | Có hôm khách đông, một đơn giao chậm, con chị lại sốt, còn tin nhắn công việc vẫn đến liên tục. Nếu nhìn… |
| 09 | Nhưng điều làm chị mệt nhất không phải số lượng việc, mà là cảm giác mọi việc đều đang đòi được ưu tiên … | Nhưng điều làm chị mệt nhất không phải số lượng việc, mà là cảm giác mọi việc đều đang đòi được ưu tiên … |
| 10 | Trong hoàn cảnh đó, lời khuyên “hãy cố thêm một chút” nghe có vẻ tích cực nhưng chưa chắc hữu ích | Trong hoàn cảnh đó, lời khuyên “hãy cố thêm một chút” nghe có vẻ tích cực nhưng chưa chắc hữu ích. |
| 11 | Điều chị cần trước tiên là một khoảng đủ rõ để nhận ra đâu là việc phải xử lý ngay, đâu là việc có thể h… | Điều chị cần trước tiên là một khoảng đủ rõ để nhận ra đâu là việc phải xử lý ngay, đâu là việc có thể h… |
| 12 | Chị gọi cho người giao hàng, báo thật với khách, nhờ người thân đưa con đi khám, rồi tạm gác những tin n… | Chị gọi cho người giao hàng, báo thật với khách, nhờ người thân đưa con đi khám, rồi tạm gác những tin n… |
| 13 | Tuy nhiên, khi thứ tự trở nên rõ ràng, tâm trí không còn phải chống đỡ tất cả mọi thứ trong cùng một kho… | Tuy nhiên, khi thứ tự trở nên rõ ràng, tâm trí không còn phải chống đỡ tất cả mọi thứ trong cùng một kho… |
| 14 | Đây là điểm ta thường nhầm lẫn giữa bận rộn và có phương hướng Bận rộn cho ta cảm giác mình đang chuyển … | Đây là điểm ta thường nhầm lẫn giữa bận rộn và có phương hướng. Bận rộn cho ta cảm giác mình đang chuyển… |
| 15 | Một ngày kín lịch có thể rất hiệu quả, nhưng cũng có thể chỉ là một cách tinh vi để né tránh câu hỏi khó… | Một ngày kín lịch có thể rất hiệu quả, nhưng cũng có thể chỉ là một cách tinh vi để né tránh câu hỏi khó… |
| 16 | Ta liên tục kiểm tra thông báo vì không muốn ngồi yên với sự bất an của mình Ta nói rằng mình đang tiến … | Ta liên tục kiểm tra thông báo vì không muốn ngồi yên với sự bất an của mình. Ta nói rằng mình đang tiến… |
| 17 | Không phải mọi sự chậm lại đều là trì hoãn, mà có những lúc chậm lại chính là hành động có trách nhiệm n… | Không phải mọi sự chậm lại đều là trì hoãn, mà có những lúc chậm lại chính là hành động có trách nhiệm n… |
| 18 | Một bác sĩ dừng vài giây trước khi đưa ra kết luận không phải vì thiếu năng lực Một người cha im lặng để… | Một người cha im lặng để nghe hết câu chuyện của con không phải vì không biết nói gì. Một người lãnh đạo… |
| 19 | Một người lãnh đạo xin thêm thời gian trước quyết định quan trọng cũng không nhất thiết là do dự Khoảng … | Khoảng dừng đúng chỗ giúp ta nhìn thấy phần hậu quả mà sự vội vàng thường che khuất. |
| 20 | Tâm lý học đời thường cho thấy con người không chỉ mệt vì làm nhiều, mà còn mệt vì phải chuyển sự chú ý … | Tâm lý học đời thường cho thấy con người không chỉ mệt vì làm nhiều, mà còn mệt vì phải chuyển sự chú ý … |
| 21 | Mỗi lần đang viết một đoạn rồi quay sang trả lời tin nhắn, tâm trí không lập tức trở về trạng thái cũ | Mỗi lần đang viết một đoạn rồi quay sang trả lời tin nhắn, tâm trí không lập tức trở về trạng thái cũ. |
| 22 | Một phần chú ý vẫn mắc lại ở cuộc trao đổi vừa rồi, giống như căn phòng đã đóng cửa nhưng tiếng nói bên … | Một phần chú ý vẫn mắc lại ở cuộc trao đổi vừa rồi, giống như căn phòng đã đóng cửa nhưng tiếng nói bên … |
| 23 | Nếu điều đó lặp lại hàng chục lần, cuối ngày ta có thể thấy kiệt sức dù chẳng hoàn thành việc nào thật s… | Nếu điều đó lặp lại hàng chục lần, cuối ngày ta có thể thấy kiệt sức dù chẳng hoàn thành việc nào thật s… |
| 24 | Vì vậy, sự tập trung không đơn giản là ép mắt nhìn vào màn hình lâu hơn Nó bắt đầu từ quyết định bảo vệ … | Vì vậy, sự tập trung không đơn giản là ép mắt nhìn vào màn hình lâu hơn. Nó bắt đầu từ quyết định bảo vệ… |
| 25 | Trong khoảng ấy, ta chỉ đọc, chỉ viết, chỉ lắng nghe, hoặc chỉ giải quyết một vấn đề cho đến khi nó đạt … | Trong khoảng ấy, ta chỉ đọc, chỉ viết, chỉ lắng nghe, hoặc chỉ giải quyết một vấn đề cho đến khi nó đạt … |
| 26 | Điều này nghe có vẻ bình thường, nhưng chính sự bình thường đó làm nó khó thực hiện Ta đã quen xem phân … | Ta đã quen xem phân tán là trạng thái mặc định, đến mức vài phút yên tĩnh cũng khiến mình muốn tìm thứ g… |
| 27 | Một cách thực tế là mỗi buổi sáng chỉ chọn một điều nếu hoàn thành sẽ khiến ngày hôm đó có ý nghĩa hơn Đ… | Một cách thực tế là mỗi buổi sáng chỉ chọn một điều nếu hoàn thành sẽ khiến ngày hôm đó có ý nghĩa hơn. … |
| 28 | Khi một yêu cầu mới xuất hiện, ta không cần phản ứng ngay; ta có thể hỏi nó có thật sự quan trọng, có th… | Khi một yêu cầu mới xuất hiện, ta không cần phản ứng ngay; ta có thể hỏi nó có thật sự quan trọng, có th… |
| 29 | Quan trọng hơn, chúng trả lại cho ta quyền lựa chọn thay vì để hoàn cảnh quyết định toàn bộ nhịp sống | Quan trọng hơn, chúng trả lại cho ta quyền lựa chọn thay vì để hoàn cảnh quyết định toàn bộ nhịp sống. |
| 30 | Dĩ nhiên, sống có phương hướng không có nghĩa là kiểm soát được mọi biến cố Sẽ có ngày kế hoạch bị phá v… | Dĩ nhiên, sống có phương hướng không có nghĩa là kiểm soát được mọi biến cố. Sẽ có ngày kế hoạch bị phá … |
| 31 | Sự ổn định không nằm ở việc bắt cuộc đời tuân theo lịch của mình Nó nằm ở khả năng nhận ra điều gì đã th… | Sự ổn định không nằm ở việc bắt cuộc đời tuân theo lịch của mình. |
| 32 | Người vững vàng không phải người chưa từng mất nhịp, mà là người biết tìm lại nhịp mà không hoảng loạn | Nó nằm ở khả năng nhận ra điều gì đã thay đổi, chấp nhận chi phí của thay đổi ấy, rồi sắp xếp lại mà khô… |
| 33 | Ta cũng cần phân biệt giữa nghỉ ngơi và trốn tránh Nghỉ ngơi làm năng lượng trở lại, còn trốn tránh thườ… | Người vững vàng không phải người chưa từng mất nhịp, mà là người biết tìm lại nhịp mà không hoảng loạn. |
| 34 | Sau một giờ nghỉ thật sự, ta có thể nhìn công việc rõ hơn Sau một giờ lướt qua những nội dung không chủ … | Ta cũng cần phân biệt giữa nghỉ ngơi và trốn tránh. Nghỉ ngơi làm năng lượng trở lại, còn trốn tránh thư… |
| 35 | Sự khác biệt không nằm hoàn toàn ở hoạt động bên ngoài, mà ở việc ta có biết mình đang tìm kiếm điều gì … | Sau một giờ nghỉ thật sự, ta có thể nhìn công việc rõ hơn. Sau một giờ lướt qua những nội dung không chủ… |
| 36 | Có người nghỉ bằng cách đi bộ quanh khu nhà, có người nấu một bữa cơm, có người ngồi im bên cửa sổ Không… | Sự khác biệt không nằm hoàn toàn ở hoạt động bên ngoài, mà ở việc ta có biết mình đang tìm kiếm điều gì … |
| 37 | Điều quan trọng là hoạt động ấy có giúp hệ thần kinh rời khỏi trạng thái phải phản ứng liên tục hay khôn… | Có người nghỉ bằng cách đi bộ quanh khu nhà, có người nấu một bữa cơm, có người ngồi im bên cửa sổ. Khôn… |
| 38 | Nó chỉ cần cho con người cơ hội trở về với nhịp thở, cảm giác cơ thể và những điều đang hiện diện trước … | Điều quan trọng là hoạt động ấy có giúp hệ thần kinh rời khỏi trạng thái phải phản ứng liên tục hay khôn… |
| 39 | Trong các mối quan hệ, tốc độ cũng tạo ra những hiểu lầm rất khó nhìn thấy Khi nghe một câu khiến mình k… | Nó chỉ cần cho con người cơ hội trở về với nhịp thở, cảm giác cơ thể và những điều đang hiện diện trước … |
| 40 | Ta tưởng mình đang bảo vệ quan điểm, nhưng đôi khi ta chỉ đang bảo vệ cảm giác không muốn bị xem là sai … | Trong các mối quan hệ, tốc độ cũng tạo ra những hiểu lầm rất khó nhìn thấy. Khi nghe một câu khiến mình … |
| 41 | Còn nếu giữ lại một nhịp, ta có thể nghe được nỗi lo nằm dưới câu chữ và nhận ra rằng vấn đề thật sự khá… | Ta tưởng mình đang bảo vệ quan điểm, nhưng đôi khi ta chỉ đang bảo vệ cảm giác không muốn bị xem là sai.… |
| 42 | Điều này không có nghĩa là luôn im lặng hoặc nhường mọi phần đúng cho người khác Một cuộc đối thoại trưở… | Còn nếu giữ lại một nhịp, ta có thể nghe được nỗi lo nằm dưới câu chữ và nhận ra rằng vấn đề thật sự khá… |
| 43 | Nhưng lời nói có trọng lượng thường xuất hiện sau khi người nói đã hiểu mình muốn bảo vệ điều gì Họ khôn… | Điều này không có nghĩa là luôn im lặng hoặc nhường mọi phần đúng cho người khác. Một cuộc đối thoại trư… |
| 44 | Họ nói vừa đủ, để sự rõ ràng đứng ở phía trước và lòng tự ái lùi lại phía sau | Nhưng lời nói có trọng lượng thường xuất hiện sau khi người nói đã hiểu mình muốn bảo vệ điều gì. Họ khô… |
| 45 | Sau cùng, sống chậm hơn một chút không phải là rút lui khỏi đời sống Đó là cách tạo đủ khoảng cách để nh… | Họ nói vừa đủ, để sự rõ ràng đứng ở phía trước và lòng tự ái lùi lại phía sau. |
| 46 | Có việc xứng đáng được làm nhanh, nhất là khi ai đó cần giúp đỡ hoặc một nguy cơ phải được xử lý Có việc… | Sau cùng, sống chậm hơn một chút không phải là rút lui khỏi đời sống. Đó là cách tạo đủ khoảng cách để n… |
| 47 | Trí tuệ không nằm ở một tốc độ cố định, mà ở khả năng chọn đúng nhịp cho điều đang ở trước mặt | Có việc xứng đáng được làm nhanh, nhất là khi ai đó cần giúp đỡ hoặc một nguy cơ phải được xử lý. Có việ… |
| 48 | Nếu hôm nay mọi thứ đều có vẻ gấp, hãy thử dừng lại và chọn một việc thật sự quan trọng Làm việc ấy bằng… | Trí tuệ không nằm ở một tốc độ cố định, mà ở khả năng chọn đúng nhịp cho điều đang ở trước mặt. |
| 49 | Sau đó mới bước sang việc tiếp theo Ta không cần chứng minh giá trị bằng cách luôn vội vàng | Nếu hôm nay mọi thứ đều có vẻ gấp, hãy thử dừng lại và chọn một việc thật sự quan trọng. Làm việc ấy bằn… |
| 50 | Một đời sống có chiều sâu không được đo bằng số lần ta chạy kịp người khác, mà bằng số lần ta vẫn nhận r… | Ta không cần chứng minh giá trị bằng cách luôn vội vàng. Một đời sống có chiều sâu không được đo bằng số… |
| 51 | Có thể ngày mai nhịp sống lại rối, và ta lại quên những điều vừa hiểu Điều đó không làm cho nỗ lực hôm n… | Có thể ngày mai nhịp sống lại rối, và ta lại quên những điều vừa hiểu. Điều đó không làm cho nỗ lực hôm … |
| 52 | Sự trưởng thành hiếm khi là một đường thẳng; nó giống việc nhiều lần quay về với điều mình biết là đúng | Sự trưởng thành hiếm khi là một đường thẳng; nó giống việc nhiều lần quay về với điều mình biết là đúng.… |
| 53 | Mỗi lần quay về, ta bớt hoảng hốt hơn một chút, rõ ràng hơn một chút, và tử tế hơn với giới hạn của chín… | Đôi khi, tiến bộ không phải là không bao giờ lạc hướng, mà là ngày càng biết con đường trở lại. |
| 54 | Đôi khi, tiến bộ không phải là không bao giờ lạc hướng, mà là ngày càng biết con đường trở lại | — |

## Boundary-label and pause-profile mismatch

| Metric | VALIDATED Phase 41G/41H V2 | PRODUCTION |
|---|---:|---:|
| Semantic thought boundaries | 31 | 37 |
| Setup→resolution boundaries | 7 | 0 |
| Paragraph transitions | 16 | 16 |
| Explicit added silence before atempo | 8.64 s | 8.82 s |

The production label `paragraph_transition` corresponds to the 16 validated Phase 41G `thought_transition` labels that Phase 41H reclassified at paragraph crossings. The pause values are present, but the production planner never emits `setup_resolution_boundary` for this source, so the winning +0.06 s behavior is absent at all seven validated setup→resolution sites.

## Reconstruction

- Production preserves the source after whitespace canonicalization: **PASS**.
- Raw production chunks retain sentence-ending periods; validated Phase 41G chunks remove them by design.
- Production canonical joined hash: `98bb7b287f1edf2296c8e181b37ef864caeaa9dc36441bd041ef78fa62b43b08`.
- Validated canonical spoken hash: `c1ea189e0e98a48d77bd5b5ccb124c9ae701b12b08bce2e02c39122bf90dc652`.
