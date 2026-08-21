import os
from cryptography.fernet import Fernet

def generate_key(key_path):
    key = Fernet.generate_key()
    with open(key_path, "wb") as key_file:
        key_file.write(key)
    return key

def load_key(key_path):
    return open(key_path, "rb").read()

def encrypt_file(file_path, key, output_path):
    f = Fernet(key)
    with open(file_path, "rb") as file:
        file_data = file.read()
    encrypted_data = f.encrypt(file_data)
    with open(output_path, "wb") as file:
        file.write(encrypted_data)

def decrypt_file(file_path, key, output_path):
    f = Fernet(key)
    with open(file_path, "rb") as file:
        encrypted_data = file.read()
    decrypted_data = f.decrypt(encrypted_data)
    with open(output_path, "wb") as file:
        file.write(decrypted_data)

def main():
    original_file = "../outputs/audit_log.jsonl"
    encrypted_file = "../outputs/audit_log.jsonl.enc"
    decrypted_file = "../outputs/audit_log.jsonl.dec"
    key_file = "../outputs/audit.key"

    # 1. Generate/Load Key (Not hardcoded)
    if not os.path.exists(key_file):
        print(f"Generating new key at {key_file}...")
        key = generate_key(key_file)
    else:
        print(f"Loading existing key from {key_file}...")
        key = load_key(key_file)

    # 2. Encrypt
    print(f"Encrypting {original_file}...")
    encrypt_file(original_file, key, encrypted_file)
    encrypt_success = os.path.exists(encrypted_file) and os.path.getsize(encrypted_file) > 0

    # 3. Decrypt
    print(f"Decrypting {encrypted_file}...")
    decrypt_file(encrypted_file, key, decrypted_file)

    # 4. Compare
    with open(original_file, "rb") as f1, open(decrypted_file, "rb") as f2:
        original_data = f1.read()
        decrypted_data = f2.read()
    
    match_success = (original_data == decrypted_data)
    
    print("\n--- RESULTS ---")
    print(f"ENCRYPT: {'PASS' if encrypt_success else 'FAIL'}")
    print(f"DECRYPT MATCH: {'PASS' if match_success else 'FAIL'}")
    print("PRODUCTION READY: NO")
    
if __name__ == "__main__":
    # execute in scripts/ folder
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    main()
