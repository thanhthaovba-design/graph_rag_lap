import sys
import os
import argparse
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))
from bm25_retriever import BM25Retriever
from dense_retriever import DenseRetriever
from hybrid_retriever import HybridRetriever
from reranker import NeuralReranker

def main():
    parser = argparse.ArgumentParser(description="Hybrid Search + Reranking")
    parser.add_argument("--query", type=str, required=True, help="Query string")
    parser.add_argument("--top-k", type=int, default=5, help="Top k results")
    parser.add_argument("--candidate-k", type=int, default=20, help="Candidate k before RRF")
    args = parser.parse_args()

    corpus_path = "C:/graph_rag_labs/buoi_14/data/processed/chunks_normalized.csv"
    if not os.path.exists(corpus_path):
        print(f"Error: Corpus not found at {corpus_path}. Please run prepare_corpus.py first.")
        return

    print("Loading retrievers and reranker...")
    bm25 = BM25Retriever(corpus_path)
    dense = DenseRetriever(corpus_path)
    hybrid = HybridRetriever(bm25, dense)
    reranker = NeuralReranker()
    
    print(f"\nQUERY:\n\"{args.query}\"\n")
    
    # Get candidates
    candidates = hybrid.retrieve(args.query, top_k=args.candidate_k, candidate_k=args.candidate_k)
    
    print("BEFORE RERANK (Top 5 for preview)")
    for r in candidates[:5]:
        print(f"{r['final_rank']}. {r['chunk_id']} | Score: {r['rrf_score']:.4f}")
        
    print("\nRunning Reranker...")
    results = reranker.rerank(args.query, candidates, top_k=args.top_k)
    
    print("\nAFTER RERANK")
    for r in results:
        print(f"{r['final_rank']}. {r['chunk_id']} | Score: {r['rerank_score']:.4f} | Citation: {r['citation']}")

if __name__ == "__main__":
    main()
