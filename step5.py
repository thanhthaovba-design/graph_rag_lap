import pandas as pd
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

def main():
    print("=== BƯỚC 5: RELATIONSHIP EXTRACTION ===")
    
    # 1. Load Data
    docs = pd.read_csv(os.path.join("ner_kb", "cleaned_documents.csv"))
    candidates = pd.read_csv(os.path.join("ner_kb", "relation_candidates.csv"))
    entities = pd.read_csv(os.path.join("ner_kb", "entities.csv"))
    
    relations = []
    
    # 2. Document -> Document Relations from candidates
    # trigger: sửa đổi, bổ sung -> SUA_DOI_BO_SUNG
    # trigger: thay thế -> THAY_THE_BOI
    # trigger: căn cứ -> THAM_CHIEU
    # other triggers -> THAM_CHIEU (by default, if no specific keyword)
    
    for _, row in candidates.iterrows():
        source_id = row['source_so_ky_hieu'] # Using so_ky_hieu as node identifier for now
        target_id = row['target_so_ky_hieu']
        trigger = str(row['trigger']).lower()
        
        rel_type = "THAM_CHIEU"
        if "sửa đổi" in trigger or "bổ sung" in trigger:
            rel_type = "SUA_DOI_BO_SUNG"
        elif "thay thế" in trigger:
            rel_type = "THAY_THE_BOI"
            # Chiều THAY_THE_BOI: Document cũ -> Document mới.
            # Văn bản hiện tại (source) thay thế văn bản cũ (target).
            # Vậy target (cũ) -[THAY_THE_BOI]-> source (mới).
            source_id, target_id = target_id, source_id
            
        relations.append({
            'source': source_id,
            'target': target_id,
            'relationship_type': rel_type,
            'method': 'rule',
            'confidence': 1.0,
            'evidence': row['evidence']
        })
        
    # 3. Document -> Entity Relations from entities
    # CoQuan -> BAN_HANH_BOI
    # NguoiKy -> KY_BOI
    # DoiTuongApDung -> AP_DUNG_CHO
    # LinhVuc -> THUOC_LINH_VUC
    
    # Need mapping from source_doc_id to so_ky_hieu
    doc_id_map = dict(zip(docs['id'], docs['so_ky_hieu']))
    
    for _, row in entities.iterrows():
        doc_id = row['source_doc_id']
        source_skh = doc_id_map.get(doc_id)
        if not source_skh: continue
        
        target = row['canonical_name']
        e_type = row['entity_type']
        
        rel_type = ""
        if e_type == "CoQuan": rel_type = "BAN_HANH_BOI"
        elif e_type == "NguoiKy": rel_type = "KY_BOI"
        elif e_type == "DoiTuongApDung": rel_type = "AP_DUNG_CHO"
        elif e_type == "LinhVuc": rel_type = "THUOC_LINH_VUC"
        
        if rel_type:
            relations.append({
                'source': source_skh,
                'target': target,
                'relationship_type': rel_type,
                'method': 'gemini_extraction',
                'confidence': row['confidence'],
                'evidence': row['evidence']
            })
            
    df_rel = pd.DataFrame(relations)
    df_rel = df_rel.drop_duplicates(subset=['source', 'target', 'relationship_type'])
    
    out_path = os.path.join("ner_kb", "relationships_raw.csv")
    df_rel.to_csv(out_path, index=False, encoding='utf-8')
    
    print(f"Tổng số relation: {len(df_rel)}")
    if len(df_rel) > 0:
        print("\nSố relation theo type:")
        print(df_rel['relationship_type'].value_counts().to_string())
        
        print("\n10 Relation mẫu:")
        print(df_rel[['source', 'relationship_type', 'target']].head(10).to_string())
        
    print(f"\n[PASS] Đã lưu relationships vào {out_path}")

if __name__ == "__main__":
    main()
