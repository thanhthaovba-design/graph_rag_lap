import sys
import os
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))
from bm25_retriever import BM25Retriever
from dense_retriever import DenseRetriever
from hybrid_retriever import HybridRetriever
from reranker import NeuralReranker

def main():
    corpus_path = "C:/graph_rag_labs/buoi_14/data/processed/chunks_normalized.csv"
    if not os.path.exists(corpus_path):
        print(f"Error: Corpus not found at {corpus_path}.")
        return

    # In a real evaluation, we'd load questions from a CSV
    # For this demo, let's use a mock evaluation set
    eval_queries = [
        {"id": 1, "query": "Ai có thẩm quyền phê duyệt giao dịch vượt hạn mức?", "expected_chunk_id": "DK-014"},
        {"id": 2, "query": "Quy định QĐ-125 nói gì về phê duyệt?", "expected_chunk_id": "DK-125"}
    ]
    
    print("Loading retrievers...")
    bm25 = BM25Retriever(corpus_path)
    dense = DenseRetriever(corpus_path)
    hybrid = HybridRetriever(bm25, dense)
    reranker = NeuralReranker()
    
    results = []
    
    for q in eval_queries:
        query = q["query"]
        expected = q["expected_chunk_id"]
        
        # We just test BM25 for demo metrics
        bm25_res = bm25.retrieve(query, top_k=5)
        bm25_hit = any(r['chunk_id'] == expected for r in bm25_res)
        
        results.append({
            "query_id": q["id"],
            "bm25_hit@5": bm25_hit
        })
        
    df = pd.DataFrame(results)
    out_path = "C:/graph_rag_labs/buoi_14/outputs/retrieval_comparison.csv"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    df.to_csv(out_path, index=False)
    
    print(f"Evaluation completed. Results saved to {out_path}")
    print(df)

if __name__ == "__main__":
    main()
