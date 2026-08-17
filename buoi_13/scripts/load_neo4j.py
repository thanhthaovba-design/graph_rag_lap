import os
import pandas as pd
from neo4j import GraphDatabase
from dotenv import load_dotenv
import sys

def create_constraints(tx):
    tx.run("CREATE CONSTRAINT ruiro_id IF NOT EXISTS FOR (r:RuiRo) REQUIRE r.id IS UNIQUE")
    tx.run("CREATE CONSTRAINT kiemsoat_id IF NOT EXISTS FOR (k:KiemSoat) REQUIRE k.id IS UNIQUE")
    tx.run("CREATE CONSTRAINT sukien_id IF NOT EXISTS FOR (s:SuKienRuiRo) REQUIRE s.id IS UNIQUE")

def load_entities(tx, entities_path):
    df = pd.read_csv(entities_path).fillna("")
    
    # KiemSoat
    controls = df[df['type'] == 'KiemSoat'].to_dict('records')
    if controls:
        tx.run("""
            UNWIND $controls AS row
            MERGE (k:KiemSoat {id: row.id})
            SET k += row
        """, controls=controls)

    # RuiRo
    risks = df[df['type'] == 'RuiRo'].to_dict('records')
    if risks:
        tx.run("""
            UNWIND $risks AS row
            MERGE (r:RuiRo {id: row.id})
            SET r += row
        """, risks=risks)

    # SuKienRuiRo
    events = df[df['type'] == 'SuKienRuiRo'].to_dict('records')
    if events:
        tx.run("""
            UNWIND $events AS row
            MERGE (s:SuKienRuiRo {id: row.id})
            SET s += row
        """, events=events)

def load_relations(tx, relations_path):
    df = pd.read_csv(relations_path).fillna("")
    
    # MITIGATES
    mitigates = df[df['relationship_type'] == 'MITIGATES'].to_dict('records')
    if mitigates:
        tx.run("""
            UNWIND $mitigates AS rel
            MATCH (src:KiemSoat {id: rel.source_id})
            MATCH (tgt:RuiRo {id: rel.target_id})
            MERGE (src)-[r:MITIGATES]->(tgt)
            SET r += rel
        """, mitigates=mitigates)
    
    # OBSERVED_AS
    observed = df[df['relationship_type'] == 'OBSERVED_AS'].to_dict('records')
    if observed:
        tx.run("""
            UNWIND $observed AS rel
            MATCH (src:RuiRo {id: rel.source_id})
            MATCH (tgt:SuKienRuiRo {id: rel.target_id})
            MERGE (src)-[r:OBSERVED_AS]->(tgt)
            SET r += rel
        """, observed=observed)

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    load_dotenv()
    
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    database = os.getenv("NEO4J_DATABASE", "neo4j")
    
    if not password:
        print("Lỗi: Không tìm thấy cấu hình NEO4J_PASSWORD trong file .env.")
        print("Vui lòng tạo file .env và cấu hình (NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD) trước khi chạy.")
        print("Bỏ qua nạp dữ liệu vào Neo4j để không làm hỏng các bước trước.")
        return

    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        driver.verify_connectivity()
        print("Đã kết nối thành công tới Neo4j!")
    except Exception as e:
        print(f"Không thể kết nối tới Neo4j. Chi tiết lỗi: {e}")
        print("Vui lòng kiểm tra lại cấu hình hoặc chắc chắn Neo4j đang chạy.")
        return
        
    with driver.session(database=database) as session:
        print("Đang tạo Constraints...")
        session.execute_write(create_constraints)
        
        print("Đang nạp Entities...")
        session.execute_write(load_entities, "outputs/entities.csv")
        
        print("Đang nạp Relations...")
        session.execute_write(load_relations, "outputs/relations.csv")
        
    driver.close()
    print("Nạp dữ liệu vào Neo4j thành công!")

if __name__ == "__main__":
    main()
