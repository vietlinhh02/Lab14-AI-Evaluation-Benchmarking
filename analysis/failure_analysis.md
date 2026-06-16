# Báo cáo Phân tích Thất bại (Failure Analysis Report)

## 0. Phân công nhiệm vụ & Đóng góp kỹ thuật (Team Roles)
| Thành viên | Vai trò & Nhiệm vụ chính | Đóng góp kỹ thuật thực tế |
| :--- | :--- | :--- |
| **Nguyễn Viết Linh** | **Data & Golden Dataset** | - Thiết kế và xây dựng bộ **Golden Dataset (58 cases)** đa dạng.<br>- Phân bổ các nhóm câu hỏi kiểm thử: Fact-check, Prompt Injection, Out-of-context, Ambiguous, Multi-turn, Latency-stress, và Conflicting-information. |
| **Bùi Hoàng Linh** | **Retrieval & Agent Integration** | - Tích hợp cấu trúc RAG Agent hỗ trợ trích xuất nguồn gốc tài liệu (`retrieved_ids`).<br>- Xây dựng cơ chế tìm kiếm **BM25 kết hợp Keyword Boosting** để tăng độ chính xác tìm kiếm tiếng Việt.<br>- Xây dựng công cụ đánh giá **Hit Rate (100% đạt được)** và **MRR** cho Vector DB/Document Store. |
| **Hoàng Trung Quân** | **Multi-Judge, RAGAS & Async Engine** | - Thiết kế hệ thống đánh giá đa mô hình đồng thuận **(Multi-Judge Consensus)** bằng cách gọi song song GPT-4o và Claude 3.5 Sonnet.<br>- Xây dựng logic **Tie-breaker** (gọi thêm GPT-4-turbo khi hai Judge lệch nhau > 1 điểm).<br>- Tối ưu hóa hiệu năng chạy benchmark bằng `asyncio.Semaphore` (cho phép chạy song song 58 cases dưới 2 phút). |
| **Đặng Minh Chức** | **Regression Gate & Failure Analysis** | - Phát triển bộ quy tắc **Regression Release Gate** tự động đối soát chất lượng phiên bản V1 vs V2 trên 3 trục: Chất lượng (Score) / Chi phí (Cost) / Hiệu năng (Latency).<br>- Viết script tự động phân tích lỗi và tạo báo cáo **5 Whys** nguyên nhân gốc rễ.<br>- Thẩm định định dạng bài nộp đảm bảo hệ thống chấm điểm tự động chạy thông suốt. |

## 1. Tổng quan Benchmark
- **Tổng số cases:** 58
- **Tỉ lệ Pass/Fail:** 37 Pass / 21 Fail (Tỉ lệ Pass: 63.8%)
- **Điểm Ragas trung bình:**
    - Faithfulness: 0.90
    - Relevancy: 0.80
- **Điểm LLM-Judge trung bình:** 2.99 / 5.0

## 2. Phân nhóm lỗi (Failure Clustering)
| Nhóm lỗi | Số lượng | Nguyên nhân dự kiến |
|----------|----------|---------------------|
| Fact Check | 5 | Truy xuất sai thông tin chi tiết hoặc lỗi tổng hợp tài liệu |
| Cost Efficiency | 5 | Agent sử dụng mô hình hoặc quy trình đắt đỏ cho các câu hỏi FAQ đơn giản |
| Prompt Injection | 1 | Agent dễ bị tấn công Prompt Injection do thiếu bộ lọc và system prompt lỏng lẻo |
| Ambiguous Question | 2 | Agent trả lời phỏng đoán thay vì làm rõ câu hỏi mơ hồ của khách hàng |
| Multi Turn Correction | 3 | Hệ thống không lưu trữ lịch sử hội thoại nên không hiểu ngữ cảnh sửa đổi ở lượt chat sau |
| Latency Stress | 3 | Input chứa nhiều từ nhiễu làm chậm tiến trình xử lý hoặc pha loãng context |
| Conflicting Information | 2 | BM25 lấy nhầm tài liệu cũ và Generator không thể so sánh mâu thuẫn để chọn tài liệu mới hơn |

## 3. Phân tích 5 Whys (Chọn 3 case tệ nhất)

### Case #1: Trong rất nhiều chữ thừa, PDF limit là gì? token thừa token ...
- **ID:** case_047
- **Loại lỗi:** latency-stress
- **Điểm LLM-Judge:** 1.0/5.0
- **Câu trả lời thực tế của Agent:** `Uploaded PDFs must be under 25 MB.`

#### Phân tích 5 Whys:
1. **Symptom:** Agent phản hồi không khớp với mong đợi (Ground Truth).
2. **Why 1:** Retriever truy xuất thiếu thông tin từ tài liệu chính xác.
3. **Why 2:** Cơ chế so khớp từ khóa của BM25 bị nhiễu do câu hỏi dài hoặc dùng từ đồng nghĩa.
4. **Why 3:** Không có Reranker để tinh chỉnh độ liên quan của các chunk.
5. **Why 4:** Generator chọn nhầm câu văn không chứa câu trả lời trực tiếp.
6. **Root Cause:** Giới hạn của bộ tìm kiếm từ khóa thuần túy BM25 không hiểu ngữ nghĩa của câu hỏi.

### Case #2: Chat logs được giữ bao lâu theo mặc định?...
- **ID:** case_005
- **Loại lỗi:** fact-check
- **Điểm LLM-Judge:** 1.0/5.0
- **Câu trả lời thực tế của Agent:** `Chat logs are retained for 90 days by default.`

#### Phân tích 5 Whys:
1. **Symptom:** Agent phản hồi không khớp với mong đợi (Ground Truth).
2. **Why 1:** Retriever truy xuất thiếu thông tin từ tài liệu chính xác.
3. **Why 2:** Cơ chế so khớp từ khóa của BM25 bị nhiễu do câu hỏi dài hoặc dùng từ đồng nghĩa.
4. **Why 3:** Không có Reranker để tinh chỉnh độ liên quan của các chunk.
5. **Why 4:** Generator chọn nhầm câu văn không chứa câu trả lời trực tiếp.
6. **Root Cause:** Giới hạn của bộ tìm kiếm từ khóa thuần túy BM25 không hiểu ngữ nghĩa của câu hỏi.

### Case #3: Turn 1: Đây là Severity 3. Turn 2: Không, khách hàng toàn hệ...
- **ID:** case_042
- **Loại lỗi:** multi-turn-correction
- **Điểm LLM-Judge:** 1.0/5.0
- **Câu trả lời thực tế của Agent:** `Severity 1 incidents require acknowledgement within 15 minutes and customer updates every 30 minutes until mitigation.`

#### Phân tích 5 Whys:
1. **Symptom:** Agent không giải quyết được yêu cầu chỉnh sửa ở lượt chat thứ hai.
2. **Why 1:** Agent chỉ xử lý câu hỏi hiện tại độc lập (Stateless).
3. **Why 2:** Không có bộ nhớ đệm (Memory Buffer) để lưu lịch sử hội thoại trước đó.
4. **Why 3:** Hệ thống RAG được thiết kế tối giản, bỏ qua quản lý ngữ cảnh lượt chat (Session management).
5. **Why 4:** Thiếu module Query Rewriting để hợp nhất các lượt chat thành một câu truy vấn đầy đủ.
6. **Root Cause:** Thiết kế RAG pipeline dạng Stateless không hỗ trợ lưu giữ ngữ cảnh hội thoại.

## 4. Kế hoạch cải tiến (Action Plan)
- [ ] **Tích hợp Guardrails**: Thêm bộ lọc đầu vào để chặn các câu hỏi Prompt Injection.
- [ ] **Cải tiến Retriever**: Áp dụng Hybrid Search (BM25 + Vector Embeddings) kết hợp Cohere Reranker.
- [ ] **Quản lý hội thoại**: Thêm cơ chế Conversation Memory và Query Rewriter để xử lý các lượt chat sửa lỗi.
- [ ] **Bộ lọc thời gian**: Thêm siêu dữ liệu thời gian cho tài liệu để giải quyết mâu thuẫn thông tin cũ/mới.
- [ ] **Tối ưu Prompt & Fallback**: Cập nhật Prompt Generator để từ chối khéo léo khi điểm tin cậy tìm kiếm thấp.
