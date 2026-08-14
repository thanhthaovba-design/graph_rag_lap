import os
import json
import pandas as pd
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
import sys
import time

# Đảm bảo output terminal là UTF-8
sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

class Entity(BaseModel):
    entity: str
    confidence: float
    evidence: str

class ExtractedData(BaseModel):
    co_quan: list[Entity]
    nguoi_ky: list[Entity]
    doi_tuong_ap_dung: list[Entity]
    linh_vuc: list[Entity]

def process_with_gemini(client, text_content):
    prompt = f"""
Trích xuất các thông tin sau từ văn bản pháp luật dưới đây.
Trả về định dạng JSON phù hợp với schema.
- co_quan: Cơ quan ban hành (Ví dụ: Quốc hội, Chính phủ...)
- nguoi_ky: Người ký / người có thẩm quyền ban hành
- doi_tuong_ap_dung: Đối tượng chịu sự điều chỉnh (Ví dụ: Ngân hàng thương mại, Tổ chức tín dụng...)
- linh_vuc: Lĩnh vực pháp lý (Ví dụ: Tín dụng, Kiểm toán, Bảo hiểm, Quản lý ngoại hối...)

QUAN TRỌNG:
- Nếu không có bằng chứng rõ ràng, KHÔNG tạo entity (trả về mảng rỗng).
- Mức độ tin cậy (confidence) từ 0.0 đến 1.0.
- Evidence là câu/đoạn văn bản trích dẫn nguyên văn chứa thông tin đó.

Văn bản:
{text_content[:4000]}
    """
    try:
        response = client.models.generate_content(
            model='gemini-3.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ExtractedData,
                temperature=0.0
            )
        )
        return json.loads(response.text)
    except Exception as e:
        return {"error": str(e)}

def main():
    print("=== BƯỚC 3: ENTITY EXTRACTION & METADATA ENRICHMENT ===")
    
    if not API_KEY:
        print("[FAIL] GEMINI_API_KEY is missing in .env")
        return
        
    client = genai.Client(api_key=API_KEY)
    
    in_path = os.path.join("ner_kb", "cleaned_documents.csv")
    if not os.path.exists(in_path):
        print(f"[FAIL] Missing {in_path}")
        return
        
    df = pd.read_csv(in_path)
    # Lấy thông tin gốc để so sánh
    df_original = df.copy()
    
    entities = []
    success_count = 0
    fail_count = 0
    errors = []
    enriched_fields_count = 0
    
    print(f"Đang xử lý {len(df)} documents bằng Gemini. Quá trình này có thể mất một ít thời gian...")
    
    for idx, row in df.iterrows():
        doc_id = row['id']
        text = str(row['content_clean'])
        
        res = process_with_gemini(client, text)
        
        if "error" in res:
            fail_count += 1
            errors.append(f"Doc {doc_id}: {res['error']}")
            continue
            
        has_parsed_any = False
        mapping = {
            'co_quan': 'CoQuan',
            'nguoi_ky': 'NguoiKy',
            'doi_tuong_ap_dung': 'DoiTuongApDung',
            'linh_vuc': 'LinhVuc'
        }
        
        for json_key, entity_type in mapping.items():
            items = res.get(json_key, [])
            for item in items:
                if isinstance(item, dict) and item.get('entity') and item.get('evidence'):
                    entities.append({
                        'source_doc_id': doc_id,
                        'entity': item['entity'],
                        'entity_type': entity_type,
                        'source': 'content_clean',
                        'method': 'gemini',
                        'confidence': item.get('confidence', 0.8),
                        'evidence': item['evidence']
                    })
                    has_parsed_any = True
        
        if has_parsed_any:
            success_count += 1
        else:
            fail_count += 1
            errors.append(f"Doc {doc_id}: Không trích xuất được entity nào hoặc response rỗng")
            
        # Metadata Enrichment: Ưu tiên metadata gốc, chỉ bổ sung nếu thiếu hoặc "Chưa phân loại"
        co_quan_goc = str(row.get('co_quan_ban_hanh', ''))
        if co_quan_goc == "" or co_quan_goc == "Chưa phân loại" or co_quan_goc == "nan":
            co_quans = [e.get('entity') for e in res.get('co_quan', []) if isinstance(e, dict) and e.get('entity')]
            if co_quans:
                df.at[idx, 'co_quan_ban_hanh'] = co_quans[0]
                enriched_fields_count += 1
                
        linh_vuc_goc = str(row.get('linh_vuc', ''))
        if linh_vuc_goc == "" or linh_vuc_goc == "Chưa phân loại" or linh_vuc_goc == "nan":
            linh_vucs = [e.get('entity') for e in res.get('linh_vuc', []) if isinstance(e, dict) and e.get('entity')]
            if linh_vucs:
                df.at[idx, 'linh_vuc'] = ", ".join(linh_vucs)
                enriched_fields_count += 1
                
        nguoi_ky_goc = str(row.get('nguoi_ky', ''))
        if nguoi_ky_goc == "" or nguoi_ky_goc == "Chưa phân loại" or nguoi_ky_goc == "nan":
            nguoi_kys = [e.get('entity') for e in res.get('nguoi_ky', []) if isinstance(e, dict) and e.get('entity')]
            if nguoi_kys:
                df.at[idx, 'nguoi_ky'] = nguoi_kys[0]
                enriched_fields_count += 1
                
        # Tránh lỗi Rate Limit 429 (Giới hạn 15 RPM free tier)
        time.sleep(4.5)

    df_entities = pd.DataFrame(entities)
    out_entities = os.path.join("ner_kb", "extracted_entities_raw.csv")
    df_entities.to_csv(out_entities, index=False, encoding='utf-8')
    
    out_metadata = os.path.join("ner_kb", "enriched_metadata.csv")
    df.to_csv(out_metadata, index=False, encoding='utf-8')
    
    print("\n--- KẾT QUẢ BƯỚC 3 ---")
    print(f"Số document thành công: {success_count}")
    print(f"Số document thất bại: {fail_count}")
    
    if len(df_entities) > 0:
        print("\nSố entity theo loại:")
        print(df_entities['entity_type'].value_counts().to_string())
        
    print(f"\nSố giá trị metadata được bổ sung: {enriched_fields_count}")
    
    print("\n5 Ví dụ metadata gốc so với metadata làm giàu:")
    sample_count = 0
    for idx in range(len(df)):
        orig_lv = str(df_original.at[idx, 'linh_vuc'])
        new_lv = str(df.at[idx, 'linh_vuc'])
        if orig_lv != new_lv or str(df_original.at[idx, 'co_quan_ban_hanh']) != str(df.at[idx, 'co_quan_ban_hanh']):
            print(f"- Doc ID {df.at[idx, 'id']}:")
            print(f"  + Lĩnh vực GỐC: {orig_lv} -> Lĩnh vực LÀM GIÀU: {new_lv}")
            print(f"  + Cơ quan GỐC: {df_original.at[idx, 'co_quan_ban_hanh']} -> Cơ quan LÀM GIÀU: {df.at[idx, 'co_quan_ban_hanh']}")
            sample_count += 1
        if sample_count >= 5:
            break
    
    if errors:
        print("\nDanh sách lỗi (hiển thị tối đa 5):")
        for err in errors[:5]:
            print(f"- {err}")
            
    print(f"\n[PASS] Đã lưu {len(df_entities)} entity vào {out_entities}")
    print(f"[PASS] Đã lưu metadata vào {out_metadata}")

if __name__ == "__main__":
    main()
