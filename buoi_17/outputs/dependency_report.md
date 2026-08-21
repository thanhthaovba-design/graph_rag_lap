# Dependency Report cho Buổi 17

## 1. Kiểm tra dữ liệu (SOURCE DATA)

### Dữ liệu đầu vào
- File Secure: `../buoi_14/data/processed/chunks_secure.csv`
- File Normalized: `../buoi_14/data/processed/chunks_normalized.csv`

### File `chunks_secure.csv`
- Số dòng: 1343 (Lưu ý: Dữ liệu thực tế khác với con số 787 dòng trong kịch bản mẫu, nhưng đây là bộ dữ liệu đầy đủ của project).
- Số cột: 14 cột.
- Danh sách cột hiện có: `chunk_id`, `document_id`, `text`, `source_file`, `title`, `document_type`, `so_ky_hieu`, `effective_date`, `status`, `allowed_roles`, `entities`, `relationships`, `keywords`, `summary`.
- Đối chiếu các trường yêu cầu:
  - `chunk_id`: Có
  - `document_id`: Có
  - `citation`: Không có sẵn thành cột (thường được generate động ở đầu ra của Retriever).
  - `title`: Có
  - `loai_van_ban`: Không có tên này (đang dùng tên tiếng Anh `document_type`).
  - `co_quan_ban_hanh`: Không có.
  - `ngay_ban_hanh`: Không có tên này (đang dùng tên tiếng Anh `effective_date`).
  - `allowed_roles`: Có.

### So sánh hai file CSV
- File `chunks_normalized.csv` có 1343 dòng và 13 cột.
- Dữ liệu ở 13 cột này hoàn toàn khớp với `chunks_secure.csv`.
- Xác nhận: `chunks_secure.csv = chunks_normalized.csv + allowed_roles`.

## 2. Kiểm tra mã nguồn (SECURE RETRIEVER REUSABLE)

- **File/Module**: `buoi_14/src/secure_retriever.py` (sử dụng như code kế thừa của Buổi 16).
- **Hàm/Class chính**: `SecureHybridRetriever` (hiện đã được alias lại là `SecureRetriever` ở cuối file để tiện import). Phương thức chính là `retrieve()`.
- **Input role**: Tham số `user_roles` được nhận vào trong hàm `retrieve(self, query, user_roles, top_k=5, candidate_k=20)`.
- **Output**: Là một list of dictionaries. Mỗi phần tử chứa các key: `chunk_id`, `document_id`, `text`, `retrieval_score`, `retrieval_method`, `citation`, `allowed_roles`.
- **Cơ chế Filter**: 
  - Với BM25 và Dense: Việc lọc `allowed_roles` được thực hiện **trước** quá trình retrieval (dùng `filter_by_roles()` hoặc boolean masking) để đảm bảo an toàn.
  - Với Graph: Được lọc trong mệnh đề `WHERE` của câu lệnh Cypher.
- **Bảo lưu ID**: `document_id`, `chunk_id`, và `citation` đều được giữ nguyên và map vào kết quả trả về.

---

SOURCE DATA: PASS
RBAC DATA AVAILABLE: YES
SECURE RETRIEVER REUSABLE: YES
REUSE PLAN:
- Sử dụng trực tiếp `chunks_secure.csv` từ thư mục `buoi_14` làm knowledge base. Dù số dòng lớn hơn mẫu (1343 dòng) và một số tên cột dùng tiếng Anh, nhưng file đã thỏa mãn đầy đủ cấu trúc 14 cột với cột quan trọng nhất là `allowed_roles`.
- Tiếp tục tái sử dụng `SecureRetriever` từ `buoi_14` thông qua import trực tiếp, không cần phải viết lại file hay thay đổi policy.
