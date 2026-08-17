import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

class DenseRetriever:
    def __init__(self, corpus_path, model_name="keepitreal/vietnamese-sbert"):
        self.corpus_path = corpus_path
        self.df = pd.read_csv(corpus_path)
        self.df = self.df.fillna("")
        self.model = SentenceTransformer(model_name)
        
        # In a real app, you would load pre-computed embeddings.
        # Here we compute them on the fly for simplicity (might be slow).
        self.corpus_embeddings = self.model.encode(self.df['text'].tolist())

    def retrieve(self, query, top_k=5):
        query_embedding = self.model.encode([str(query)])
        
        # Calculate cosine similarity
        similarities = cosine_similarity(query_embedding, self.corpus_embeddings)[0]
        self.df['retrieval_score'] = similarities
        
        top_n = self.df.nlargest(top_k, 'retrieval_score')
        
        results = []
        for rank, (_, row) in enumerate(top_n.iterrows(), 1):
            results.append({
                "rank": rank,
                "chunk_id": row['chunk_id'],
                "document_id": row.get('document_id', ''),
                "text": row['text'],
                "retrieval_score": row['retrieval_score'],
                "retrieval_method": "Dense",
                "citation": f"[{row.get('document_id', '')} | Chunk {row['chunk_id']}]"
            })
            
        return results
