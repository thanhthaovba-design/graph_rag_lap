import sys
import os
import importlib

def check_env():
    print("=== STEP 0: ENVIRONMENT CHECK ===")
    
    # 1. Python version
    print(f"Python version: {sys.version.split(' ')[0]}")
    print("[PASS] Python")
    
    # 2. Virtual environment
    is_venv = (hasattr(sys, 'real_prefix') or 
               (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix))
    if is_venv:
        print("[PASS] Virtual environment")
    else:
        print("[FAIL] Virtual environment (Not in venv)")
        
    # 3. Files
    metadata_path = os.path.join("ner_kb", "metadata.csv")
    content_path = os.path.join("ner_kb", "content.csv")
    
    if os.path.exists(metadata_path):
        print("[PASS] metadata.csv")
    else:
        print("[FAIL] metadata.csv missing")
        
    if os.path.exists(content_path):
        print("[PASS] content.csv")
    else:
        print("[FAIL] content.csv missing")
        
    # 4. Packages
    packages = ["pandas", "bs4", "dotenv", "google.genai", "neo4j"]
    all_packages_pass = True
    for pkg in packages:
        try:
            importlib.import_module(pkg)
        except ImportError:
            print(f"[FAIL] Package missing: {pkg}")
            all_packages_pass = False
            
    if all_packages_pass:
        print("[PASS] Python packages")
    else:
        print("[FAIL] Python packages")
        
    # 5. .env
    env_path = ".env"
    if os.path.exists(env_path):
        print("[PASS] .env file exists")
    else:
        print("[FAIL] .env file missing (Created .env.example, please copy to .env and configure)")
        
    # 6. Gemini and Neo4j Config
    if os.path.exists(env_path):
        from dotenv import load_dotenv
        load_dotenv(env_path)
        if os.getenv("GEMINI_API_KEY"):
            print("[PASS] Gemini configuration")
        else:
            print("[FAIL] Gemini configuration (GEMINI_API_KEY missing)")
            
        if os.getenv("NEO4J_URI") and os.getenv("NEO4J_USER") and os.getenv("NEO4J_PASSWORD"):
            print("[PASS] Neo4j configuration")
            if "neo4j" in sys.modules:
                from neo4j import GraphDatabase
                try:
                    driver = GraphDatabase.driver(
                        os.getenv("NEO4J_URI"),
                        auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
                    )
                    driver.verify_connectivity()
                    print("[PASS] Neo4j connection verified")
                    driver.close()
                except Exception as e:
                    print(f"[FAIL] Neo4j connection: {e}")
        else:
            print("[FAIL] Neo4j configuration")
    else:
        print("[FAIL] Gemini configuration (missing .env)")
        print("[FAIL] Neo4j configuration (missing .env)")

if __name__ == "__main__":
    check_env()
