import pandas as pd
import json
import os
import sys

# Ensure UTF-8 output for Windows console
sys.stdout.reconfigure(encoding='utf-8')

def assign_roles_to_row(row):
    """
    Assign roles based on document_id or text keywords.
    """
    doc_id = str(row.get('document_id', '')).lower()
    text = str(row.get('text', '')).lower()
    
    combined = doc_id + " " + text
    
    # HR Keywords
    hr_keywords = ["nhân sự", "lương thưởng", "tuyển dụng", "bổ nhiệm", "hr"]
    if any(kw in combined for kw in hr_keywords):
        return ["Admin", "HR"]
        
    # Risk/Credit Keywords
    risk_keywords = ["tín dụng", "rủi ro", "hạn mức", "phê duyệt duyệt vay", "phê duyệt vay"]
    if any(kw in combined for kw in risk_keywords):
        return ["Admin", "Risk_Manager", "Staff"]
        
    # Others
    return ["Admin", "HR", "Risk_Manager", "Staff", "Guest"]

def main():
    input_path = "c:/graph_rag_labs/buoi_14/data/processed/chunks_normalized.csv"
    output_path = "c:/graph_rag_labs/buoi_14/data/processed/chunks_secure.csv"
    
    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found.")
        return
        
    print(f"Reading {input_path}...")
    df = pd.read_csv(input_path)
    df = df.fillna("")
    
    print("Assigning security tags...")
    df['allowed_roles'] = df.apply(lambda row: json.dumps(assign_roles_to_row(row)), axis=1)
    
    print(f"Saving to {output_path}...")
    df.to_csv(output_path, index=False)
    
    # Verification
    print("\n--- SECURITY TAGGING VERIFICATION ---")
    
    # Check for empty roles
    empty_roles = df[df['allowed_roles'].apply(lambda x: len(json.loads(x)) == 0)]
    if len(empty_roles) == 0:
        print("[OK] All chunks have at least one assigned role.")
    else:
        print(f"[ERROR] Found {len(empty_roles)} chunks with NO roles!")
        
    # Stats
    df['role_group'] = df['allowed_roles']
    stats = df['role_group'].value_counts()
    print("\nRole Distribution:")
    for role, count in stats.items():
        print(f"- {role}: {count} chunks")
        
    # Print 3 sample rows representing different access levels
    print("\n--- SAMPLE ROWS (3 Access Levels) ---")
    sample_hr = df[df['allowed_roles'].str.contains('HR', na=False) & ~df['allowed_roles'].str.contains('Guest', na=False)]
    if not sample_hr.empty:
        print("\n1. HR/Admin Level Sample:")
        row = sample_hr.iloc[0]
        print(f"Doc ID: {row['document_id']} | Roles: {row['allowed_roles']}")
        print(f"Text Snippet: {row['text'][:100]}...")
        
    sample_risk = df[df['allowed_roles'].str.contains('Risk_Manager', na=False) & ~df['allowed_roles'].str.contains('Guest', na=False) & ~df['allowed_roles'].str.contains('HR', na=False)]
    if not sample_risk.empty:
        print("\n2. Risk/Staff Level Sample:")
        row = sample_risk.iloc[0]
        print(f"Doc ID: {row['document_id']} | Roles: {row['allowed_roles']}")
        print(f"Text Snippet: {row['text'][:100]}...")
        
    sample_guest = df[df['allowed_roles'].str.contains('Guest', na=False)]
    if not sample_guest.empty:
        print("\n3. Public/Guest Level Sample:")
        row = sample_guest.iloc[0]
        print(f"Doc ID: {row['document_id']} | Roles: {row['allowed_roles']}")
        print(f"Text Snippet: {row['text'][:100]}...")

if __name__ == "__main__":
    main()
