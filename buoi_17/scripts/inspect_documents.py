import os
import pandas as pd

def check_gap_data():
    corpus_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../buoi_14/data/processed/chunks_secure.csv'))
    df = pd.read_csv(corpus_path)
    
    # We only care about unique documents
    docs = df.drop_duplicates(subset=['document_id']).copy()
    
    total_docs = len(docs)
    
    catalog = f"# Gap Input Catalog\n\nTổng số document: {total_docs}\n\n"
    
    has_internal = False
    has_external = False
    
    # Analyze each doc
    for _, row in docs.iterrows():
        title = str(row.get('title', '')).lower()
        so_ky_hieu = str(row.get('so_ky_hieu', '')).lower()
        doc_type = str(row.get('document_type', '')).lower()
        
        # Check for internal vs external
        classification = "UNKNOWN"
        evidence = "Không đủ thông tin"
        
        # Simple heuristic for Vietnamese legal docs
        external_keywords = ['thông tư', 'nghị định', 'luật', 'nhnn', 'ngân hàng nhà nước', 'chính phủ']
        internal_keywords = ['agribank', 'quy định nội bộ', 'nội bộ', 'hđqt', 'tổng giám đốc']
        
        if any(kw in title or kw in so_ky_hieu or kw in doc_type for kw in external_keywords):
            classification = "EXTERNAL_REQUIREMENT"
            evidence = "Tên văn bản chứa từ khóa Thông tư/Nghị định/Luật/NHNN"
            has_external = True
        elif any(kw in title or kw in so_ky_hieu or kw in doc_type for kw in internal_keywords):
            classification = "INTERNAL_POLICY"
            evidence = "Tên/Ký hiệu văn bản chứa từ khóa Agribank/nội bộ"
            has_internal = True
        else:
            # If not explicitly external, let's look closer. If it's just 'Quy định' it might be internal, but we shouldn't hallucinate.
            # In buoi 14 dataset, there is agribank_internal_policies.csv which was merged.
            if 'agribank' in str(row.get('source_file', '')).lower() or 'internal' in str(row.get('source_file', '')).lower():
                classification = "INTERNAL_POLICY"
                evidence = "Tên file nguồn chứa từ khóa internal/agribank"
                has_internal = True
            elif 'thong_tu' in str(row.get('source_file', '')).lower() or 'nhnn' in str(row.get('source_file', '')).lower():
                classification = "EXTERNAL_REQUIREMENT"
                evidence = "Tên file nguồn chứa từ khóa thong_tu/nhnn"
                has_external = True
                
        catalog += f"### Document: {row.get('document_id', 'N/A')}\n"
        catalog += f"- **Title**: {row.get('title', 'N/A')}\n"
        catalog += f"- **Loại văn bản**: {row.get('document_type', 'N/A')}\n"
        catalog += f"- **Cơ quan ban hành**: N/A (Không có trong dữ liệu)\n"
        catalog += f"- **Classification**: {classification}\n"
        catalog += f"- **Evidence**: {evidence}\n\n"
        
    if has_internal and has_external:
        catalog += "\nCOMPLIANCE GAP DATA: READY\n"
    else:
        catalog += "\nCOMPLIANCE GAP DATA: INSUFFICIENT\n"
        if not has_internal:
            catalog += "DATA GAP: INTERNAL POLICY NOT FOUND\n"
        if not has_external:
            catalog += "DATA GAP: EXTERNAL REQUIREMENT NOT FOUND\n"
            
    output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../outputs/gap_input_catalog.md'))
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(catalog)
        
    print(f"Catalog saved to {output_path}")

if __name__ == "__main__":
    check_gap_data()
