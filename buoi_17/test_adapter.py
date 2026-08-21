import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from scripts.secure_retrieval_adapter import SecureRetrievalAdapter

def test_adapter():
    corpus_path = '../buoi_14/data/processed/chunks_secure.csv'
    adapter = SecureRetrievalAdapter(corpus_path)
    
    query = "quy định"
    
    print("Testing with Admin role...")
    admin_results = adapter.retrieve(query, ["Admin"], top_k=3)
    print(f"Admin retrieved {len(admin_results)} chunks.")
    if len(admin_results) > 0:
        first = admin_results[0]
        print(f" - Keys: {list(first.keys())}")
        print(f" - Rank: {first['rank']}")
        print(f" - Chunk ID: {first['chunk_id']}")
        print(f" - Title: {first['title']}")
        print(f" - Access Decision: {first['access_decision']}")
        
    print("\nTesting with Guest role...")
    guest_results = adapter.retrieve(query, ["Guest"], top_k=3)
    print(f"Guest retrieved {len(guest_results)} chunks.")
    
    print("\nTesting with Unknown Role...")
    unknown_results = adapter.retrieve(query, ["Unauthorized_User"], top_k=3)
    print(f"Unauthorized retrieved {len(unknown_results)} chunks.")

if __name__ == "__main__":
    test_adapter()
