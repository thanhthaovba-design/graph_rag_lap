import os
import sys
import pandas as pd
from dotenv import load_dotenv

def check_env():
    print("--- CHECKING ENVIRONMENT BUOI 17 ---")
    print(f"Python version: {sys.version.split(' ')[0]}")
    print(f"Virtual env active: {sys.prefix != sys.base_prefix}")
    
    secure_csv = "../buoi_14/data/processed/chunks_secure.csv"
    normalized_csv = "../buoi_14/data/processed/chunks_normalized.csv"
    
    source_ready = True
    
    try:
        df_secure = pd.read_csv(secure_csv)
        print(f"chunks_secure.csv read success: {df_secure.shape}")
        if df_secure.shape[1] == 14 and 'allowed_roles' in df_secure.columns:
            print(" - chunks_secure.csv has 14 columns and allowed_roles.")
        else:
            print(f" - chunks_secure.csv has {df_secure.shape[1]} columns, allowed_roles: {'allowed_roles' in df_secure.columns}")
            source_ready = False
    except Exception as e:
        print(f"Error reading chunks_secure.csv: {e}")
        source_ready = False
        df_secure = None
        
    try:
        df_norm = pd.read_csv(normalized_csv)
        print(f"chunks_normalized.csv read success: {df_norm.shape}")
        if df_norm.shape[1] == 13:
            print(" - chunks_normalized.csv has exactly 13 columns.")
        else:
            print(f" - chunks_normalized.csv has {df_norm.shape[1]} columns.")
            source_ready = False
    except Exception as e:
        print(f"Error reading chunks_normalized.csv: {e}")
        source_ready = False
        df_norm = None

    if df_secure is not None and df_norm is not None:
        if df_secure.shape[0] == df_norm.shape[0]:
            print(f"Row count matches: {df_secure.shape[0]} rows.")
        else:
            print(f"Row count MISMATCH: secure={df_secure.shape[0]}, norm={df_norm.shape[0]}")
            source_ready = False

    env_path = ".env"
    env_ready = False
    if os.path.exists(env_path):
        load_dotenv(env_path)
        if os.getenv("GEMINI_API_KEY"):
            print(".env for buoi_17: Valid.")
            env_ready = True
        else:
            print(".env for buoi_17: Missing GEMINI_API_KEY.")
    else:
        print(".env for buoi_17: Not found.")

    secure_retriever_found = False
    sys.path.append(os.path.abspath("../buoi_14"))
    try:
        from src.secure_retriever import SecureRetriever
        print("SecureRetriever import successful.")
        secure_retriever_found = True
    except ImportError as e:
        print(f"SecureRetriever import error: {e}")
    except Exception as e:
        print(f"Other error importing SecureRetriever: {e}")
        
    print("\n--- RESULTS ---")
    print(f"ENVIRONMENT READY: {'YES' if env_ready else 'NO'}")
    print(f"SOURCE DATA READY: {'YES' if source_ready else 'NO'}")
    print(f"SECURE RETRIEVER FOUND: {'YES' if secure_retriever_found else 'NO'}")

if __name__ == '__main__':
    check_env()
