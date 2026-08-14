import pandas as pd
import os
import sys

# Ensure UTF-8 output in Windows terminal
sys.stdout.reconfigure(encoding='utf-8')

def normalize_entity(name):
    if not isinstance(name, str):
        return ""
    # Chuẩn hóa whitespace
    name = " ".join(name.split()).strip()
    return name

def apply_alias(name):
    # Mapping các alias phổ biến và chắc chắn
    alias_map = {
        "nhnn": "Ngân hàng Nhà nước Việt Nam",
        "ngân hàng nhà nước": "Ngân hàng Nhà nước Việt Nam",
        "chính phủ": "Chính phủ",
        "quốc hội": "Quốc hội",
        "bộ tài chính": "Bộ Tài chính",
        "btc": "Bộ Tài chính",
        "nhnn việt nam": "Ngân hàng Nhà nước Việt Nam"
    }
    lower_name = name.lower()
    if lower_name in alias_map:
        return alias_map[lower_name]
    return name

def main():
    print("=== BƯỚC 4: CHUẨN HÓA ENTITY ===")
    
    in_entities = os.path.join("ner_kb", "extracted_entities_raw.csv")
    in_meta = os.path.join("ner_kb", "enriched_metadata.csv")
    
    if not os.path.exists(in_entities):
        print(f"[FAIL] Missing {in_entities}")
        return
        
    df_raw = pd.read_csv(in_entities)
    print(f"Số entity trước khi normalize: {len(df_raw)}")
    
    if len(df_raw) == 0:
        print("[FAIL] File entity rỗng, vui lòng kiểm tra lại bước 3.")
        return
        
    # Chuẩn hóa tên (whitespace, lowercase cho comparison, etc.)
    df_raw['original_name'] = df_raw['entity'].apply(normalize_entity)
    df_raw['canonical_name'] = df_raw['original_name'].apply(apply_alias)
    
    # Track alias merges
    merged_alias = df_raw[df_raw['original_name'] != df_raw['canonical_name']]
    
    # Drop duplicates dựa trên canonical_name, entity_type và source_doc_id
    # (Để nếu trong cùng 1 doc có nhiều lần nhắc đến thì gom lại làm 1)
    # Tuy nhiên Entities có thể là master list, 
    # nên chúng ta sẽ tạo id duy nhất cho entity. 
    # Ở đây ta sẽ giữ lại 1 dòng đại diện cho mỗi cặp (canonical_name, entity_type)
    
    # Khởi tạo master entity list
    df_master = df_raw.sort_values('confidence', ascending=False).drop_duplicates(
        subset=['canonical_name', 'entity_type'], keep='first'
    )
    
    # Tạo entity_id
    df_master = df_master.reset_index(drop=True)
    df_master['entity_id'] = ["E" + str(i).zfill(4) for i in range(1, len(df_master) + 1)]
    
    print(f"Số entity sau khi normalize và loại duplicate: {len(df_master)}")
    
    if len(merged_alias) > 0:
        print("\nCác alias đã merge:")
        alias_summary = merged_alias[['original_name', 'canonical_name']].drop_duplicates()
        for _, row in alias_summary.iterrows():
            print(f"- {row['original_name']} -> {row['canonical_name']}")
    else:
        print("\nKhông có alias nào được merge.")
        
    out_path = os.path.join("ner_kb", "entities.csv")
    # Sắp xếp các cột cho dễ nhìn
    cols = ['entity_id', 'entity_type', 'canonical_name', 'original_name', 'source_doc_id', 'method', 'confidence', 'evidence']
    # Filter columns that exist
    cols = [c for c in cols if c in df_master.columns]
    
    df_master[cols].to_csv(out_path, index=False, encoding='utf-8')
    
    print("\n10 Entity mẫu:")
    print(df_master[['entity_id', 'entity_type', 'canonical_name']].head(10).to_string())
    
    print(f"\n[PASS] Đã lưu entity chính thức vào {out_path}")

if __name__ == "__main__":
    main()
