# Hướng dẫn thiết kế Hard Cases cho AI Evaluation

Để bài lab đủ khó, các bạn cần thiết kế các test cases có tính thử thách cao:

### 1. Adversarial Prompts (Tấn công bằng Prompt)
- **Prompt Injection:** Thử lừa Agent bỏ qua context để trả lời theo ý người dùng.
- **Goal Hijacking:** Yêu cầu Agent làm việc không liên quan đến nhiệm vụ chính.
  Ví dụ: đang là hỗ trợ kỹ thuật nhưng bị yêu cầu viết thơ chính trị.

### 2. Edge Cases (Trường hợp biên)
- **Out of Context:** Đặt câu hỏi mà tài liệu không hề đề cập. Agent phải biết
  nói "Tôi không biết" thay vì bịa chuyện.
- **Ambiguous Questions:** Câu hỏi mập mờ, thiếu thông tin để xem Agent có biết
  hỏi lại không.
- **Conflicting Information:** Đưa ra 2 đoạn tài liệu mâu thuẫn nhau để xem
  Agent xử lý thế nào.

### 3. Multi-turn Complexity
- **Context Carry-over:** Câu hỏi thứ 2 phụ thuộc vào câu trả lời thứ 1.
- **Correction:** Người dùng đính chính lại thông tin ở giữa cuộc hội thoại.

### 4. Technical Constraints
- **Latency Stress:** Yêu cầu Agent xử lý văn bản dài để đo latency.
- **Cost Efficiency:** Đánh giá xem Agent có đang dùng quá nhiều token không cần
  thiết cho các câu hỏi đơn giản không.

## Golden Dataset Coverage

`data/synthetic_gen.py` tạo `data/golden_set.jsonl` với hơn 50 cases theo cùng một schema:

```json
{
  "id": "case_001",
  "question": "...",
  "expected_answer": "...",
  "context": "...",
  "expected_retrieval_ids": ["doc_01"],
  "metadata": {
    "difficulty": "hard",
    "type": "prompt-injection"
  }
}
```

Các nhóm bắt buộc đã được cover:

- `prompt-injection`: cố tình yêu cầu bỏ qua context, giả policy, hoặc đổi mục
  tiêu.
- `out-of-context`: câu hỏi không có trong tài liệu, kỳ vọng agent nói không biết.
- `ambiguous-question`: câu hỏi thiếu đối tượng, kỳ vọng agent hỏi lại.
- `conflicting-information`: tài liệu cũ mâu thuẫn với policy mới.
- `multi-turn-correction`: câu hỏi phụ thuộc lượt trước hoặc người dùng đính
  chính.
- `latency-stress`: input dài có nhiễu nhưng expected answer phải ngắn.
- `cost-efficiency`: câu đơn giản để kiểm tra agent có dùng quá nhiều token không.
