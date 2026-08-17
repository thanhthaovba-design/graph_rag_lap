import sys
import os
import argparse

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))
from bm25_retriever import BM25Retriever
from dense_retriever import DenseRetriever

def main():
    parser = argparse.ArgumentParser(description="Baseline Retrieval (BM25 vs Dense)")
    parser.add_argument("--query", type=str, required=True, help="Query string")
    parser.add_argument("--top-k", type=int, default=5, help="Top k results")
    args = parser.parse_args()

    corpus_path = "C:/graph_rag_labs/buoi_14/data/processed/chunks_normalized.csv"
    if not os.path.exists(corpus_path):
        print(f"Error: Corpus not found at {corpus_path}. Please run prepare_corpus.py first.")
        return

    print(f"Loading corpus from {corpus_path}...")
    
    print("\n--- BM25 RESULTS ---")
    bm25 = BM25Retriever(corpus_path)
    bm25_res = bm25.retrieve(args.query, top_k=args.top_k)
    for r in bm25_res:
        print(f"{r['rank']}. Chunk: {r['chunk_id']} | Score: {r['retrieval_score']:.4f} | Citation: {r['citation']}")
        
    print("\n--- DENSE RESULTS ---")
    dense = DenseRetriever(corpus_path)
    dense_res = dense.retrieve(args.query, top_k=args.top_k)
    for r in dense_res:
        print(f"{r['rank']}. Chunk: {r['chunk_id']} | Score: {r['retrieval_score']:.4f} | Citation: {r['citation']}")

if __name__ == "__main__":
    main()
