import os
import pandas as pd

def run_gap_checker():
    # Kiểm tra trạng thái dữ liệu từ báo cáo Prompt 6
    catalog_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../outputs/gap_input_catalog.md'))
    
    is_ready = False
    if os.path.exists(catalog_path):
        with open(catalog_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if "COMPLIANCE GAP DATA: READY" in content:
                is_ready = True
                
    report_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../outputs/compliance_gap_report.md'))
    csv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../outputs/compliance_gap_results.csv'))
    
    schema = [
        "gap_id", "external_document_id", "external_chunk_id", "external_requirement",
        "external_citation", "internal_document_id", "internal_chunk_id", "internal_evidence",
        "internal_citation", "classification", "reason", "confidence", "review_status", "request_id"
    ]
    
    if not is_ready:
        print("Data is insufficient for Compliance Gap Checker. Generating DATA GAP report.")
        # Tạo file CSV rỗng với đúng schema
        pd.DataFrame(columns=schema).to_csv(csv_path, index=False)
        
        report = """# AI Compliance Gap Checker Report

## Trạng thái: DATA GAP (THIẾU DỮ LIỆU)

Theo nguyên tắc an toàn, hệ thống từ chối chạy AI Compliance Gap Checker vì dữ liệu không đủ.
Kết quả từ Prompt 6 chỉ ra rằng: **DATA GAP: INTERNAL POLICY NOT FOUND** (Không tìm thấy văn bản quy định nội bộ thực tế nào trong tập dữ liệu).

Để tránh sinh ra ảo giác (hallucination) hay các kết luận giả mạo, hệ thống đã ngừng hoạt động cho Use Case này.
File `compliance_gap_results.csv` đã được tạo ra dưới dạng schema chuẩn, nhưng trống dữ liệu.

---

GAP CHECKER: FAIL
HUMAN REVIEW REQUIRED: YES
"""
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)
        return

if __name__ == "__main__":
    run_gap_checker()
