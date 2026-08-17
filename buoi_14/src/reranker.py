from sentence_transformers import CrossEncoder

class NeuralReranker:
    def __init__(self, model_name="cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model = CrossEncoder(model_name)

    def rerank(self, query, candidates, top_k=5):
        if not candidates:
            return []
            
        # Prepare pairs of (query, candidate_text)
        pairs = [[str(query), c['text']] for c in candidates]
        
        # Predict scores
        scores = self.model.predict(pairs)
        
        # Add scores to candidates
        for i, c in enumerate(candidates):
            c['rerank_score'] = float(scores[i])
            c['retrieval_method'] = "Hybrid + Rerank"
            
        # Sort by rerank score
        reranked = sorted(candidates, key=lambda x: x['rerank_score'], reverse=True)
        
        # Update ranks
        for rank, c in enumerate(reranked, 1):
            c['final_rank'] = rank
            
        return reranked[:top_k]
