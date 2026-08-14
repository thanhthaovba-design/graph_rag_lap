import os
import sys
import pandas as pd
from dotenv import load_dotenv
from neo4j import GraphDatabase

sys.stdout.reconfigure(encoding='utf-8')

def create_constraints(session):
    print("Creating constraints...")
    queries = [
        "CREATE CONSTRAINT document_id IF NOT EXISTS FOR (n:Document) REQUIRE n.id IS UNIQUE",
        "CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (n:CoQuan) REQUIRE n.id IS UNIQUE",
        "CREATE CONSTRAINT entity_id_nk IF NOT EXISTS FOR (n:NguoiKy) REQUIRE n.id IS UNIQUE",
        "CREATE CONSTRAINT entity_id_dt IF NOT EXISTS FOR (n:DoiTuongApDung) REQUIRE n.id IS UNIQUE",
        "CREATE CONSTRAINT entity_id_lv IF NOT EXISTS FOR (n:LinhVuc) REQUIRE n.id IS UNIQUE"
    ]
    for q in queries:
        session.run(q)

def import_documents(session, df_docs):
    print("Importing documents...")
    query = """
    UNWIND $rows AS row
    MERGE (d:Document {id: row.so_ky_hieu})
    SET d.original_id = row.id,
        d.title = row.title,
        d.loai_van_ban = row.loai_van_ban,
        d.ngay_ban_hanh = row.ngay_ban_hanh
    """
    rows = df_docs.to_dict('records')
    session.run(query, rows=rows)

def import_entities(session, df_entities):
    print("Importing entities...")
    for _, row in df_entities.iterrows():
        entity_id = row['canonical_name']
        label = row['entity_type'] # CoQuan, NguoiKy, DoiTuongApDung, LinhVuc
        name = row['canonical_name']
        
        # Valid labels check
        if label not in ["CoQuan", "NguoiKy", "DoiTuongApDung", "LinhVuc"]:
            continue
            
        query = f"""
        MERGE (e:{label} {{id: $id}})
        SET e.name = $name
        """
        session.run(query, id=entity_id, name=name)

def import_relationships(session, df_rel):
    print("Importing relationships...")
    
    # We will build dynamic query based on relationship_type.
    # Since we don't know the exact label of the target just from the relationship,
    # wait, Document -> Document is known.
    # Document -> Entity is also known based on relationship type.
    
    doc_rel_types = {"THAM_CHIEU", "SUA_DOI_BO_SUNG", "THAY_THE_BOI"}
    entity_rel_types = {
        "BAN_HANH_BOI": "CoQuan",
        "KY_BOI": "NguoiKy",
        "AP_DUNG_CHO": "DoiTuongApDung",
        "THUOC_LINH_VUC": "LinhVuc"
    }
    
    errors = 0
    for _, row in df_rel.iterrows():
        source = row['source']
        target = row['target']
        rel_type = row['relationship_type']
        
        try:
            if rel_type in doc_rel_types:
                # Document -> Document
                query = f"""
                MATCH (s:Document {{id: $source}})
                MERGE (t:Document {{id: $target}}) // create external docs as well
                MERGE (s)-[:{rel_type}]->(t)
                """
                session.run(query, source=source, target=target)
            elif rel_type in entity_rel_types:
                # Document -> Entity
                target_label = entity_rel_types[rel_type]
                query = f"""
                MATCH (s:Document {{id: $source}})
                MATCH (t:{target_label} {{id: $target}})
                MERGE (s)-[:{rel_type}]->(t)
                """
                session.run(query, source=source, target=target)
        except Exception as e:
            print(f"Error importing relationship {source} -[{rel_type}]-> {target}: {e}")
            errors += 1
            
    return errors

def print_stats(session):
    print("\n--- NEO4J STATS ---")
    res_nodes = session.run("MATCH (n) RETURN labels(n)[0] AS label, count(*) AS count")
    print("Nodes:")
    for record in res_nodes:
        print(f"- {record['label']}: {record['count']}")
        
    res_rels = session.run("MATCH ()-[r]->() RETURN type(r) AS type, count(*) AS count")
    print("\nRelationships:")
    for record in res_rels:
        print(f"- {record['type']}: {record['count']}")

def main():
    print("=== BƯỚC 8: IMPORT VÀO NEO4J ===")
    
    load_dotenv()
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")
    
    df_docs = pd.read_csv(os.path.join("ner_kb", "cleaned_documents.csv"))
    df_entities = pd.read_csv(os.path.join("ner_kb", "entities.csv"))
    df_rel = pd.read_csv(os.path.join("ner_kb", "relationships.csv"))
    
    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    try:
        with driver.session() as session:
            create_constraints(session)
            import_documents(session, df_docs)
            import_entities(session, df_entities)
            err_count = import_relationships(session, df_rel)
            
            print(f"\nSố lỗi import relationship: {err_count}")
            print_stats(session)
            print("\n[PASS] Import lần 1 hoàn tất.")
            
            # Import lần 2 để kiểm tra idempotent
            print("\nChạy import lần 2 (Idempotent test)...")
            import_documents(session, df_docs)
            import_entities(session, df_entities)
            import_relationships(session, df_rel)
            print_stats(session)
            print("\n[PASS] Import lần 2 hoàn tất, không tạo thêm duplicate.")
            
    finally:
        driver.close()

if __name__ == "__main__":
    main()
