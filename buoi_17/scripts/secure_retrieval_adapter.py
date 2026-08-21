import os
import sys
import pandas as pd

# Import from buoi_14
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../buoi_14")))
from src.secure_retriever import SecureBM25Retriever, SecureDenseRetriever, SecureRetriever

class SecureRetrievalAdapter:
    def __init__(self, corpus_path):
        self.corpus_path = corpus_path
        self.bm25 = SecureBM25Retriever(corpus_path)
        self.dense = SecureDenseRetriever(corpus_path)
        # Using Hybrid (SecureRetriever) as requested
        self.retriever = SecureRetriever(self.bm25, self.dense)
        self.df = pd.read_csv(corpus_path)

    def retrieve(self, query, user_roles, top_k=5):
        raw_results = self.retriever.retrieve(query, user_roles, top_k=top_k)
        
        normalized_results = []
        for i, res in enumerate(raw_results):
            chunk_id = res['chunk_id']
            # Fetch missing fields like title from dataframe
            row = self.df[self.df['chunk_id'] == chunk_id].iloc[0]
            
            normalized_results.append({
                "rank": res.get("final_rank", i + 1),
                "chunk_id": chunk_id,
                "document_id": res.get("document_id", ""),
                "title": row.get("title", ""),
                "article": res.get("text", ""),
                "citation": res.get("citation", ""),
                "allowed_roles": res.get("allowed_roles", ""),
                "access_decision": "ALLOWED", # Since it's filtered before retrieval, any result here is allowed
                "retrieval_method": res.get("retrieval_method", "Secure Hybrid (RRF)")
            })
        return normalized_results
