# Reflection - Bùi Hoàng Linh (MSV: 2A202600804)

## 1. Điều gì hoạt động tốt?
- **Faithfulness cao (0.92):** Agent trả lời dựa trên context, không hallucinate thông tin mới.
- **Retrieval V2 cải thiện đáng kể:** Hit rate từ 0.76 lên 0.95, MRR từ 0.70 lên 0.94.
- **Xử lý out-of-context tốt:** Các câu hỏi về CEO salary, Bitcoin payment, HR policy đều trả lời "Không có đủ thông tin" đúng cách.
- **Xử lý adversarial attacks:** Agent từ chối các prompt injection (debug mode, ignore context, fake policy).

## 2. Điều gì cần cải thiện?
- **Relevancy thấp (0.31):** Agent trả lời đúng context nhưng không khớp expected answer format.
- **Multi-turn context loss:** Agent không maintain context giữa các turns trong conversation.
- **Comparative questions:** Agent không xử lý được câu hỏi so sánh (Team vs Pro, Starter vs higher plans).
- **Conflicting documents:** Agent chọn document cũ (memo 2022) thay vì policy mới (2025).

## 3. Bài học rút về RAG pipeline
- **Chunking strategy quan trọng:** Fixed-size chunking tách rời thông tin liên quan. Semantic chunking sẽ tốt hơn.
- **Hybrid search cần thiết:** TF-IDF alone không đủ cho semantic understanding. Kết hợp keyword + semantic search.
- **Conversation memory cần thiết:** Stateless architecture không phù hợp cho multi-turn support chat.
- **Document versioning:** Cần timestamp hoặc version tag để ưu tiên document mới hơn.

## 4. Kế hoạch cá nhân
- Tìm hiểu thêm về semantic chunking techniques (LangChain text splitters).
- Nghiên cứu hybrid search (BM25 + vector search) cho retrieval.
- Implement conversation memory với window buffer cho multi-turn support.
