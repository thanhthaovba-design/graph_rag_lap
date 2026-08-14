import pandas as pd
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

def main():
    print("=== BƯỚC 6: VALIDATE RELATIONSHIPS ===")
    
    in_rel = os.path.join("ner_kb", "relationships_raw.csv")
    in_docs = os.path.join("ner_kb", "cleaned_documents.csv")
    in_entities = os.path.join("ner_kb", "entities.csv")
    
    df_rel = pd.read_csv(in_rel)
    df_docs = pd.read_csv(in_docs)
    df_entities = pd.read_csv(in_entities)
    
    valid_source_ids = set(df_docs['so_ky_hieu'])
    valid_entity_targets = set(df_entities['canonical_name'])
    
    valid_rel_types = {
        "THAM_CHIEU", "SUA_DOI_BO_SUNG", "THAY_THE_BOI",
        "BAN_HANH_BOI", "KY_BOI", "AP_DUNG_CHO", "THUOC_LINH_VUC"
    }
    
    doc_rel_types = {"THAM_CHIEU", "SUA_DOI_BO_SUNG", "THAY_THE_BOI"}
    
    valid_relations = []
    invalid_relations = []
    
    for idx, row in df_rel.iterrows():
        source = str(row['source'])
        target = str(row['target'])
        rel_type = str(row['relationship_type'])
        evidence = str(row['evidence'])
        
        reason = []
        
        if source not in valid_source_ids:
            reason.append("Source not in corpus")
            
        if rel_type not in valid_rel_types:
            reason.append("Invalid relationship type")
            
        if source == target:
            reason.append("Self-loop")
            
        if not evidence or evidence == 'nan':
            reason.append("Missing evidence")
            
        if rel_type in doc_rel_types:
            pass # target is another doc, might not be in corpus if closed-corpus is strict, but we allow external docs
        else:
            if target not in valid_entity_targets:
                reason.append("Entity target not in entities.csv")
                
        if reason:
            row_dict = row.to_dict()
            row_dict['fail_reason'] = " | ".join(reason)
            invalid_relations.append(row_dict)
        else:
            valid_relations.append(row.to_dict())
            
    df_valid = pd.DataFrame(valid_relations)
    df_invalid = pd.DataFrame(invalid_relations)
    
    # Drop duplicates one more time just in case
    if len(df_valid) > 0:
        df_valid = df_valid.drop_duplicates(subset=['source', 'target', 'relationship_type'])
        
    out_valid = os.path.join("ner_kb", "relationships.csv")
    out_invalid = os.path.join("ner_kb", "validation_report.csv")
    
    df_valid.to_csv(out_valid, index=False, encoding='utf-8')
    
    if len(df_invalid) > 0:
        df_invalid.to_csv(out_invalid, index=False, encoding='utf-8')
    else:
        # Create empty file
        pd.DataFrame(columns=df_rel.columns.tolist() + ['fail_reason']).to_csv(out_invalid, index=False)
        
    print(f"Tổng relation raw: {len(df_rel)}")
    print(f"Số PASS: {len(df_valid)}")
    print(f"Số FAIL: {len(df_invalid)}")
    
    if len(df_valid) > 0:
        print("\nSố theo relationship_type:")
        print(df_valid['relationship_type'].value_counts().to_string())
        
        print("\n10 Relation PASS mẫu:")
        print(df_valid[['source', 'relationship_type', 'target']].head(10).to_string())
        
    if len(df_invalid) > 0:
        print("\nNguyên nhân fail phổ biến:")
        print(df_invalid['fail_reason'].value_counts().to_string())
        
    print(f"\n[PASS] Lưu báo cáo vào {out_invalid}")
    print(f"[PASS] Lưu data hợp lệ vào {out_valid}")

if __name__ == "__main__":
    main()
