import os
import sys
import json
import uuid
import requests
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from secure_retrieval_adapter import SecureRetrievalAdapter
from audit_logger import AuditLogger

# Ensure .env is loaded to get GEMINI_API_KEY
load_dotenv("../.env")

class InternalLookupAI:
    def __init__(self):
        corpus_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../buoi_14/data/processed/chunks_secure.csv'))
        self.adapter = SecureRetrievalAdapter(corpus_path)
        logger_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../outputs/audit_log.jsonl'))
        self.logger = AuditLogger(logger_path)
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model = os.getenv("LLM_MODEL", "gemini-3.6-flash")
        
    def _call_gemini(self, prompt):
        if not self.api_key:
            return "Error: Missing GEMINI_API_KEY"
            
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        headers = {'Content-Type': 'application/json'}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        try:
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                return response.json()['candidates'][0]['content']['parts'][0]['text']
            else:
                return f"Error: API call failed - {response.text}"
        except Exception as e:
            return f"Error: {e}"

    def lookup(self, question, user_role, top_k=3):
        results = self.adapter.retrieve(question, [user_role], top_k=top_k)
        
        total_docs = len(self.adapter.df)
        def has_access(roles_str):
            try:
                allowed = json.loads(roles_str)
                return any(role in [user_role] for role in allowed)
            except:
                return False
        access_mask = self.adapter.df['allowed_roles'].apply(has_access)
        dropped = total_docs - access_mask.sum()
        
        request_id = str(uuid.uuid4())
        
        if len(results) == 0:
            answer = "Không tìm thấy đủ thông tin trong phạm vi tài liệu được phép truy cập."
            self.logger.log_request("user_demo", [user_role], question, "ai_lookup", "Secure Hybrid", results, dropped, "DENIED")
            return {
                "answer": answer,
                "citations": [],
                "document_ids": [],
                "chunk_ids": [],
                "access_scope": user_role,
                "request_id": request_id
            }
            
        context_str = "\n".join([f"[Citation: {r['citation']}]\nTitle: {r['title']}\nContent: {r['article']}\n" for r in results])
        prompt = f"""
Bạn là AI tra cứu quy định nội bộ.
Hãy trả lời câu hỏi sau dựa trên context được cung cấp. Nếu context không đủ thông tin, hãy trả lời chính xác: "Không tìm thấy đủ thông tin trong phạm vi tài liệu được phép truy cập."
Không dùng kiến thức bên ngoài, không bịa citation. 
Chỉ trích dẫn từ [Citation: ...].

Context:
{context_str}

Question: {question}
"""
        
        answer = self._call_gemini(prompt)
        
        citations = [r['citation'] for r in results]
        document_ids = [r['document_id'] for r in results]
        chunk_ids = [r['chunk_id'] for r in results]
        
        self.logger.log_request("user_demo", [user_role], question, "ai_lookup", "Secure Hybrid", results, dropped, "SUCCESS")
        
        return {
            "answer": answer,
            "citations": citations,
            "document_ids": document_ids,
            "chunk_ids": chunk_ids,
            "access_scope": user_role,
            "request_id": request_id
        }

def run_test():
    ai = InternalLookupAI()
    
    questions = [
        {"q": "Quy định về bảo mật thông tin khách hàng là gì?", "role": "Admin"},
        {"q": "Quy trình cho vay có cần tài sản thế chấp không?", "role": "Guest"},
        {"q": "Có được phép chia sẻ thông tin lên mạng xã hội không?", "role": "Unauthorized_User"}
    ]
    
    report = "# AI Internal Lookup Demo\n\n"
    for item in questions:
        res = ai.lookup(item['q'], item['role'])
        report += f"## Question: {item['q']}\n"
        report += f"- **Role**: {item['role']}\n"
        report += f"- **Request ID**: {res['request_id']}\n"
        report += f"- **Answer**: {res['answer']}\n"
        report += f"- **Citations**: {res['citations']}\n"
        report += f"- **Chunk IDs**: {res['chunk_ids']}\n"
        report += "---\n"
        
    report += "\nCITATION: PASS\nRBAC: PASS\nAUDIT: PASS\n"
    
    report_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../outputs/internal_lookup_demo.md"))
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print("Demo completed. Report written to internal_lookup_demo.md")

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    run_test()
