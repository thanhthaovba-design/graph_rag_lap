import pandas as pd
import json
import numpy as np
import os
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

def filter_by_roles(df, user_roles):
    """Filter DataFrame rows where there's an intersection between allowed_roles and user_roles."""
    if not user_roles:
        return df.iloc[0:0]
        
    def has_access(roles_str):
        try:
            allowed = json.loads(roles_str)
            return any(role in user_roles for role in allowed)
        except:
            return False
            
    mask = df['allowed_roles'].apply(has_access)
    return df[mask].copy()

class SecureBM25Retriever:
    def __init__(self, corpus_path):
        self.corpus_path = corpus_path
        self.full_df = pd.read_csv(corpus_path).fillna("")

    def retrieve(self, query, user_roles, top_k=5):
        df = filter_by_roles(self.full_df, user_roles)
        if len(df) == 0:
            return []
            
        tokenized_corpus = [doc.lower().split() for doc in df['text']]
        if not tokenized_corpus:
            return []
            
        bm25 = BM25Okapi(tokenized_corpus)
        tokenized_query = str(query).lower().split()
        doc_scores = bm25.get_scores(tokenized_query)
        
        df['retrieval_score'] = doc_scores
        top_n = df.nlargest(top_k, 'retrieval_score')
        
        results = []
        for rank, (_, row) in enumerate(top_n.iterrows(), 1):
            if row['retrieval_score'] <= 0:
                continue
            results.append({
                "chunk_id": row['chunk_id'],
                "document_id": row.get('document_id', ''),
                "text": row['text'],
                "retrieval_score": row['retrieval_score'],
                "retrieval_method": "Secure BM25",
                "citation": f"[{row.get('document_id', '')} | Chunk {row['chunk_id']}]",
                "allowed_roles": row['allowed_roles']
            })
        return results

class SecureDenseRetriever:
    def __init__(self, corpus_path, model_name="keepitreal/vietnamese-sbert"):
        self.corpus_path = corpus_path
        self.full_df = pd.read_csv(corpus_path).fillna("")
        self.model = SentenceTransformer(model_name)
        
        # Cache embeddings to disk to speed up Streamlit
        embeddings_cache_path = corpus_path.replace(".csv", "_embeddings.npy")
        if os.path.exists(embeddings_cache_path):
            print(f"Loading precomputed embeddings from {embeddings_cache_path}...")
            self.corpus_embeddings = np.load(embeddings_cache_path)
        else:
            print(f"Precomputing embeddings for {len(self.full_df)} chunks...")
            self.corpus_embeddings = self.model.encode(self.full_df['text'].tolist())
            print(f"Saving embeddings to {embeddings_cache_path}...")
            np.save(embeddings_cache_path, self.corpus_embeddings)

    def retrieve(self, query, user_roles, top_k=5):
        def has_access(roles_str):
            try:
                allowed = json.loads(roles_str)
                return any(role in user_roles for role in allowed)
            except:
                return False
                
        access_mask = self.full_df['allowed_roles'].apply(has_access).values
        if not any(access_mask):
            return []
            
        df = self.full_df[access_mask].copy()
        filtered_embeddings = self.corpus_embeddings[access_mask]
        
        query_embedding = self.model.encode([str(query)])
        similarities = cosine_similarity(query_embedding, filtered_embeddings)[0]
        
        df['retrieval_score'] = similarities
        top_n = df.nlargest(top_k, 'retrieval_score')
        
        results = []
        for rank, (_, row) in enumerate(top_n.iterrows(), 1):
            results.append({
                "chunk_id": row['chunk_id'],
                "document_id": row.get('document_id', ''),
                "text": row['text'],
                "retrieval_score": row['retrieval_score'],
                "retrieval_method": "Secure Dense",
                "citation": f"[{row.get('document_id', '')} | Chunk {row['chunk_id']}]",
                "allowed_roles": row['allowed_roles']
            })
        return results

class SecureGraphRetriever:
    def __init__(self):
        uri = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "password")
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def retrieve(self, query, user_roles, top_k=5):
        # We perform a full text search or simple keyword matching in Neo4j, 
        # combining with RBAC WHERE clause. Since no fulltext index was strictly defined 
        # in the lab instruction, we will use a basic MATCH with string contains.
        
        keywords = query.lower().split()
        if not keywords:
            return []
            
        # Create dynamic WHERE clause for keyword matching
        keyword_conditions = " OR ".join([f"toLower(node.text) CONTAINS '{kw}'" for kw in keywords])
        
        # The key required Cypher clause for Security Tagging:
        # WHERE any(role IN node.allowed_roles WHERE role IN $user_roles)
        
        cypher_query = f"""
        MATCH (node:DieuKhoan)
        WHERE ({keyword_conditions}) 
          AND any(role IN node.allowed_roles WHERE role IN $user_roles)
        RETURN node.id AS chunk_id, node.document_id AS document_id, node.text AS text, node.allowed_roles AS allowed_roles
        LIMIT $top_k
        """
        
        with self.driver.session() as session:
            result = session.run(cypher_query, user_roles=user_roles, top_k=top_k)
            
            results = []
            for record in result:
                roles_str = json.dumps(record["allowed_roles"]) if isinstance(record["allowed_roles"], list) else record["allowed_roles"]
                results.append({
                    "chunk_id": record["chunk_id"],
                    "document_id": record.get("document_id", ""),
                    "text": record["text"],
                    "retrieval_score": 1.0, # Dummy score for Graph Match
                    "retrieval_method": "Secure Graph",
                    "citation": f"[{record.get('document_id', '')} | Chunk {record['chunk_id']}]",
                    "allowed_roles": roles_str
                })
            return results
            
    def close(self):
        self.driver.close()

class SecureHybridRetriever:
    def __init__(self, bm25_retriever, dense_retriever, graph_retriever=None):
        self.bm25_retriever = bm25_retriever
        self.dense_retriever = dense_retriever
        self.graph_retriever = graph_retriever

    def compute_rrf(self, results_lists, k=60):
        rrf_scores = {}
        items = {}
        
        for method_idx, results in enumerate(results_lists):
            for rank, item in enumerate(results, 1):
                chunk_id = item['chunk_id']
                if chunk_id not in rrf_scores:
                    rrf_scores[chunk_id] = 0
                    items[chunk_id] = item.copy()
                rrf_scores[chunk_id] += 1.0 / (k + rank)
                items[chunk_id][f'method_{method_idx}_rank'] = rank

        sorted_chunks = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        
        final_results = []
        for rank, (chunk_id, rrf_score) in enumerate(sorted_chunks, 1):
            item = items[chunk_id].copy()
            item['rrf_score'] = rrf_score
            item['final_rank'] = rank
            item['retrieval_method'] = "Secure Hybrid (RRF)"
            final_results.append(item)
        return final_results

    def retrieve(self, query, user_roles, top_k=5, candidate_k=20):
        bm25_results = self.bm25_retriever.retrieve(query, user_roles, top_k=candidate_k)
        dense_results = self.dense_retriever.retrieve(query, user_roles, top_k=candidate_k)
        
        results_lists = [bm25_results, dense_results]
        
        if self.graph_retriever:
            graph_results = self.graph_retriever.retrieve(query, user_roles, top_k=candidate_k)
            results_lists.append(graph_results)
            
        hybrid_results = self.compute_rrf(results_lists)
        return hybrid_results[:top_k]
