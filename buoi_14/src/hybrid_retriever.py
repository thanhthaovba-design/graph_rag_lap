class HybridRetriever:
    def __init__(self, bm25_retriever, dense_retriever):
        self.bm25_retriever = bm25_retriever
        self.dense_retriever = dense_retriever

    def compute_rrf(self, bm25_results, dense_results, k=60):
        # Create a dictionary to hold the combined scores
        rrf_scores = {}
        items = {}
        
        # Helper to process results
        def process_results(results, method_name):
            for rank, item in enumerate(results, 1):
                chunk_id = item['chunk_id']
                if chunk_id not in rrf_scores:
                    rrf_scores[chunk_id] = 0
                    items[chunk_id] = item
                
                # RRF formula: 1 / (k + rank)
                rrf_scores[chunk_id] += 1.0 / (k + rank)
                items[chunk_id][f'{method_name.lower()}_rank'] = rank

        process_results(bm25_results, "BM25")
        process_results(dense_results, "Dense")

        # Sort by RRF score
        sorted_chunks = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        
        final_results = []
        for rank, (chunk_id, rrf_score) in enumerate(sorted_chunks, 1):
            item = items[chunk_id].copy()
            item['rrf_score'] = rrf_score
            item['final_rank'] = rank
            item['retrieval_method'] = "Hybrid (RRF)"
            final_results.append(item)
            
        return final_results

    def retrieve(self, query, top_k=5, candidate_k=20):
        # Get more candidates before RRF
        bm25_results = self.bm25_retriever.retrieve(query, top_k=candidate_k)
        dense_results = self.dense_retriever.retrieve(query, top_k=candidate_k)
        
        hybrid_results = self.compute_rrf(bm25_results, dense_results)
        return hybrid_results[:top_k]
