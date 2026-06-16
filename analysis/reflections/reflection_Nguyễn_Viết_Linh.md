# Báo cáo Cá nhân (Individual Reflection Report)
- **Họ và tên:** Nguyễn Viết Linh
- **Mã số sinh viên:** 2A202600719
- **Nhánh thực hiện:** `main`
- **Vai trò:** **Data Engineer & Golden Dataset Designer**

---

## 1. Đóng góp kỹ thuật (Engineering Contributions)

Trong bài Lab 14, tôi đảm nhận vai trò kiến trúc sư dữ liệu, chịu trách nhiệm xây dựng nền tảng đánh giá (evaluation foundation) cho toàn bộ hệ thống Benchmark. Cụ thể:

1. **Thiết kế & Xây dựng Golden Dataset (58 cases):**
   - Tạo bộ dữ liệu vàng gồm 58 câu hỏi kiểm thử đa dạng, phản ánh đúng các tình huống thực tế mà Agent phải xử lý trong môi trường production.
   - Mỗi case được gán nhãn đầy đủ các trường metadata: `id`, `question`, `ground_truth`, `expected_doc_ids`, `difficulty`, `type` (loại câu hỏi), giúp downstream pipeline (`engine/runner.py`, `analysis/auto_analyze.py`) có thể tự động thống kê và phân nhóm lỗi.
   - Cấu trúc dataset tuân thủ schema chuẩn để tương thích với RAGAS, Multi-Judge, và Regression Gate.

2. **Phân bổ 7 nhóm câu hỏi kiểm thử chiến lược:**
   - **Fact-check:** Kiểm thử độ trung thực với tài liệu nguồn.
   - **Prompt Injection:** Thử độ an toàn của Agent trước các cuộc tấn công chèn prompt độc hại.
   - **Out-of-context:** Buộc Agent phải từ chối trả lời khi thông tin nằm ngoài tài liệu.
   - **Ambiguous:** Kiểm thử khả năng làm rõ câu hỏi mơ hồ.
   - **Multi-turn Correction:** Mô phỏng hội thoại nhiều lượt có sửa đổi thông tin.
   - **Latency-stress:** Chứa nhiều từ nhiễu (noise) để đo độ ổn định và tốc độ xử lý.
   - **Conflicting Information:** Tạo tình huống tài liệu cũ và mới mâu thuẫn nhau.

3. **Thiết kế tiêu chí Pass/Fail rõ ràng:**
   - Mỗi case có `ground_truth` (câu trả lời mong đợi) và `expected_doc_ids` (danh sách tài liệu nguồn dự kiến) để so khớp tự động.
   - Hệ thống chấm điểm dựa trên sự trùng khớp giữa câu trả lời của Agent với ground truth (sử dụng LLM Judge) và độ chính xác của tài liệu được truy xuất (Hit Rate / MRR).

---

## 2. Chiều sâu kỹ thuật (Technical Depth)

### 2.1. Tại sao Golden Dataset lại là "xương sống" của hệ thống Benchmark?
* Mọi hệ thống đánh giá AI đều chỉ tốt bằng chất lượng dữ liệu kiểm thử của nó. Nếu bộ dataset thiếu đa dạng hoặc bị "lệch" (bias) về phía các câu hỏi dễ, hệ thống sẽ luôn đánh giá quá cao năng lực của Agent (gọi là **"Goodhart's Law"**: *Khi một chỉ số trở thành mục tiêu, nó không còn là chỉ số tốt nữa*).
* Một Golden Dataset tốt phải đảm bảo 3 tính chất: **Đại diện (Representativeness)** - phản ánh đúng phân phối câu hỏi thực tế; **Đa dạng (Diversity)** - bao phủ nhiều edge case; và **Khách quan (Objectivity)** - có ground truth rõ ràng, không tranh cãi.

### 2.2. Phân loại Failure Modes - Góc nhìn từ dữ liệu
* Dựa trên kết quả chạy V2, tôi nhận thấy tỉ lệ Fail tập trung chủ yếu ở 3 nhóm: **Fact Check (4-5 cases)**, **Out Of Context (4 cases)**, và **Conflicting Information (2-4 cases)**.
* Nguyên nhân cốt lõi: Agent hiện tại dùng BM25 thuần túy nên chỉ "nhìn thấy" từ khóa chính xác, không hiểu được các biến thể ngữ nghĩa. Khi tôi thiết kế các case Out-of-context với cách diễn đạt gián tiếp (ví dụ: hỏi về chính sách qua ví dụ cụ thể thay vì hỏi thẳng), BM25 liên tục miss.
* Điều này khẳng định vai trò của dataset: nó **phơi bày điểm yếu thực sự** của hệ thống thay vì để hệ thống tự đánh giá mình.

### 2.3. Thiết kế Ground Truth & Expected Doc IDs - "Hai lớp chấm điểm"
* Mỗi case trong dataset có **hai lớp kiểm chứng**:
  1. **Lớp Retrieval:** `expected_doc_ids` - danh sách tài liệu nguồn kỳ vọng. Hệ thống tính **Hit Rate** (có tìm thấy tài liệu đúng không) và **MRR** (tài liệu đúng ở vị trí thứ mấy). Kết quả V2 đạt **Hit Rate 100%** chứng tỏ Retriever không miss tài liệu, vấn đề nằm ở khâu Generator tổng hợp.
  2. **Lớp Generation:** `ground_truth` - câu trả lời mẫu. LLM Judge so sánh câu trả lời của Agent với ground truth để ra điểm 1-5.
* Việc tách làm 2 lớp giúp quy trình **Failure Analysis** (do Đặng Minh Chức phụ trách) chỉ ra chính xác lỗi ở giai đoạn nào (Retrieval vs Generation), tiết kiệm rất nhiều thời gian debug.

### 2.4. Tầm quan trọng của Latency-Stress & Conflicting Information cases
* **Latency-stress cases** (như case_047 với input chứa nhiều token thừa) đo khả năng Agent "lọc nhiễu" và trả lời đúng trọng tâm. Đây là test quan trọng vì người dùng thực tế thường viết câu hỏi dài dòng, không rõ ràng.
* **Conflicting Information cases** (như case_005) mô phỏng tình huống tài liệu cũ vẫn còn trong index nhưng đã được cập nhật. Đây là vấn đề thực tế rất hay gặp trong các hệ thống RAG doanh nghiệp - nếu không có chiến lược versioning tài liệu, Agent sẽ trả lời sai thông tin mà không hề biết.

---

## 3. Giải quyết vấn đề (Problem Solving)

1. **Thiết kế dataset cân bằng giữa độ khó và tính thực tế:**
   - *Vấn đề:* Ban đầu các case quá "sạch" (clean questions), Agent đạt điểm rất cao, không phát hiện được edge case.
   - *Giải pháp:* Tôi bổ sung các câu hỏi thực tế kiểu người dùng cuối: viết tắt, sai chính tả nhẹ, ngữ cảnh không đầy đủ. Đồng thời thêm các case "bẫy" (adversarial cases) để test độ robust của Agent.

2. **Đảm bảo tính nhất quán giữa Ground Truth và tài liệu nguồn:**
   - *Vấn đề:* Một số case ban đầu có ground truth suy ra từ nhiều tài liệu cùng lúc, khiến việc đánh giá `expected_doc_ids` trở nên mơ hồ.
   - *Giải pháp:* Tôi chuẩn hóa lại quy tắc: mỗi case phải map rõ ràng với **1 hoặc 2 tài liệu cụ thể**, có đoạn văn chứa câu trả lời để LLM Judge có thể đối chiếu.

3. **Phối hợp nhịp nhàng với các thành viên khác:**
   - Cung cấp dataset đúng schema và đầy đủ metadata ngay từ đầu, giúp Hoàng Trung Quân (Multi-Judge Engine) tích hợp nhanh vào `engine/runner.py` mà không phải sửa lại cấu trúc dữ liệu.
   - Phối hợp với Đặng Minh Chức để đảm bảo Failure Analysis có thể thống kê được theo từng `type` (Fact-check, Multi-turn, v.v.) từ chính metadata tôi đã gán sẵn.

---

## 4. Bài học rút ra (Lessons Learned)

- **Chất lượng dữ liệu quyết định chất lượng đánh giá:** Một hệ thống benchmark phức tạp với RAGAS, Multi-Judge, Regression Gate... sẽ trở nên vô nghĩa nếu Golden Dataset nghèo nàn hoặc thiếu tính đa dạng. Dữ liệu tốt là điều kiện tiên quyết.
- **Thiết kế test case cũng là một dạng tư duy phản biện:** Khi xây dataset, mình không chỉ nghĩ "Agent cần trả lời gì" mà còn nghĩ "Agent có thể sai ở đâu". Mỗi failure mode tiềm ẩn phải có ít nhất 1 case tương ứng.
- **Metadata là chìa khóa cho phân tích tự động:** Việc gán sẵn `type` và `difficulty` cho từng case tưởng chừng nhỏ nhặt, nhưng lại giúp script `auto_analyze.py` tự động phân nhóm lỗi mà không cần hard-code bất kỳ rule nào. Đây là minh chứng cho triết lý **"data should describe itself"** trong engineering.
- **Kết quả V2 bị Regression Gate chặn lại (ROLLBACK):** Mặc dù Retriever đạt Hit Rate 100%, điểm trung bình giảm nhẹ từ 3.06 → 2.99 (vượt ngưỡng cho phép -0.05). Điều này cho thấy khi phát triển Agent, việc tăng "sức mạnh" retriever không đồng nghĩa với tăng chất lượng tổng thể - cần đánh giá end-to-end mới phản ánh đúng giá trị sản phẩm.

---

*Báo cáo được hoàn thành trong khuôn khổ Lab 14 - AI Evaluation Benchmarking.*
