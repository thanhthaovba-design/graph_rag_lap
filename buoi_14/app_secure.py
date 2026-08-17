import streamlit as st
import sys
import os
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from secure_retriever import SecureBM25Retriever, SecureDenseRetriever, SecureGraphRetriever, SecureHybridRetriever
from reranker import NeuralReranker
from scripts.query_demo import get_graph_hints

st.set_page_config(page_title="RAG Hybrid Search - Secure RBAC", layout="wide")

def load_css():
    st.markdown("""
        <style>
        .main-banner {
            background: linear-gradient(90deg, #1A365D 0%, #2B6CB0 50%, #00B5D8 100%);
            border-radius: 12px;
            padding: 30px;
            color: white;
            margin-bottom: 25px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .main-banner h1 {
            color: white !important;
            margin-top: 0;
            font-size: 2.2rem;
            font-weight: 700;
        }
        .main-banner p {
            font-size: 1.1rem;
            opacity: 0.9;
            margin-bottom: 0;
        }
        [data-testid="stSidebar"] {
            background-color: #F8FAFC;
        }
        div.stButton > button:first-child {
            background-color: #EF4444;
            color: white;
            border-radius: 8px;
            border: none;
            width: 100%;
            font-weight: 600;
            padding: 10px;
            transition: all 0.3s;
        }
        div.stButton > button:first-child:hover {
            background-color: #DC2626;
            box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
            color: white;
        }
        .result-card {
            background-color: white;
            border-left: 5px solid #3B82F6;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 15px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            border-top: 1px solid #F1F5F9;
            border-right: 1px solid #F1F5F9;
            border-bottom: 1px solid #F1F5F9;
        }
        .result-card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid #E2E8F0;
        }
        .result-citation {
            color: #1E40AF;
            font-weight: 600;
            font-size: 0.95rem;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .result-badge {
            background-color: #ECFDF5;
            color: #059669;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 700;
            text-align: right;
        }
        .result-content {
            color: #334155;
            font-size: 1rem;
            line-height: 1.6;
        }
        .security-badge {
            background-color: #FEF3C7;
            color: #92400E;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8rem;
            font-weight: 600;
            margin-left: 10px;
        }
        .alert-filtered {
            background-color: #FEF2F2;
            color: #991B1B;
            padding: 10px;
            border-radius: 8px;
            font-weight: 600;
            margin-bottom: 20px;
            border: 1px solid #FCA5A5;
        }
        </style>
    """, unsafe_allow_html=True)

load_css()

@st.cache_resource
def load_secure_retrievers():
    corpus_path = "data/processed/chunks_secure.csv"
    if not os.path.exists(corpus_path):
        return None, None, None, None
    bm25 = SecureBM25Retriever(corpus_path)
    dense = SecureDenseRetriever(corpus_path)
    graph = SecureGraphRetriever()
    reranker = NeuralReranker()
    return bm25, dense, graph, reranker

bm25_retriever, dense_retriever, graph_retriever, reranker = load_secure_retrievers()

if not bm25_retriever:
    st.error("Secure corpus not found. Please run scripts/assign_security_tags.py first.")
    st.stop()

hybrid_retriever = SecureHybridRetriever(bm25_retriever, dense_retriever, graph_retriever)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### 🔐 Cấu hình Phân Quyền (RBAC)")
    # Use multiselect instead of selectbox
    all_roles = ["Admin", "HR", "Risk_Manager", "Staff", "Guest"]
    user_roles = st.multiselect("Chọn Vai Trò (Role):", all_roles, default=["Guest"])
    st.info(f"Bạn đang đăng nhập với quyền: **{', '.join(user_roles)}**")
    
    st.markdown("### 🔍 Cấu hình Retrieval")
    query = st.text_area("Nhập câu hỏi tra cứu:")
    method = st.selectbox("Phương pháp Retrieval:", ["BM25", "Dense", "Hybrid", "Hybrid + Rerank"], index=3)
    top_k = st.slider("Top-k Kết quả:", 1, 20, 5)
    candidate_k = st.slider("Số lượng Ứng viên (Candidate-N):", 5, 50, 20)
    
    search_clicked = st.button("🚀 Tìm kiếm an toàn")

# --- MAIN BANNER ---
st.markdown("""
    <div class="main-banner">
        <h1>🛡️ Secure RAG Hybrid Search with RBAC</h1>
        <p>Hệ thống RAG nâng cao kết hợp phân quyền mức dữ liệu (Data-level Access Control)</p>
    </div>
""", unsafe_allow_html=True)

# --- SEARCH LOGIC ---
if search_clicked and query:
    if not user_roles:
        st.error("Vui lòng chọn ít nhất một vai trò để thực hiện tìm kiếm.")
        st.stop()
        
    results = []
    before_rerank = []
    
    # We will simulate the count of filtered items by comparing with Admin retrieval
    # In a real app, the retriever could return this stat directly, but we will run a quick Admin query to compare.
    admin_results = hybrid_retriever.retrieve(query, ["Admin"], top_k=candidate_k, candidate_k=candidate_k)
    
    if method == "BM25":
        results = bm25_retriever.retrieve(query, user_roles, top_k=top_k)
    elif method == "Dense":
        results = dense_retriever.retrieve(query, user_roles, top_k=top_k)
    elif method == "Hybrid":
        results = hybrid_retriever.retrieve(query, user_roles, top_k=top_k, candidate_k=candidate_k)
    elif method == "Hybrid + Rerank":
        candidates = hybrid_retriever.retrieve(query, user_roles, top_k=candidate_k, candidate_k=candidate_k)
        before_rerank = [{"rank": c['final_rank'], "chunk": c['chunk_id']} for c in candidates[:top_k]]
        results = reranker.rerank(query, candidates, top_k=top_k)

    # Calculate Filtered Items
    filtered_count = len(admin_results) - len(results) if len(admin_results) > len(results) else 0

    if not results:
        st.warning(f"Không tìm thấy kết quả hoặc bạn không có quyền xem tài liệu phù hợp.")
    else:
        # Display filter warning if any items were excluded
        if filtered_count > 0:
            st.markdown(f'<div class="alert-filtered">⚠️ Đã lọc bỏ {filtered_count} kết quả do không đủ quyền truy cập</div>', unsafe_allow_html=True)
            
        st.markdown(f"### 📌 Kết quả Tra cứu ({method}) - Role: {', '.join(user_roles)}")
        st.markdown(f"*Hiển thị Top {top_k} kết quả cho câu hỏi:* **\"{query}\"**")
        st.markdown("<br>", unsafe_allow_html=True)
        
        col_results, col_metrics = st.columns([7, 3], gap="large")
        
        with col_results:
            # Display Graph Hints for authorized chunks ONLY
            doc_ids = list(set(r['document_id'] for r in results))
            chunk_ids = list(set(r['chunk_id'] for r in results))
            hints = get_graph_hints(doc_ids, chunk_ids)
            if hints:
                for h in hints:
                    st.info(f"💡 **Graph Hint:** {h}")
            
            # Display Custom Result Cards
            for i, r in enumerate(results):
                rank = r.get('final_rank', r.get('rank', i+1))
                score = r.get('rerank_score', r.get('rrf_score', r.get('retrieval_score', 0)))
                
                card_html = f"""
                <div class="result-card">
                    <div class="result-card-header">
                        <div class="result-citation">
                            📚 {r.get('citation', 'Tài liệu')} 
                            <span class="security-badge">🔒 Quyền xem: {r.get('allowed_roles', '')}</span>
                        </div>
                        <div class="result-badge">
                            Rank #{rank} | <br>Score: {score:.4f}
                        </div>
                    </div>
                    <div class="result-content">
                        {r.get('text', '')}
                    </div>
                </div>
                """
                st.markdown(card_html, unsafe_allow_html=True)
                
        with col_metrics:
            st.markdown("### 📊 Ranking Metrics")
            metrics_data = []
            for i, r in enumerate(results):
                metrics_data.append({
                    "Rank": i + 1,
                    "Chunk ID": r['chunk_id'],
                    "Method Rank": r.get('final_rank', 'N/A'),
                    "Score": f"{r.get('rerank_score', r.get('rrf_score', r.get('retrieval_score', 0))):.4f}"
                })
            
            df_metrics = pd.DataFrame(metrics_data)
            st.dataframe(df_metrics, use_container_width=True, hide_index=True)
