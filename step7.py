import os
import sys
from dotenv import load_dotenv
from neo4j import GraphDatabase

sys.stdout.reconfigure(encoding='utf-8')

def main():
    print("=== BƯỚC 7: KIỂM TRA KẾT NỐI NEO4J ===")
    
    load_dotenv()
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")
    
    if not uri or not user or not password:
        print("[FAIL] Neo4j configuration is missing in .env")
        return
        
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        driver.verify_connectivity()
        print("[PASS] Mở driver thành công")
        print("[PASS] Neo4j connection: PASS")
        
        # Test a simple query
        with driver.session() as session:
            result = session.run("CALL db.info()")
            for record in result:
                pass # Just consume it to verify database is readable
        print("[PASS] Chạy query thành công")
        
        driver.close()
        print("[PASS] Đóng driver đúng cách")
        
    except Exception as e:
        print(f"[FAIL] Lỗi kết nối Neo4j: {e}")

if __name__ == "__main__":
    main()
