# Báo Cáo Cá Nhân (Reflection Report) - Bài Tập Đánh Giá AI

**Thành viên:** Hoàng Trung Quân - 2A202600720
**Vai trò:** Multi-Judge & Benchmark Engine

---

## 1. Các công việc đã thực hiện (What I Did)

Trong khuôn khổ Lab 14, tôi chịu trách nhiệm thiết kế và tối ưu hóa hệ thống "não bộ" đánh giá (Benchmark Engine) với các tính năng:

1. **Phát triển module Multi-Judge (`engine/llm_judge.py`)**
   - Xây dựng lớp `LLMJudge` để đánh giá câu trả lời bằng 2 mô hình LLM khác nhau.
   - **Xử lý Conflict & Trọng số:** Dựa trên tư duy thiết kế, tôi đã đề xuất phương án xử lý "Conflict": Nếu 2 giám khảo ngang hàng thì lấy trung bình, nhưng nếu có sự chênh lệch trình độ (như GPT-4o và Claude-3-Haiku) thì sử dụng trọng số (VD: 0.6 - 0.4 hoặc 0.9 - 0.1). Trong trường hợp nghi ngờ (lệch điểm quá lớn), khi 2 Judge có điểm số lệch nhau lớn hơn 1 điểm, hệ thống sẽ tự động gọi một **Tie-breaker Judge** (ví dụ: GPT-4-turbo) để đưa ra phán quyết cuối cùng, đảm bảo sự công bằng và chính xác.
   - Tích hợp đo lường mức sử dụng token và ước tính chi phí (estimated cost).

2. **Tối ưu hóa Benchmark Runner (`engine/runner.py`)**
   - Áp dụng chạy bất đồng bộ (async). Nếu gửi 100 câu tuần tự mất hàng trăm giây, nhưng dùng async giúp hệ thống xử lý đồng thời, có thể rút gọn thời gian chỉ còn 3s.
   - **Rate Limit:** Để ngăn chặn lỗi HTTP 429 (Too Many Requests) do "spam" request quá nhanh làm sập API, tôi đã thay thế "chia lô tĩnh" bằng `asyncio.Semaphore` giúp kiểm soát số lượng request song song một cách an toàn.

3. **Tích hợp vào Pipeline Chính (`main.py`)**
   - Kết nối thành công lớp `LLMJudge` thực tế vào `BenchmarkRunner`.
   - Thu thập và tổng hợp các chỉ số mới bao gồm: Tổng chi phí (Total Cost), Số lượng Tokens, và Thời gian trễ (Latency) vào tệp báo cáo `reports/summary.json`. Những dữ liệu này đóng vai trò sống còn giúp hệ thống tự động đưa ra quyết định APPROVE hay BLOCK RELEASE đối với bản cập nhật Agent.

## 2. Những thách thức đã gặp phải (Challenges)

- **Xử lý bất đồng bộ (Asynchronous execution):** Gặp khó khăn trong việc hiểu rõ cách gửi hàng chục request cùng lúc mà không làm sập API. Phải tìm hiểu sự khác biệt giữa `asyncio.gather` thông thường và việc dùng `Semaphore` để kiểm soát luồng.
- **Thiết kế kịch bản Conflict:** Ban đầu, khi hai mô hình chấm điểm khác nhau (ví dụ: 10 và 2), việc lấy điểm trung bình (6) làm mất đi tính gay gắt của sự tranh cãi. Giải pháp Tie-breaker đòi hỏi tư duy hệ thống cao để tránh thiên kiến.

## 3. Bài học rút ra (Lessons Learned)

- Đánh giá một mô hình AI không chỉ nhìn vào độ chính xác, mà phải cân bằng giữa 3 yếu tố: **Thời gian (Latency), Độ chính xác (Accuracy), và Tiền bạc (Cost)**. 
- Một model có độ chính xác cao, thời gian hợp lý nhưng chi phí vượt quá dự kiến sẽ khiến sản phẩm kinh doanh chịu lỗ. Ngược lại, nếu rẻ nhưng xử lý chậm và kém chính xác thì người dùng sẽ cảm thấy khó chịu. Việc xuất ra được các con số đo lường này (như tôi đã code) là bằng chứng sống còn để ra quyết định phát hành sản phẩm.

---
*Báo cáo được hoàn thành trong khuôn khổ Lab 14 - AI Evaluation Benchmarking.*
