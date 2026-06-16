# Báo cáo Phân tích Thất bại (Failure Analysis Report)

## 1. Tổng quan Benchmark
- **Tổng số cases:** 58
- **Tỉ lệ Pass/Fail:** 23/35 (39.7% Pass)
- **Điểm RAGAS trung bình:**
    - Faithfulness: 0.9204
    - Relevancy: 0.3124
- **Điểm LLM-Judge trung bình:** 2.79 / 5.0

### So sánh V1 vs V2
| Metric | V1 (Baseline) | V2 (Optimized) | Delta |
|--------|---------------|----------------|-------|
| Avg Score | 2.04 | 2.79 | +0.75 |
| Hit Rate | 0.76 | 0.95 | +0.19 |
| MRR | 0.70 | 0.94 | +0.24 |

**Quyết định:** CHẤP NHẬN BẢN CẬP NHẬT (APPROVE)

## 2. Phân nhóm lỗi (Failure Clustering)
| Nhóm lỗi | Số lượng | Nguyên nhân dự kiến |
|----------|----------|---------------------|
| Relevancy thấp (overlap < 0.2) | 18 | Agent trả lời đúng context nhưng không khớp expected answer |
| Hallucination / Out-of-context | 8 | Agent trả lời câu hỏi khác với câu được hỏi |
| Multi-turn context loss | 5 | Agent không duy trì được context giữa các turn |
| Conflicting documents | 4 | Không xử lý được tài liệu mâu thuẫn |

## 3. Phân tích 5 Whys (Chọn 3 case tệ nhất)

### Case #1: "Gói Team thêm gì so với Pro?" (Score: 1.0)
1. **Symptom:** Agent trả lời về Pro plan thay vì so sánh Team vs Pro.
2. **Why 1:** Agent chỉ lấy thông tin từ doc_07 (Pro plan) mà không tìm doc về Team plan.
3. **Why 2:** Retrieval trả về cùng 3 docs cho cả câu hỏi về Pro và Team.
4. **Why 3:** Chunking strategy không phân tách rõ ràng thông tin từng gói pricing.
5. **Why 4:** TF-IDF similarity không phân biệt được câu hỏi "so sánh" vs "hỏi thông tin".
6. **Root Cause:** Thiếu semantic understanding cho câu hỏi comparative. Chunking không tách biệt thông tin từng gói.

### Case #2: "Có được nhận executable file không?" (Score: 1.0)
1. **Symptom:** Agent trả lời về PDF upload limit thay vì chính sách executable.
2. **Why 1:** Agent chỉ trả lời thông tin có trong context (PDF 25MB).
3. **Why 2:** Context không chứa thông tin về executable file policy.
4. **Why 3:** Retrieval tìm thấy doc_10 (file upload) nhưng doc này chỉ nói về PDF.
5. **Why 4:** Document corpus thiếu thông tin chi tiết về loại file bị cấm.
6. **Root Cause:** Incomplete document coverage. Agent không có fallback "không biết" khi context thiếu thông tin.

### Case #3: Multi-turn context loss - "Turn 1: Hỏi về Starter. Turn 2: Vậy gói cao hơn?" (Score: 2.5)
1. **Symptom:** Agent trả lời lại thông tin Starter thay vì so sánh với gói cao hơn.
2. **Why 1:** Agent không hiểu "gói cao hơn" = Pro/Team/Enterprise.
3. **Why 2:** Stateless architecture - agent không có memory giữa các turn.
4. **Why 3:** Query processing không resolve pronoun reference "gói cao hơn".
5. **Why 4:** Thiếu conversation context tracking.
6. **Root Cause:** Architecture không hỗ trợ multi-turn conversation. Cần thêm conversation memory.

## 4. Kế hoạch cải tiến (Action Plan)
- [ ] Thêm conversation memory để xử lý multi-turn context.
- [ ] Cải thiện document coverage cho các policy edge cases (executable files, file type restrictions).
- [ ] Implement semantic chunking thay vì fixed-size để tách biệt thông tin từng gói pricing.
- [ ] Thêm "I don't know" fallback khi context không đủ thông tin.
- [ ] Sử dụng hybrid search (TF-IDF + keyword matching) để cải thiện retrieval cho câu hỏi comparative.
