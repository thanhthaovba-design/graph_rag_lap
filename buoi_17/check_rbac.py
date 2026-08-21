import os
import sys
import pandas as pd
import json

sys.path.append(os.path.abspath("../buoi_14"))
from src.secure_retriever import SecureRetriever, SecureDenseRetriever, SecureBM25Retriever

def check_rbac():
    df = pd.read_csv('../buoi_14/data/processed/chunks_secure.csv')
    
    roles_count = {}
    multiple_roles = 0
    restricted_rights = 0
    parse_errors = 0
    
    for idx, row in df.iterrows():
        roles_str = row['allowed_roles']
        try:
            roles = json.loads(roles_str) if isinstance(roles_str, str) else []
            if len(roles) > 1:
                multiple_roles += 1
            if len(roles) < 4:  # Assuming less than all roles means restricted
                restricted_rights += 1
                
            for role in roles:
                roles_count[role] = roles_count.get(role, 0) + 1
        except Exception as e:
            parse_errors += 1
            
    print("--- DATA ANALYSIS ---")
    print(f"Roles found: {list(roles_count.keys())}")
    for role, count in roles_count.items():
        print(f" - {role}: {count} chunks")
    print(f"Chunks with multiple roles: {multiple_roles}")
    print(f"Chunks with restricted rights: {restricted_rights}")
    print(f"Parse errors: {parse_errors}")

    print("\n--- RETRIEVER TEST ---")
    query = "quy định"
    
    # Init retriever
    print("Initializing SecureRetriever...")
    bm25 = SecureBM25Retriever('../buoi_14/data/processed/chunks_secure.csv')
    dense = SecureDenseRetriever('../buoi_14/data/processed/chunks_secure.csv')
    # Use Hybrid (alias SecureRetriever) without Graph since Graph requires DB
    hybrid = SecureRetriever(bm25, dense)
    
    roles_to_test = [["Admin"], ["HR"], ["Risk_Manager"], ["Staff"], ["Guest"], ["Unknown_Role"]]
    
    for test_role in roles_to_test:
        results = hybrid.retrieve(query, test_role, top_k=3)
        print(f"Role {test_role[0]}: retrieved {len(results)} chunks.")

if __name__ == '__main__':
    check_rbac()
