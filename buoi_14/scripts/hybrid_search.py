import sys
import os
import argparse

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))
from bm25_retriever import BM25Retriever
from dense_retriever import DenseRetriever
from hybrid_retriever import HybridRetriever

def main():
    parser = argparse.ArgumentParser(description="Hybrid Search")
    parser.add_argument("--query", type=str, required=True, help="Query string")
    parser.add_argument("--top-k", type=int, default=5, help="Top k results")
    parser.add_argument("--candidate-k", type=int, default=20, help="Candidate k before RRF")
    args = parser.parse_args()

    corpus_path = "C:/graph_rag_labs/buoi_14/data/processed/chunks_normalized.csv"
    if not os.path.exists(corpus_path):
        print(f"Error: Corpus not found at {corpus_path}. Please run prepare_corpus.py first.")
        return

    print("Loading retrievers...")
    bm25 = BM25Retriever(corpus_path)
    dense = DenseRetriever(corpus_path)
    hybrid = HybridRetriever(bm25, dense)
    
    print(f"\nQUERY: {args.query}")
    print("\nHYBRID RESULTS\n")
    print(f"{'Rank':<5} | {'Chunk':<10} | {'BM25 rank':<10} | {'Dense rank':<10} | {'RRF':<6} | {'Citation'}")
    print("-" * 80)
    
    results = hybrid.retrieve(args.query, top_k=args.top_k, candidate_k=args.candidate_k)
    for r in results:
        print(f"{r['final_rank']:<5} | {r['chunk_id']:<10} | {r.get('bm25_rank', '-'):<10} | {r.get('dense_rank', '-'):<10} | {r['rrf_score']:.4f} | {r['citation']}")

if __name__ == "__main__":
    main()
