import pandas as pd
from rank_bm25 import BM25Okapi

class BM25Retriever:
    def __init__(self, corpus_path):
        self.corpus_path = corpus_path
        self.df = pd.read_csv(corpus_path)
        self.df = self.df.fillna("")
        
        # Tokenize using simple whitespace
        self.tokenized_corpus = [doc.lower().split() for doc in self.df['text']]
        self.bm25 = BM25Okapi(self.tokenized_corpus)

    def retrieve(self, query, top_k=5):
        tokenized_query = str(query).lower().split()
        
        # Get raw scores
        doc_scores = self.bm25.get_scores(tokenized_query)
        
        # Add scores to dataframe to sort
        self.df['retrieval_score'] = doc_scores
        
        # Get top k
        top_n = self.df.nlargest(top_k, 'retrieval_score')
        
        results = []
        for rank, (_, row) in enumerate(top_n.iterrows(), 1):
            if row['retrieval_score'] <= 0:
                continue
                
            results.append({
                "rank": rank,
                "chunk_id": row['chunk_id'],
                "document_id": row.get('document_id', ''),
                "text": row['text'],
                "retrieval_score": row['retrieval_score'],
                "retrieval_method": "BM25",
                "citation": f"[{row.get('document_id', '')} | Chunk {row['chunk_id']}]"
            })
            
        return results
