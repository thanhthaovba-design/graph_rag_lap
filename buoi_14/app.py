import streamlit as st
import sys
import os
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from bm25_retriever import BM25Retriever
from dense_retriever import DenseRetriever
from hybrid_retriever import HybridRetriever
from reranker import NeuralReranker
from scripts.query_demo import get_graph_hints

st.set_page_config(page_title="RAG Hybrid Search - Buổi 14", layout="wide")

def load_css():
    st.markdown("""
        <style>
        /* Banner Style */
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
        
        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: #F8FAFC;
        }
        
        /* Red Search Button */
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

        /* Result Card Styling */
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
        </style>
    """, unsafe_allow_html=True)

load_css()

@st.cache_resource
def load_retrievers():
    corpus_path = "data/processed/chunks_normalized.csv"
    if not os.path.exists(corpus_path):
        return None, None, None
    bm25 = BM25Retriever(corpus_path)
    dense = DenseRetriever(corpus_path)
    reranker = NeuralReranker()
    return bm25, dense, reranker

bm25_retriever, dense_retriever, reranker = load_retrievers()

if not bm25_retriever:
    st.error("Corpus not found. Please run prepare_corpus.py first.")
    st.stop()

hybrid_retriever = HybridRetriever(bm25_retriever, dense_retriever)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### 🔍 Cấu hình Retrieval")
    query = st.text_area("Nhập câu hỏi tra cứu:")
    method = st.selectbox("Phương pháp Retrieval:", ["BM25", "Dense", "Hybrid", "Hybrid + Rerank"], index=3)
    top_k = st.slider("Top-k Kết quả:", 1, 20, 5)
    candidate_k = st.slider("Số lượng Ứng viên (Candidate-N):", 5, 50, 20)
    
    search_clicked = st.button("🚀 Tìm kiếm")

# --- MAIN BANNER ---
st.markdown("""
    <div class="main-banner">
        <h1>⚡ RAG Hybrid Search + Reranking & Knowledge Graph Mini</h1>
        <p>Hệ thống RAG nâng cao kết hợp Lexical Search (BM25), Dense Vector Embedding, Reciprocal Rank Fusion & Cross-Encoder Reranking</p>
    </div>
""", unsafe_allow_html=True)

# --- SEARCH LOGIC ---
if search_clicked and query:
    
    results = []
    before_rerank = []
    
    if method == "BM25":
        results = bm25_retriever.retrieve(query, top_k=top_k)
    elif method == "Dense":
        results = dense_retriever.retrieve(query, top_k=top_k)
    elif method == "Hybrid":
        results = hybrid_retriever.retrieve(query, top_k=top_k, candidate_k=candidate_k)
    elif method == "Hybrid + Rerank":
        candidates = hybrid_retriever.retrieve(query, top_k=candidate_k, candidate_k=candidate_k)
        before_rerank = [{"rank": c['final_rank'], "chunk": c['chunk_id']} for c in candidates[:top_k]]
        results = reranker.rerank(query, candidates, top_k=top_k)

    if not results:
        st.warning("Không tìm thấy kết quả.")
    else:
        st.markdown(f"### 📌 Kết quả Tra cứu ({method})")
        st.markdown(f"*Hiển thị Top {top_k} kết quả cho câu hỏi:* **\"{query}\"**")
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Split into 2 columns: Results (Left) and Metrics (Right)
        col_results, col_metrics = st.columns([7, 3], gap="large")
        
        with col_results:
            # Display Graph Hints if any
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
                            📚 {r.get('citation', 'Tài liệu Nội bộ')}
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
                    "Hybrid Rank": r.get('bm25_rank', 'N/A') if method == 'BM25' else r.get('final_rank', 'N/A'),
                    "Score": f"{r.get('rerank_score', r.get('rrf_score', r.get('retrieval_score', 0))):.4f}"
                })
            
            df_metrics = pd.DataFrame(metrics_data)
            st.dataframe(df_metrics, use_container_width=True, hide_index=True)
