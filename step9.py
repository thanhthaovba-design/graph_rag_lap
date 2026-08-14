import os
import sys
from dotenv import load_dotenv
from neo4j import GraphDatabase

sys.stdout.reconfigure(encoding='utf-8')

def main():
    print("=== BƯỚC 9: KIỂM TRA & QUERY GRAPH TRÊN NEO4J ===")
    
    load_dotenv()
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")
    
    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    try:
        with driver.session() as session:
            # 1. Node count theo label
            print("\n1. Node count theo label:")
            res = session.run("MATCH (n) RETURN labels(n)[0] AS label, count(*) AS count ORDER BY count DESC")
            for r in res:
                if r['label'] in ['Document', 'CoQuan', 'NguoiKy', 'DoiTuongApDung', 'LinhVuc']:
                    print(f"   - {r['label']}: {r['count']}")
                    
            # 2. Relationship count theo type
            print("\n2. Relationship count theo type:")
            res = session.run("MATCH ()-[r]->() RETURN type(r) AS type, count(*) AS count ORDER BY count DESC")
            for r in res:
                if r['type'] in ['THAM_CHIEU', 'SUA_DOI_BO_SUNG', 'THAY_THE_BOI', 'BAN_HANH_BOI', 'KY_BOI', 'AP_DUNG_CHO', 'THUOC_LINH_VUC']:
                    print(f"   - {r['type']}: {r['count']}")
                    
            # 3. Document -> NguoiKy
            print("\n3. Mẫu Document -> NguoiKy:")
            res = session.run("MATCH (d:Document)-[:KY_BOI]->(p:NguoiKy) RETURN d.id AS doc_id, p.name AS person LIMIT 3")
            for r in res:
                print(f"   - {r['doc_id']} KÝ BỞI {r['person']}")
                
            # 4. Document -> DoiTuongApDung
            print("\n4. Mẫu Document -> DoiTuongApDung:")
            res = session.run("MATCH (d:Document)-[:AP_DUNG_CHO]->(o:DoiTuongApDung) RETURN d.id AS doc_id, o.name AS obj LIMIT 3")
            for r in res:
                print(f"   - {r['doc_id']} ÁP DỤNG CHO {r['obj']}")
                
            # 5. Document -> Document relations
            print("\n5. Mẫu Document -> Document relations:")
            res = session.run("MATCH (d1:Document)-[r:THAM_CHIEU|SUA_DOI_BO_SUNG|THAY_THE_BOI]->(d2:Document) RETURN d1.id AS source, type(r) AS rel, d2.id AS target LIMIT 5")
            for r in res:
                print(f"   - {r['source']} -[{r['rel']}]-> {r['target']}")
                
            print("\n[PASS] Mọi thứ đã hoàn tất thành công!")
            
    finally:
        driver.close()

if __name__ == "__main__":
    main()
