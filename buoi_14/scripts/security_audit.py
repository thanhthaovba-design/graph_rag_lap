import sys
import os
import json

# Ensure UTF-8 output for Windows console
sys.stdout.reconfigure(encoding='utf-8')

sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))
from secure_retriever import SecureBM25Retriever, SecureDenseRetriever, SecureGraphRetriever, SecureHybridRetriever

def ensure_list(roles):
    if isinstance(roles, str):
        try:
            return json.loads(roles)
        except:
            return [roles]
    return roles

def run_audit():
    corpus_path = "c:/graph_rag_labs/buoi_14/data/processed/chunks_secure.csv"
    if not os.path.exists(corpus_path):
        print("Error: Secure corpus not found.")
        sys.exit(1)
        
    print("Initializing Secure Retrievers for Audit...")
    bm25 = SecureBM25Retriever(corpus_path)
    dense = SecureDenseRetriever(corpus_path)
    graph = SecureGraphRetriever()
    hybrid = SecureHybridRetriever(bm25, dense, graph)
    
    test_cases = [
        {
            "query": "Quy trình tuyển dụng và bổ nhiệm nhân sự cấp cao",
            "unauthorized_roles": ["Guest"],
            "authorized_roles": ["HR"],
            "sensitive_tag": "HR"
        },
        {
            "query": "Quy định về lương thưởng và phụ cấp",
            "unauthorized_roles": ["Staff"],
            "authorized_roles": ["Admin"],
            "sensitive_tag": "HR"
        },
        {
            "query": "Quy trình phê duyệt duyệt vay và hạn mức tín dụng",
            "unauthorized_roles": ["Guest"],
            "authorized_roles": ["Risk_Manager"],
            "sensitive_tag": "Risk_Manager"
        },
        {
            "query": "Đánh giá rủi ro tín dụng khách hàng doanh nghiệp",
            "unauthorized_roles": ["HR"],
            "authorized_roles": ["Staff"],
            "sensitive_tag": "Risk_Manager"
        },
        {
            "query": "Hồ sơ nhân sự và đánh giá hiệu suất nhân viên",
            "unauthorized_roles": ["Risk_Manager"],
            "authorized_roles": ["Admin"],
            "sensitive_tag": "HR"
        }
    ]
    
    report_lines = []
    report_lines.append("# Security Audit Report")
    report_lines.append("\n**Mục tiêu**: Kiểm thử tính an toàn của hệ thống RAG RBAC.")
    report_lines.append(f"**Số lượng Test Case**: {len(test_cases)}\n")
    
    overall_pass = True
    
    for i, tc in enumerate(test_cases, 1):
        query = tc["query"]
        unauth = tc["unauthorized_roles"]
        auth = tc["authorized_roles"]
        tag = tc["sensitive_tag"]
        
        print(f"\n--- Running Test Case {i} ---")
        print(f"Query: {query}")
        
        report_lines.append(f"## Test Case {i}")
        report_lines.append(f"- **Query**: `{query}`")
        report_lines.append(f"- **Unauthorized Roles**: `{unauth}`")
        report_lines.append(f"- **Authorized Roles**: `{auth}`")
        
        # 1. Run Authorized
        auth_results = hybrid.retrieve(query, user_roles=auth, top_k=5, candidate_k=20)
        auth_docs = [r['document_id'] for r in auth_results]
        
        # Determine target document ID from the authorized results
        # We find the best matching document that actually has the sensitive tag
        target_doc = None
        for r in auth_results:
            roles = ensure_list(r['allowed_roles'])
            if tag in roles:
                target_doc = r['document_id']
                break
                
        if not target_doc:
            report_lines.append("- **Warning**: Cannot find a purely sensitive target doc for this query in top results.")
            target_doc = auth_docs[0] if auth_docs else "Unknown"
            
        report_lines.append(f"- **Target Sensitive Doc ID**: `{target_doc}`")
        
        # 2. Run Unauthorized
        unauth_results = hybrid.retrieve(query, user_roles=unauth, top_k=10, candidate_k=50)
        unauth_docs = [r['document_id'] for r in unauth_results]
        
        # Check leakage
        leakage = False
        leaked_chunks = []
        for r in unauth_results:
            roles = ensure_list(r['allowed_roles'])
            # Check if any role in unauth is in roles
            if not any(ur in roles for ur in unauth):
                leakage = True
                leaked_chunks.append(r['chunk_id'])
            # Check target doc leak
            if r['document_id'] == target_doc and tag not in roles:
                # If it's the same doc but not the sensitive chunk, that's fine.
                pass
            if r['document_id'] == target_doc and tag in roles and not any(ur in roles for ur in unauth):
                leakage = True
                
        if leakage:
            overall_pass = False
            print(f"[FAIL] Data Leakage detected for unauth roles {unauth}!")
            report_lines.append(f"- **Result**: FAILED ❌ (Data Leakage Detected! Chunks: {leaked_chunks})")
        else:
            print("[PASS] No leakage detected.")
            report_lines.append("- **Result**: PASSED ✅")
            report_lines.append("- **Evidence**: Unauthorized roles received 0 sensitive chunks.")
            
    report_lines.append("\n## Kết Luận")
    if overall_pass:
        report_lines.append("**Hệ thống ĐẠT CHỨNG NHẬN AN TOÀN DỮ LIỆU MỨC CƠ BẢN. ✅**")
    else:
        report_lines.append("**HỆ THỐNG KHÔNG AN TOÀN. PHÁT HIỆN RÒ RỈ DỮ LIỆU. ❌**")
        
    report_path = "c:/graph_rag_labs/buoi_14/outputs/security_audit_report.md"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
        
    print(f"\nAudit completed. Report saved to {report_path}")
    
    if not overall_pass:
        sys.exit(1)

if __name__ == "__main__":
    run_audit()
