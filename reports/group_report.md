# Báo cáo Nhóm - AI Evaluation Factory (Group Report)

## 0. Phân công nhiệm vụ & Đóng góp kỹ thuật (Team Roles)
| Thành viên | Vai trò & Nhiệm vụ chính | Đóng góp kỹ thuật thực tế |
| :--- | :--- | :--- |
| **Người 1** | **Data & Golden Dataset** | - Thiết kế và xây dựng bộ **Golden Dataset (58 cases)** đa dạng.<br>- Phân bổ các nhóm câu hỏi kiểm thử: Fact-check, Prompt Injection, Out-of-context, Ambiguous, Multi-turn, Latency-stress, và Conflicting-information. |
| **Người 2** | **Retrieval & Agent Integration** | - Tích hợp cấu trúc RAG Agent hỗ trợ trích xuất nguồn gốc tài liệu (`retrieved_ids`).<br>- Xây dựng cơ chế tìm kiếm **BM25 kết hợp Keyword Boosting** để tăng độ chính xác tìm kiếm tiếng Việt.<br>- Xây dựng công cụ đánh giá **Hit Rate (100% đạt được)** và **MRR** cho Vector DB/Document Store. |
| **Người 3** | **Multi-Judge, RAGAS & Async Engine** | - Thiết kế hệ thống đánh giá đa mô hình đồng thuận **(Multi-Judge Consensus)** bằng cách gọi song song GPT-4o và Claude 3.5 Sonnet.<br>- Xây dựng logic **Tie-breaker** (gọi thêm GPT-4-turbo khi hai Judge lệch nhau > 1 điểm).<br>- Tối ưu hóa hiệu năng chạy benchmark bằng `asyncio.Semaphore` (cho phép chạy song song 58 cases dưới 2 phút). |
| **Người 4** | **Regression Gate & Failure Analysis** | - Phát triển bộ quy tắc **Regression Release Gate** tự động đối soát chất lượng phiên bản V1 vs V2 trên 3 trục: Chất lượng (Score) / Chi phí (Cost) / Hiệu năng (Latency).<br>- Viết script tự động phân tích lỗi và tạo báo cáo **5 Whys** nguyên nhân gốc rễ.<br>- Thẩm định định dạng bài nộp đảm bảo hệ thống chấm điểm tự động chạy thông suốt. |

## 1. Tổng quan Benchmark
- **Tổng số cases:** 58
- **Tỉ lệ Pass/Fail:** 35 Pass / 23 Fail (Tỉ lệ Pass: 60.3%)
- **Điểm Ragas trung bình:**
    - Faithfulness: 0.90
    - Relevancy: 0.80
- **Điểm LLM-Judge trung bình:** 3.17 / 5.0

## 2. Phân nhóm lỗi (Failure Clustering)
| Nhóm lỗi | Số lượng | Nguyên nhân dự kiến |
|----------|----------|---------------------|
| Fact Check | 4 | Truy xuất sai thông tin chi tiết hoặc lỗi tổng hợp tài liệu |
| Safety Boundary | 1 | Lỗi phân tích hoặc xử lý tài liệu |
| Prompt Injection | 1 | Agent dễ bị tấn công Prompt Injection do thiếu bộ lọc và system prompt lỏng lẻo |
| Out Of Context | 4 | Retriever lấy nhầm tài liệu hoặc Agent bịa câu trả lời khi thiếu thông tin |
| Ambiguous Question | 1 | Agent trả lời phỏng đoán thay vì làm rõ câu hỏi mơ hồ của khách hàng |
| Multi Turn Correction | 3 | Hệ thống không lưu trữ lịch sử hội thoại nên không hiểu ngữ cảnh sửa đổi ở lượt chat sau |
| Latency Stress | 3 | Input chứa nhiều từ nhiễu làm chậm tiến trình xử lý hoặc pha loãng context |
| Conflicting Information | 4 | BM25 lấy nhầm tài liệu cũ và Generator không thể so sánh mâu thuẫn để chọn tài liệu mới hơn |
| Cost Efficiency | 2 | Agent sử dụng mô hình hoặc quy trình đắt đỏ cho các câu hỏi FAQ đơn giản |

## 3. Phân tích 5 Whys (Chọn 3 case tệ nhất)
*(Xem chi tiết trong tệp analysis/failure_analysis.md)*

## 4. Kế hoạch cải tiến (Action Plan)
- **Tích hợp Guardrails**: Thêm bộ lọc đầu vào để chặn các câu hỏi Prompt Injection.
- **Cải tiến Retriever**: Áp dụng Hybrid Search (BM25 + Vector Embeddings) kết hợp Cohere Reranker.
- **Quản lý hội thoại**: Thêm cơ chế Conversation Memory và Query Rewriter để xử lý các lượt chat sửa lỗi.
- **Bộ lọc thời gian**: Thêm siêu dữ liệu thời gian cho tài liệu để giải quyết mâu thuẫn thông tin cũ/mới.
- **Tối ưu Prompt & Fallback**: Cập nhật Prompt Generator để từ chối khéo léo khi điểm tin cậy tìm kiếm thấp.
