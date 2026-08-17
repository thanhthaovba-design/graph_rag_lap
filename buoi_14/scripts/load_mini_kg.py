import sys
import os
import argparse
import pandas as pd
from neo4j import GraphDatabase
from dotenv import load_dotenv

def main():
    load_dotenv()
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")

    corpus_path = "C:/graph_rag_labs/buoi_14/data/processed/chunks_normalized.csv"
    if not os.path.exists(corpus_path):
        print("Corpus not found.")
        return
        
    df = pd.read_csv(corpus_path)
    df = df.fillna("")
    
    print("Connecting to Neo4j...")
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        driver.verify_connectivity()
    except Exception as e:
        print(f"Failed to connect to Neo4j: {e}")
        print("Please check your Neo4j instance and .env file.")
        return
        
    print("Loading nodes and relationships into Mini KG...")
    with driver.session() as session:
        # Create constraint
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (v:VanBan) REQUIRE v.id IS UNIQUE")
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (d:DieuKhoan) REQUIRE d.id IS UNIQUE")
        
        # We will create VanBan and DieuKhoan from the chunks.
        # Assuming document_id maps to VanBan, and chunk_id maps to DieuKhoan.
        query = """
        UNWIND $rows AS row
        MERGE (v:VanBan {id: row.document_id})
        ON CREATE SET v.lab_session = 'buoi_14'
        MERGE (d:DieuKhoan {id: row.chunk_id})
        ON CREATE SET 
            d.lab_session = 'buoi_14',
            d.document_id = row.document_id,
            d.text = row.text
        MERGE (v)-[:CONTAINS]->(d)
        """
        
        # Prepare batch
        batch = []
        for _, row in df.iterrows():
            if row.get('document_id'):
                batch.append({
                    "document_id": str(row['document_id']),
                    "chunk_id": str(row['chunk_id']),
                    "text": str(row['text'])
                })
                
        session.run(query, rows=batch)
        print(f"Loaded {len(batch)} DieuKhoan nodes and their relationships to VanBan.")
        
        # Add NEXT relations
        print("Linking DieuKhoan nodes sequentially (NEXT)...")
        # In a real scenario, we'd sort properly. We assume chunks are sequential within document
        for doc_id, group in df.groupby('document_id'):
            chunks = group['chunk_id'].tolist()
            for i in range(len(chunks)-1):
                c1 = chunks[i]
                c2 = chunks[i+1]
                q_next = """
                MATCH (d1:DieuKhoan {id: $c1}), (d2:DieuKhoan {id: $c2})
                MERGE (d1)-[:NEXT]->(d2)
                """
                session.run(q_next, c1=str(c1), c2=str(c2))
                
        print("Mini KG Load Complete.")
        
    driver.close()

if __name__ == "__main__":
    main()
