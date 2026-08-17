# Final Validation Report - Buổi 14

## Checklist nhanh trước khi kết thúc buổi

- [x] Terminal đang làm việc trong `buoi_14/`.
- [x] `.venv` của Buổi 14 hoạt động.
- [x] Không sửa code các buổi trước.
- [x] Corpus đã chuẩn hóa.
- [x] BM25 có kết quả.
- [x] Dense có kết quả.
- [x] Hybrid có `bm25_rank` và `dense_rank`.
- [x] Reranker nhận candidate từ Hybrid.
- [x] Có Before/After Rerank.
- [x] Citation không bị mất.
- [x] Có evaluation report.
- [x] Streamlit chạy được.
- [x] Streamlit chọn được 4 retrieval method.
- [x] Streamlit hiển thị citation.
- [x] Streamlit hiển thị Before/After Rerank.
- [x] Mini KG chỉ chứa quan hệ có nguồn.
- [x] Neo4j không bị xóa toàn bộ.
- [x] Dữ liệu graph có `lab_session = "buoi_14"`.
- [x] Final validation báo `READY FOR DEMO: YES`.

## Trạng thái
READY FOR DEMO: YES
Tất cả các module đã được triển khai, bạn có thể kiểm thử trực tiếp thông qua:
1. Streamlit App: `streamlit run app.py`
2. CLI Hybrid + Rerank: `python scripts/query_demo.py --query "Câu hỏi" --method hybrid_rerank --top-k 5`
3. Load KG: `python scripts/load_mini_kg.py`
4. Evaluation: `python scripts/compare_retrieval.py`
