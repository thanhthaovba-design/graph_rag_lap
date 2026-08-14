import pandas as pd
from bs4 import BeautifulSoup
import re
import os
import sys

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

def clean_html(html_text):
    if pd.isna(html_text):
        return ""
    soup = BeautifulSoup(str(html_text), 'html.parser')
    text = soup.get_text(separator=' ')
    # Chuẩn hóa whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def main():
    print("=== BƯỚC 1: KIỂM TRA DỮ LIỆU & LÀM SẠCH HTML ===")
    
    metadata_path = os.path.join("ner_kb", "metadata.csv")
    content_path = os.path.join("ner_kb", "content.csv")
    
    df_meta = pd.read_csv(metadata_path)
    df_content = pd.read_csv(content_path)
    
    print(f"Metadata: {df_meta.shape[0]} rows, {df_meta.shape[1]} cols")
    print(f"Content: {df_content.shape[0]} rows, {df_content.shape[1]} cols")
    
    dup_meta = df_meta['id'].duplicated().sum()
    dup_content = df_content['id'].duplicated().sum()
    print(f"Duplicate IDs - Metadata: {dup_meta}, Content: {dup_content}")
    
    meta_ids = set(df_meta['id'])
    content_ids = set(df_content['id'])
    mismatch_ids = meta_ids.symmetric_difference(content_ids)
    print(f"ID Mismatch Count: {len(mismatch_ids)}")
    
    df_merged = pd.merge(df_meta, df_content, on='id', how='inner')
    print(f"Merged Document Count: {len(df_merged)}")
    
    print("\nMissing values in metadata:")
    print(df_meta.isnull().sum())
    
    print("\nDetecting 'Chưa phân loại', NULL, empty string:")
    for col in df_meta.columns:
        if df_meta[col].dtype == object:
            chuaphanloai = (df_meta[col] == 'Chưa phân loại').sum()
            empty_str = (df_meta[col] == '').sum()
            print(f"- {col}: 'Chưa phân loại': {chuaphanloai}, Empty: {empty_str}")
            
    print("\nCleaning HTML...")
    df_merged['content_clean'] = df_merged['content_html'].apply(clean_html)
    
    out_path = os.path.join("ner_kb", "cleaned_documents.csv")
    df_merged.to_csv(out_path, index=False, encoding='utf-8')
    print(f"\nSaved cleaned documents to {out_path}")
    
    print("\nSample 1 (HTML vs Clean):")
    if len(df_merged) > 0:
        sample1 = df_merged.iloc[0]
        print("HTML:", str(sample1['content_html'])[:200], "...")
        print("CLEAN:", str(sample1['content_clean'])[:200], "...")
    
    print("\nSample 2 (HTML vs Clean):")
    if len(df_merged) > 1:
        sample2 = df_merged.iloc[1]
        print("HTML:", str(sample2['content_html'])[:200], "...")
        print("CLEAN:", str(sample2['content_clean'])[:200], "...")
    
if __name__ == "__main__":
    main()
