import pandas as pd
import re
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

def extract_candidates(df):
    candidates = []
    
    # Add common triggers based on requirements
    triggers = ['Căn cứ', 'Sửa đổi, bổ sung', 'bãi bỏ', 'thay thế', 'Thông tư số', 'Nghị định số', 'Luật số']
    # Use re.IGNORECASE for flexible matching
    trigger_pattern = re.compile(r'(' + '|'.join(triggers) + r')', re.IGNORECASE)
    
    # Match patterns like: 32/2024/QH15, 73/2016/NĐ-CP, 22/2023/TT-NHNN
    doc_id_pattern = re.compile(r'(\d+/\d+/[A-Z0-9Đ-]+)', re.IGNORECASE)
    
    for _, row in df.iterrows():
        source_id = row['id']
        source_so_ky_hieu = str(row['so_ky_hieu'])
        text = str(row['content_clean'])
        
        for match in trigger_pattern.finditer(text):
            trigger = match.group(1)
            start_pos = match.start()
            
            # Extract 250 characters as evidence
            end_pos = min(len(text), start_pos + 250)
            evidence = text[start_pos:end_pos]
            
            # Find document numbers in this chunk
            for doc_match in doc_id_pattern.finditer(evidence):
                target_so_ky_hieu = doc_match.group(1).upper()
                
                # Loại self-reference
                if target_so_ky_hieu != source_so_ky_hieu.upper():
                    candidates.append({
                        'source_id': source_id,
                        'source_so_ky_hieu': source_so_ky_hieu,
                        'target_so_ky_hieu': target_so_ky_hieu,
                        'trigger': trigger.lower(),
                        'evidence': evidence.strip()
                    })
                    
    return pd.DataFrame(candidates)

def main():
    print("=== BƯỚC 2: RULE-BASED CANDIDATE EXTRACTION ===")
    
    in_path = os.path.join("ner_kb", "cleaned_documents.csv")
    if not os.path.exists(in_path):
        print(f"[FAIL] Missing input file: {in_path}")
        return
        
    df = pd.read_csv(in_path)
    
    candidates_df = extract_candidates(df)
    
    # Loại duplicate candidate (giữ unique theo source, target và trigger)
    candidates_df = candidates_df.drop_duplicates(subset=['source_id', 'target_so_ky_hieu', 'trigger'])
    
    out_path = os.path.join("ner_kb", "relation_candidates.csv")
    candidates_df.to_csv(out_path, index=False, encoding='utf-8')
    
    print(f"Tổng số candidate: {len(candidates_df)}")
    
    if len(candidates_df) > 0:
        print("\nSố candidate theo trigger:")
        print(candidates_df['trigger'].value_counts().to_string())
        
        print("\n10 Candidate mẫu:")
        samples = candidates_df[['source_so_ky_hieu', 'trigger', 'target_so_ky_hieu']].head(10)
        print(samples.to_string())
    
    print(f"\n[PASS] Đã lưu vào {out_path}")

if __name__ == "__main__":
    main()
