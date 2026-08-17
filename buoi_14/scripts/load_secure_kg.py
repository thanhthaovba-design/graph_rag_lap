import os
import json
import pandas as pd
from neo4j import GraphDatabase
from dotenv import load_dotenv

def main():
    # Load .env
    load_dotenv()
    
    uri = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")
    
    csv_path = "c:/graph_rag_labs/buoi_14/data/processed/chunks_secure.csv"
    if not os.path.exists(csv_path):
        print(f"Error: Could not find {csv_path}")
        return
        
    print(f"Reading data from {csv_path}...")
    df = pd.read_csv(csv_path)
    df = df.fillna("")
    
    # Connect to Neo4j
    print(f"Connecting to Neo4j at {uri}...")
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        driver.verify_connectivity()
    except Exception as e:
        print(f"Neo4j connection error: {e}")
        return
        
    # Prepare batch data
    # We will update VanBan and DieuKhoan nodes that belong to lab_session = "buoi_15"
    # Actually, the user asked to not DETACH DELETE and update/merge properties for nodes, distinguishing by lab_session = "buoi_15".
    # We will just SET the allowed_roles for existing nodes based on id.
    
    # Document Level Roles
    doc_roles = {}
    for _, row in df.iterrows():
        doc_id = str(row.get('document_id', ''))
        roles = json.loads(row.get('allowed_roles', '[]'))
        if doc_id and doc_id not in doc_roles:
            doc_roles[doc_id] = roles
            
    doc_batch = [{"id": d_id, "roles": r, "session": "buoi_15"} for d_id, r in doc_roles.items()]
    
    # Chunk Level Roles
    chunk_batch = []
    for _, row in df.iterrows():
        chunk_id = str(row.get('chunk_id', ''))
        roles = json.loads(row.get('allowed_roles', '[]'))
        if chunk_id:
            chunk_batch.append({"id": chunk_id, "roles": roles, "session": "buoi_15"})
            
    print(f"Updating {len(doc_batch)} VanBan nodes and {len(chunk_batch)} DieuKhoan nodes...")
    
    with driver.session() as session:
        # MERGE or MATCH/SET for VanBan
        q_doc = """
        UNWIND $rows AS row
        MERGE (v:VanBan {id: row.id})
        SET v.allowed_roles = row.roles, v.lab_session = row.session
        """
        session.run(q_doc, rows=doc_batch)
        
        # MERGE or MATCH/SET for DieuKhoan
        q_chunk = """
        UNWIND $rows AS row
        MERGE (d:DieuKhoan {id: row.id})
        SET d.allowed_roles = row.roles, d.lab_session = row.session
        """
        session.run(q_chunk, rows=chunk_batch)
        
        # Verification
        print("Update complete! Running verification queries...")
        
        q_count = """
        MATCH (n)
        WHERE n.allowed_roles IS NOT NULL
        RETURN labels(n) AS label, count(n) AS count
        """
        res_count = session.run(q_count)
        print("\nNodes with 'allowed_roles' property:")
        for record in res_count:
            print(f"- {record['label']}: {record['count']}")
            
        q_verify = """
        MATCH (v:VanBan)-[r]->(d:DieuKhoan)
        WHERE v.allowed_roles IS NOT NULL AND d.allowed_roles IS NOT NULL
        RETURN v.id AS doc_id, v.allowed_roles AS doc_roles, d.id AS chunk_id, d.allowed_roles AS chunk_roles
        LIMIT 1
        """
        res_verify = session.run(q_verify)
        record = res_verify.single()
        if record:
            print("\nSample Verification:")
            print(f"VanBan (id={record['doc_id']}) -> Roles: {record['doc_roles']}")
            print(f"  |-- DieuKhoan (id={record['chunk_id']}) -> Roles: {record['chunk_roles']}")
        else:
            # Maybe there are no relationships yet, let's just pick isolated nodes
            q_single = "MATCH (n) WHERE n.allowed_roles IS NOT NULL RETURN labels(n)[0] AS lbl, n.id AS id, n.allowed_roles AS roles LIMIT 3"
            res = session.run(q_single)
            print("\nSample Nodes:")
            for rec in res:
                print(f"{rec['lbl']} (id={rec['id']}) -> Roles: {rec['roles']}")

    driver.close()

if __name__ == "__main__":
    main()
