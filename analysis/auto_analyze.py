import json
import os

def run_analysis():
    results_path = "reports/benchmark_results.json"
    summary_path = "reports/summary.json"
    output_path = "analysis/failure_analysis.md"

    if not os.path.exists(results_path):
        print(f"❌ Không tìm thấy {results_path}. Hãy chạy benchmark trước.")
        return

    with open(results_path, "r", encoding="utf-8") as f:
        results = json.load(f)

    with open(summary_path, "r", encoding="utf-8") as f:
        summary = json.load(f)

    total_cases = len(results)
    failed_cases = [r for r in results if r["status"] == "fail"]
    passed_cases = [r for r in results if r["status"] == "pass"]
    num_fail = len(failed_cases)
    num_pass = len(passed_cases)

    # Calculate RAGAS averages
    avg_faithfulness = sum(r["ragas"].get("faithfulness", 0.0) for r in results) / total_cases
    avg_relevancy = sum(r["ragas"].get("relevancy", 0.0) for r in results) / total_cases
    avg_judge_score = summary["metrics"]["avg_score"]

    # Group failures by metadata type
    failure_types = {}
    for r in failed_cases:
        m_type = r.get("metadata", {}).get("type", "unknown")
        failure_types[m_type] = failure_types.get(m_type, 0) + 1

    # Sorting failed cases to find the 3 worst cases
    # Worst case = lowest judge score, then highest latency
    worst_cases = sorted(failed_cases, key=lambda x: (x["judge"]["final_score"], -x["latency"]))[:3]

    # Generate markdown content
    md = []
    md.append("# Báo cáo Phân tích Thất bại (Failure Analysis Report)")
    md.append("")
    md.append("## 1. Tổng quan Benchmark")
    md.append(f"- **Tổng số cases:** {total_cases}")
    md.append(f"- **Tỉ lệ Pass/Fail:** {num_pass} Pass / {num_fail} Fail (Tỉ lệ Pass: {num_pass/total_cases:.1%})")
    md.append("- **Điểm Ragas trung bình:**")
    md.append(f"    - Faithfulness: {avg_faithfulness:.2f}")
    md.append(f"    - Relevancy: {avg_relevancy:.2f}")
    md.append(f"- **Điểm LLM-Judge trung bình:** {avg_judge_score:.2f} / 5.0")
    md.append("")
    md.append("## 2. Phân nhóm lỗi (Failure Clustering)")
    md.append("| Nhóm lỗi | Số lượng | Nguyên nhân dự kiến |")
    md.append("|----------|----------|---------------------|")

    # Map metadata type to friendly names and descriptions
    friendly_causes = {
        "prompt-injection": "Agent dễ bị tấn công Prompt Injection do thiếu bộ lọc và system prompt lỏng lẻo",
        "out-of-context": "Retriever lấy nhầm tài liệu hoặc Agent bịa câu trả lời khi thiếu thông tin",
        "ambiguous-question": "Agent trả lời phỏng đoán thay vì làm rõ câu hỏi mơ hồ của khách hàng",
        "multi-turn-correction": "Hệ thống không lưu trữ lịch sử hội thoại nên không hiểu ngữ cảnh sửa đổi ở lượt chat sau",
        "latency-stress": "Input chứa nhiều từ nhiễu làm chậm tiến trình xử lý hoặc pha loãng context",
        "conflicting-information": "BM25 lấy nhầm tài liệu cũ và Generator không thể so sánh mâu thuẫn để chọn tài liệu mới hơn",
        "cost-efficiency": "Agent sử dụng mô hình hoặc quy trình đắt đỏ cho các câu hỏi FAQ đơn giản",
        "fact-check": "Truy xuất sai thông tin chi tiết hoặc lỗi tổng hợp tài liệu",
        "unknown": "Lỗi khác"
    }

    for f_type, count in failure_types.items():
        cause = friendly_causes.get(f_type, "Lỗi phân tích hoặc xử lý tài liệu")
        md.append(f"| {f_type.replace('-', ' ').title()} | {count} | {cause} |")
    
    if not failure_types:
        md.append("| Không có lỗi nào | 0 | Tất cả các case đều đạt điểm Judge >= 3.0 |")

    md.append("")
    md.append("## 3. Phân tích 5 Whys (Chọn 3 case tệ nhất)")
    md.append("")

    for i, case in enumerate(worst_cases):
        q = case["test_case"]
        ans = case["agent_response"]
        score = case["judge"]["final_score"]
        c_type = case.get("metadata", {}).get("type", "unknown")

        md.append(f"### Case #{i+1}: {q[:60]}...")
        md.append(f"- **ID:** {case.get('id', 'N/A')}")
        md.append(f"- **Loại lỗi:** {c_type}")
        md.append(f"- **Điểm LLM-Judge:** {score:.1f}/5.0")
        md.append(f"- **Câu trả lời thực tế của Agent:** `{ans}`")
        md.append("")
        md.append("#### Phân tích 5 Whys:")
        
        # Customize 5 whys based on type of error
        if c_type == "prompt-injection":
            md.append("1. **Symptom:** Agent bị lừa làm theo chỉ dẫn phá hoại hoặc tiết lộ thông tin.")
            md.append("2. **Why 1:** Agent không có bộ lọc phát hiện Prompt Injection trước khi xử lý.")
            md.append("3. **Why 2:** System Prompt của Agent không có quy tắc nghiêm ngặt ngăn chặn ghi đè chỉ thị.")
            md.append("4. **Why 3:** Generator tin tưởng hoàn toàn vào bất kỳ nội dung nào trong câu hỏi người dùng.")
            md.append("5. **Why 4:** Chưa có lớp phân lớp bảo mật (Guardrails) ở cổng vào.")
            md.append("6. **Root Cause:** Thiếu thiết kế bảo mật chống Prompt Injection trong System Prompt & Pipeline.")
        elif c_type == "out-of-context":
            md.append("1. **Symptom:** Agent trả lời sai hoặc bịa đặt khi câu hỏi ngoài phạm vi tài liệu.")
            md.append("2. **Why 1:** Retriever trả về điểm số BM25 thấp nhưng vẫn chuyển sang Generator.")
            md.append("3. **Why 2:** Ngưỡng lọc điểm (Confidence Score Threshold) trong Retriever chưa tối ưu.")
            md.append("4. **Why 3:** Generator không biết cách từ chối một cách nhất quán khi context không chứa thông tin.")
            md.append("5. **Why 4:** Tài liệu ranh giới (doc_06) không được ưu tiên khi độ khớp từ khóa thấp.")
            md.append("6. **Root Cause:** Thiếu cơ chế lọc ngưỡng tự tin trong Retriever và fallback chuyên biệt trong Generator.")
        elif c_type == "multi-turn-correction":
            md.append("1. **Symptom:** Agent không giải quyết được yêu cầu chỉnh sửa ở lượt chat thứ hai.")
            md.append("2. **Why 1:** Agent chỉ xử lý câu hỏi hiện tại độc lập (Stateless).")
            md.append("3. **Why 2:** Không có bộ nhớ đệm (Memory Buffer) để lưu lịch sử hội thoại trước đó.")
            md.append("4. **Why 3:** Hệ thống RAG được thiết kế tối giản, bỏ qua quản lý ngữ cảnh lượt chat (Session management).")
            md.append("5. **Why 4:** Thiếu module Query Rewriting để hợp nhất các lượt chat thành một câu truy vấn đầy đủ.")
            md.append("6. **Root Cause:** Thiết kế RAG pipeline dạng Stateless không hỗ trợ lưu giữ ngữ cảnh hội thoại.")
        elif c_type == "conflicting-information":
            md.append("1. **Symptom:** Agent đưa ra câu trả lời dựa trên tài liệu đã lỗi thời.")
            md.append("2. **Why 1:** Retriever trả về cả tài liệu cũ và mới có cùng từ khóa.")
            md.append("3. **Why 2:** Generator chọn ngẫu nhiên hoặc chọn câu đầu tiên tìm thấy mà không so sánh tính cập nhật.")
            md.append("4. **Why 3:** Thiếu siêu dữ liệu (Metadata) về thời gian hiệu lực của tài liệu để Reranker sắp xếp.")
            md.append("5. **Why 4:** Logic rút trích câu trả lời chỉ dựa vào mật độ trùng khớp từ khóa đơn giản.")
            md.append("6. **Root Cause:** Thiếu cơ chế Reranking theo tính cập nhật và thiếu khả năng suy luận logic mâu thuẫn của Generator.")
        else:
            md.append("1. **Symptom:** Agent phản hồi không khớp với mong đợi (Ground Truth).")
            md.append("2. **Why 1:** Retriever truy xuất thiếu thông tin từ tài liệu chính xác.")
            md.append("3. **Why 2:** Cơ chế so khớp từ khóa của BM25 bị nhiễu do câu hỏi dài hoặc dùng từ đồng nghĩa.")
            md.append("4. **Why 3:** Không có Reranker để tinh chỉnh độ liên quan của các chunk.")
            md.append("5. **Why 4:** Generator chọn nhầm câu văn không chứa câu trả lời trực tiếp.")
            md.append("6. **Root Cause:** Giới hạn của bộ tìm kiếm từ khóa thuần túy BM25 không hiểu ngữ nghĩa của câu hỏi.")
        md.append("")

    if not worst_cases:
        md.append("### Không có case thất bại nào cần phân tích.")
        md.append("")

    md.append("## 4. Kế hoạch cải tiến (Action Plan)")
    md.append("- [ ] **Tích hợp Guardrails**: Thêm bộ lọc đầu vào để chặn các câu hỏi Prompt Injection.")
    md.append("- [ ] **Cải tiến Retriever**: Áp dụng Hybrid Search (BM25 + Vector Embeddings) kết hợp Cohere Reranker.")
    md.append("- [ ] **Quản lý hội thoại**: Thêm cơ chế Conversation Memory và Query Rewriter để xử lý các lượt chat sửa lỗi.")
    md.append("- [ ] **Bộ lọc thời gian**: Thêm siêu dữ liệu thời gian cho tài liệu để giải quyết mâu thuẫn thông tin cũ/mới.")
    md.append("- [ ] **Tối ưu Prompt & Fallback**: Cập nhật Prompt Generator để từ chối khéo léo khi điểm tin cậy tìm kiếm thấp.")
    md.append("")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md))

    print(f"✅ Đã phân tích xong và cập nhật báo cáo thất bại tại {output_path}")

if __name__ == "__main__":
    run_analysis()
