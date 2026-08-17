import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

def get_graph_hints(doc_ids, chunk_ids):
    """
    Connect to Neo4j and return hints about relationships for the retrieved chunks.
    """
    if not chunk_ids:
        return []
        
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password") # Default fallback
    
    hints = set()
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        with driver.session() as session:
            # Check for NEXT relationship
            q_next = """
            MATCH (d1:DieuKhoan)-[:NEXT]->(d2:DieuKhoan)
            WHERE d1.id IN $chunk_ids OR d2.id IN $chunk_ids
            RETURN d1.id AS c1, d2.id AS c2
            LIMIT 5
            """
            res_next = session.run(q_next, chunk_ids=[str(c) for c in chunk_ids])
            for r in res_next:
                hints.add(f"Điều khoản {r['c1']} nằm liền trước Điều khoản {r['c2']}")
                
            # Check for CONTAINS relationship (document -> chunk)
            q_contains = """
            MATCH (v:VanBan)-[:CONTAINS]->(d:DieuKhoan)
            WHERE d.id IN $chunk_ids
            RETURN v.id AS doc, d.id AS chunk
            LIMIT 5
            """
            res_contains = session.run(q_contains, chunk_ids=[str(c) for c in chunk_ids])
            for r in res_contains:
                hints.add(f"Văn bản {r['doc']} chứa nội dung của {r['chunk']}")
                
        driver.close()
    except Exception as e:
        print(f"Neo4j Error: {e}")
        
    return list(hints)
