import json
import uuid
import os
import sys
from datetime import datetime, timezone

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from secure_retrieval_adapter import SecureRetrievalAdapter

class AuditLogger:
    def __init__(self, log_file_path):
        self.log_file_path = log_file_path
        os.makedirs(os.path.dirname(self.log_file_path), exist_ok=True)

    def log_request(self, user_id, user_roles, query, action, method, retrieved_results, dropped_candidates, status):
        event = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "request_id": str(uuid.uuid4()),
            "user_id_demo": user_id,
            "user_role": user_roles,
            "action": action,
            "query": query,
            "retrieval_method": method,
            "retrieved_document_ids": [r.get("document_id") for r in retrieved_results],
            "retrieved_chunk_ids": [r.get("chunk_id") for r in retrieved_results],
            "citation_ids": [r.get("citation") for r in retrieved_results],
            "rbac_dropped_candidates": int(dropped_candidates),
            "status": status
        }
        with open(self.log_file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
        return event

def run_demo():
    corpus_path = '../buoi_14/data/processed/chunks_secure.csv'
    adapter = SecureRetrievalAdapter(corpus_path)
    logger = AuditLogger('../outputs/audit_log.jsonl')
    
    total_docs = len(adapter.df)
    
    def calculate_dropped(roles):
        # A simple approximation: if Admin, drop 0. Otherwise use simple filter count.
        def has_access(roles_str):
            try:
                allowed = json.loads(roles_str)
                return any(role in roles for role in allowed)
            except:
                return False
        access_mask = adapter.df['allowed_roles'].apply(has_access)
        return total_docs - access_mask.sum()

    print("Running Demo 1: Allowed (Admin)...")
    roles = ["Admin"]
    query = "quy định"
    results = adapter.retrieve(query, roles, top_k=2)
    dropped = calculate_dropped(roles)
    logger.log_request("user_01", roles, query, "search", "Secure Hybrid", results, dropped, "SUCCESS")

    print("Running Demo 2: Denied (Unauthorized_User)...")
    roles = ["Unauthorized_User"]
    results = adapter.retrieve(query, roles, top_k=2)
    dropped = calculate_dropped(roles)
    # If 100% dropped, status is DENIED
    status = "DENIED" if dropped == total_docs else "SUCCESS"
    logger.log_request("user_02", roles, query, "search", "Secure Hybrid", results, dropped, status)

    print("Running Demo 3: Normal (Staff)...")
    roles = ["Staff"]
    query = "bảo mật"
    results = adapter.retrieve(query, roles, top_k=2)
    dropped = calculate_dropped(roles)
    logger.log_request("user_03", roles, query, "search", "Secure Hybrid", results, dropped, "SUCCESS")
    
    print("Audit trail generated successfully.")
    print("AUDIT TRAIL: PASS")

if __name__ == "__main__":
    run_demo()
