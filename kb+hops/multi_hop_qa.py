import sys
import os
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Load env variables for Gemini API key
load_dotenv(r"c:\Rag_thuchanh\RAG\rag_advanced\buoi_08\.env")
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("Warning: GEMINI_API_KEY not found in environment.")

genai.configure(api_key=api_key)
model_gen = genai.GenerativeModel('gemini-flash-latest')

# Neo4j settings
NEO4J_URI = "neo4j://127.0.0.1:7687"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "abcd1234"
DB_NAME = "neo4j"

print("Loading Sentence Transformer Model...")
embed_model = SentenceTransformer('thuannc/vi-distilled-msmarco-MiniLM-L12-cos-v5', device='cpu')

def create_vector_index(driver):
    with driver.session(database=DB_NAME) as session:
        result = session.run("SHOW VECTOR INDEXES")
        indexes = [record["name"] for record in result]
        if "chunk_embedding" not in indexes:
            print("Creating vector index 'chunk_embedding'...")
            session.run("""
                CREATE VECTOR INDEX chunk_embedding IF NOT EXISTS
                FOR (c:Chunk) ON (c.embedding)
                OPTIONS {indexConfig: {
                  `vector.dimensions`: 384,
                  `vector.similarity_function`: 'cosine'
                }}
            """)
            print("Waiting for index to be online...")
            session.run("CALL db.awaitIndexes(300)")
            print("Vector index created.")
        else:
            print("Vector index 'chunk_embedding' already exists.")

def get_context(driver, question, k=3, hops=0):
    q_emb = embed_model.encode(question).tolist()
    context_texts = []
    
    with driver.session(database=DB_NAME) as session:
        # Step 1: Vector search for direct chunks
        result = session.run("""
            CALL db.index.vector.queryNodes('chunk_embedding', $k, $q_emb) YIELD node AS c, score
            MATCH (c)-[:PART_OF]->(d:Document)
            RETURN c.text AS chunk_text, d.id AS doc_id, score
        """, k=k, q_emb=q_emb)
        
        doc_ids = set()
        for record in result:
            doc_id = record["doc_id"]
            if doc_id not in doc_ids:
                doc_ids.add(doc_id)
            context_texts.append(f"Tài liệu {doc_id} (Trực tiếp): {record['chunk_text']}")

        if hops > 0 and doc_ids:
            # Step 2: Multi-hop retrieval
            for doc_id in doc_ids:
                hop_result = session.run(f"""
                    MATCH p = (d:Document {{id: $doc_id}})-[*1..{hops}]-(related:Document)
                    WITH related, [rel in relationships(p) | type(rel)] AS rels, d.id AS source_id
                    MATCH (c:Chunk)-[:PART_OF]->(related)
                    RETURN related.id AS related_id, rels, c.text AS related_text, source_id
                    LIMIT 3
                """, doc_id=doc_id)
                
                for record in hop_result:
                    rel_str = " -> ".join(record["rels"])
                    context_texts.append(f"Tài liệu {record['related_id']} (Quan hệ: {rel_str} với {record['source_id']}): {record['related_text']}")
                    
    return "\n\n".join(context_texts)

def ask_gemini(question, context):
    prompt = f"""
Bạn là một trợ lý pháp lý AI chuyên nghiệp.
Dưới đây là một số thông tin trích xuất từ cơ sở dữ liệu luật pháp (bao gồm các đoạn văn bản trực tiếp và các tài liệu liên quan thông qua các mối quan hệ như THAY_THE, CAN_CU, HOP_NHAT, v.v.):

--- NGỮ CẢNH ---
{context}
--- HẾT NGỮ CẢNH ---

Dựa vào ngữ cảnh trên, hãy trả lời câu hỏi sau một cách chính xác. Nếu ngữ cảnh không cung cấp đủ thông tin, hãy nói rõ rằng bạn không có đủ thông tin chứ không tự suy đoán. 
Khi trả lời, hãy chỉ rõ mối quan hệ giữa các tài liệu nếu có và trích dẫn tài liệu tham chiếu (ví dụ: "Theo Tài liệu X...").

Câu hỏi: {question}
"""
    try:
        response = model_gen.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Lỗi khi gọi API: {str(e)}"

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    
    try:
        create_vector_index(driver)
    except Exception as e:
        print(f"Error creating index: {e}")
    
    questions = [
        "Nghị định 46/2023/NĐ-CP thay thế cho nghị định nào, và nghị định bị thay thế đó có nội dung gì nổi bật về kinh doanh bảo hiểm?",
        "Văn bản hợp nhất số 52/VBHN-NHNN được hợp nhất từ văn bản nào, và quy định về hồ sơ, thủ tục cấp giấy phép lần đầu của ngân hàng thương mại gồm những tài liệu gì?",
        "Thông tư số 01/2025/TT-NHNN quy định về cấp giấy phép quỹ tín dụng nhân dân được sửa đổi, bổ sung bởi văn bản nào, và những nội dung sửa đổi bổ sung chính là gì?",
        "Thông tư số 41/2016/TT-NHNN về tỷ lệ an toàn vốn của ngân hàng căn cứ vào luật nào, và luật đó quy định chức năng nhiệm vụ của cơ quan nào?",
        "Hoạt động giao nhận, vận chuyển tiền mặt và tài sản quý của Ngân hàng Nhà nước được điều chỉnh bởi Thông tư nào, và Thông tư đó có được sửa đổi bổ sung bởi văn bản nào không?"
    ]
    
    output_path = "qa_comparison.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# Báo cáo so sánh Hỏi đáp Multi-hop Graph RAG\n\n")
        f.write("Báo cáo này so sánh kết quả trả lời câu hỏi pháp lý dựa trên số bước nhảy (hops) khi truy xuất dữ liệu từ Neo4j.\n\n")
        
        for i, q in enumerate(questions):
            print(f"\\n--- Đang xử lý Câu hỏi {i+1} ---")
            f.write(f"## Câu hỏi {i+1}: {q}\n\n")
            
            for hops in [0, 1, 2]:
                print(f"  + Số bước nhảy (hops) = {hops}")
                context = get_context(driver, q, k=2, hops=hops)
                answer = ask_gemini(q, context)
                
                f.write(f"### Số bước nhảy (hops) = {hops}\n")
                f.write(f"**Độ dài ngữ cảnh:** {len(context)} ký tự\n\n")
                f.write(f"**Câu trả lời:**\n{answer}\n\n")
                f.write("---\n")
                
    driver.close()
    print(f"\\nHoàn thành! Kết quả được lưu tại {output_path}")

if __name__ == "__main__":
    main()
