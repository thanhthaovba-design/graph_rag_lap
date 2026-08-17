import os
import shutil
from pathlib import Path

def prepare_corpus():
    source_path = Path("C:/graph_rag_labs/buoi_13/data/processed/chunks_normalized.csv")
    dest_dir = Path("C:/graph_rag_labs/buoi_14/data/processed")
    dest_path = dest_dir / "chunks_normalized.csv"

    if not source_path.exists():
        print(f"Lỗi: Không tìm thấy file nguồn tại {source_path}")
        return
    
    dest_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, dest_path)
    print(f"Đã sao chép corpus thành công tới {dest_path}")

if __name__ == "__main__":
    prepare_corpus()
