import streamlit as st
import os
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Basic Streamlit Config
st.set_page_config(page_title="Multi-hop Graph RAG Pháp lý", layout="wide")

# Initialize models and DB connection (cached to prevent reloading on every interaction)
@st.cache_resource
def load_models_and_db():
    load_dotenv(r"c:\Rag_thuchanh\RAG\rag_advanced\buoi_08\.env")
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        genai.configure(api_key=api_key)
    
    model_gen = genai.GenerativeModel('gemini-flash-latest')
    embed_model = SentenceTransformer('thuannc/vi-distilled-msmarco-MiniLM-L12-cos-v5', device='cpu')
    
    driver = GraphDatabase.driver("neo4j://127.0.0.1:7687", auth=("neo4j", "abcd1234"))
    
    return driver, embed_model, model_gen

driver, embed_model, model_gen = load_models_and_db()
DB_NAME = "neo4j"

def get_context(question, k=3, hops=0):
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

# UI Layout
st.title("📚 Tra cứu Pháp lý Multi-hop Graph RAG")
st.markdown("Hệ thống kết hợp tìm kiếm Vector và duyệt đồ thị Neo4j để tự động lấy thêm ngữ cảnh từ các tài liệu liên quan, sau đó sử dụng Gemini để sinh câu trả lời.")

with st.sidebar:
    st.header("⚙️ Cấu hình Tham số")
    hops = st.slider("Số bước nhảy (Hops)", min_value=0, max_value=3, value=1, help="Số lần duyệt qua các quan hệ pháp lý từ văn bản gốc.")
    top_k = st.number_input("Số Chunk ban đầu (k)", min_value=1, max_value=10, value=3)

# Chat Input
question = st.text_input("Nhập câu hỏi pháp lý của bạn:", placeholder="Ví dụ: Nghị định 46/2023/NĐ-CP thay thế cho nghị định nào?")

if st.button("Tìm kiếm & Trả lời", type="primary"):
    if not question.strip():
        st.warning("Vui lòng nhập câu hỏi!")
    else:
        with st.spinner("Đang truy xuất ngữ cảnh từ Neo4j..."):
            context = get_context(question, k=top_k, hops=hops)
        
        with st.spinner("Gemini đang tổng hợp câu trả lời..."):
            answer = ask_gemini(question, context)
            
        st.subheader("💡 Trả lời từ AI")
        st.info(answer)
        
        with st.expander(f"🔍 Ngữ cảnh Pháp lý Truy xuất (Độ dài: {len(context)} ký tự)"):
            st.text(context)
