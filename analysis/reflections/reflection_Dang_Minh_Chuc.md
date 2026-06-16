# Báo cáo Cá nhân (Individual Reflection Report)
- **Họ và tên:** Đặng Minh Chức
- **Mã số sinh viên:** 2A202600611
- **Nhánh thực hiện:** `chuc`
- **Vai trò:** **Regression Gate, Failure Analysis & Submission Check**

---

## 1. Đóng góp kỹ thuật (Engineering Contributions)

Trong bài Lab 14, tôi chịu trách nhiệm chính về phần DevOps & Analyst, thiết lập chốt chặn phiên bản và tự động hóa phân tích kiểm thử. Cụ thể:
1. **Thiết kế & Xây dựng Regression Release Gate:** 
   - Đã tạo module [engine/regression_gate.py](file:///F:/student/AIthucChien/lab14/Lab14-AI-Evaluation-Benchmarking/engine/regression_gate.py) để tự động hóa việc đưa ra quyết định Release/Rollback cho sản phẩm.
   - Triển khai thuật toán đối soát 3 trục chất lượng chính: Chất lượng phản hồi (Quality Score Delta >= -0.05), Chất lượng truy xuất (Retrieval Hit Rate >= 85%), Thời gian xử lý trung bình (Latency <= 2s/case), và Tỉ lệ tăng ngân sách (Cost Increase <= 20%).
2. **Tự động hóa Báo cáo Thất bại (Failure Analysis):**
   - Cập nhật [engine/runner.py](file:///F:/student/AIthucChien/lab14/Lab14-AI-Evaluation-Benchmarking/engine/runner.py) để thu thập thêm siêu dữ liệu phân loại câu hỏi (difficulty, type) từ dataset gốc vào file kết quả benchmark.
   - Phát triển script tự động phân tích [analysis/auto_analyze.py](file:///F:/student/AIthucChien/lab14/Lab14-AI-Evaluation-Benchmarking/analysis/auto_analyze.py) đọc file JSON kết quả, tự động thống kê tỉ lệ Pass/Fail, phân nhóm lỗi (Failure Clustering) và tự động điền mẫu phân tích **5 Whys** nguyên nhân gốc rễ cho 3 trường hợp tệ nhất.
3. **Thẩm định bài nộp (Submission Check):**
   - Đảm bảo tính tương thích và thực thi của script thẩm định [check_lab.py](file:///F:/student/AIthucChien/lab14/Lab14-AI-Evaluation-Benchmarking/check_lab.py), sửa các lỗi về Unicode Encode trên Windows Terminal bằng cách khởi tạo chạy qua biến môi trường UTF-8 (`PYTHONUTF8=1`).

---

## 2. Chiều sâu kỹ thuật (Technical Depth)

### 2.1. Đánh giá chất lượng truy xuất (MRR & Hit Rate)
* **Hit Rate:** Là tỉ lệ số câu hỏi mà Retriever tìm thấy ít nhất 1 tài liệu đúng (Ground Truth ID) nằm trong Top-K tài liệu lấy ra. Chỉ số này phản ánh năng lực "tìm kiếm bao phủ" của Vector DB.
* **MRR (Mean Reciprocal Rank):** Là số trung bình cộng của nghịch đảo thứ hạng tài liệu đúng đầu tiên tìm thấy. Công thức: $MRR = \frac{1}{|Q|} \sum_{i=1}^{|Q|} \frac{1}{\text{rank}_i}$. 
  * *Ý nghĩa:* Nếu tài liệu đúng nằm ngay ở vị trí số 1 (rank 1), điểm MRR là 1.0. Nếu nó nằm ở vị trí số 3, điểm MRR giảm xuống còn 0.33. MRR giúp đo lường mức độ tối ưu trong việc sắp xếp (Reranking) các kết quả tìm kiếm đưa vào prompt, hạn chế lãng phí token.

### 2.2. Đồng thuận đa Judge (Multi-Judge Consensus) & Triệt tiêu thiên kiến
* **Tại sao không dùng 1 Judge duy nhất?** Một LLM Judge đơn lẻ (ví dụ chỉ dùng GPT-4o) thường bị các lỗi thiên vị hệ thống như **Position Bias** (luôn thích câu trả lời đầu tiên), **Verbosity Bias** (luôn cho điểm cao hơn các câu trả lời dài dòng hơn), hoặc **Style Bias** (chuộng ngôn từ kiểu GPT).
* **Độ đồng thuận (Agreement Rate):** Đo lường mức độ đồng nhất điểm số giữa các Judge (GPT-4o và Claude 3.5 Sonnet). Nếu có sự lệch điểm đáng kể (> 1 điểm trên thang 5), hệ thống sẽ kích hoạt một mô hình Judge độc lập thứ ba làm **Tie-breaker** (GPT-4-turbo) để đưa ra phán quyết cuối cùng, giúp tăng tính khách quan của hệ thống benchmark.

### 2.3. Đánh đổi giữa Chi phí và Chất lượng (Quality vs Cost Trade-offs)
* Chi phí đánh giá chất lượng tự động bằng LLM rất đắt đỏ. Qua phân tích, chúng tôi nhận thấy các câu hỏi FAQ đơn giản có thể được xử lý trực tiếp bởi các mô hình nhỏ (Small models) và tìm kiếm từ khóa cục bộ (BM25). 
* RAG Engine chỉ nên kích hoạt các mô hình suy luận đắt tiền (Large LLMs / Multi-agent) cho các câu hỏi thuộc nhóm rủi ro cao (pháp lý, bảo mật dữ liệu, mâu thuẫn chính sách) để tối ưu hóa 30% chi phí vận hành mà không làm giảm độ chính xác của phản hồi.

---

## 3. Giải quyết vấn đề (Problem Solving)

1. **Khắc phục lỗi Unicode Encode trên Windows:**
   - *Vấn đề:* Khi chạy benchmark trên PowerShell Windows, python bị crash do lỗi charmap không mã hóa được các icon Unicode (`charmap codec can't encode character '\U0001f680'`).
   - *Giải pháp:* Thiết lập chạy script kèm biến môi trường `PYTHONUTF8=1` để ép python giao tiếp UTF-8 với Windows Terminal, giúp chạy thông suốt cả pipeline.
2. **Nhận diện lỗi hệ thống Stateless:**
   - *Vấn đề:* Trong quá trình phân tích lỗi Multi-turn, nhận thấy Agent trả về điểm 1/5 ở các lượt chat sau vì không nhớ thông tin lượt chat trước.
   - *Giải pháp:* Đề xuất kế hoạch tích hợp bộ nhớ Session và module Query Rewriter vào Action Plan của nhóm để đội kỹ thuật chỉnh sửa RAG Pipeline trong phiên bản sau.
