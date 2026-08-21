# Báo cáo tái sử dụng RBAC cho Buổi 17

## 1. Phân tích `allowed_roles` từ Data 

Đã tiến hành chạy kiểm tra toàn bộ 1343 chunks trên file `chunks_secure.csv`.
- **Danh sách Role hiện có**: `['Admin', 'Risk_Manager', 'Staff', 'HR', 'Guest']`
- **Số chunk cho từng Role**:
  - `Admin`: 1343 chunks (có quyền truy cập toàn bộ)
  - `Risk_Manager`: 1237 chunks
  - `Staff`: 1237 chunks
  - `HR`: 834 chunks
  - `Guest`: 728 chunks
- **Số chunk chia sẻ cho nhiều Role**: 1343 (Tất cả các chunk đều được phân quyền cho nhiều hơn 1 role).
- **Số chunk bị hạn chế quyền**: 615 chunk (Không cấp quyền cho toàn bộ 5 role).
- **Tính ổn định của format**: Parse JSON list ổn định, 0 lỗi (`Parse errors: 0`).
- **Xử lý Role lạ (Unknown Role)**: Retriever trả về 0 chunks khi nhập vào một role không tồn tại.

## 2. Kiểm tra `SecureRetriever` của Buổi 16

Đã chạy test khởi tạo và query thử với class `SecureRetriever` (thực chất là `SecureHybridRetriever` sử dụng BM25 + Dense).
- Có đọc `allowed_roles`: Hàm `filter_by_roles` (với BM25) và `access_mask` (với Dense) đảm nhiệm parse và kiểm tra quyền.
- Loại chunk không được phép **TRƯỚC** retrieval:
  - BM25: Dữ liệu được lọc thành `df = filter_by_roles(self.full_df, user_roles)` ngay đầu hàm `retrieve`. Sau đó mới tokenize trên corpus đã lọc.
  - Dense: Dùng boolean `access_mask` lọc trên cả `full_df` và `corpus_embeddings` trước khi tính cosine_similarity. Do đó chunk không có quyền bị loại bỏ khỏi context và vector space trước khi rank, tiết kiệm tính toán và an toàn tuyệt đối.

### Thử nghiệm thực tế

Khi chạy từ khóa `"quy định"` (top_k=3) với các role:
- `Admin`: Trả về 3 chunks
- `HR`: Trả về 3 chunks
- `Risk_Manager`: Trả về 3 chunks
- `Staff`: Trả về 3 chunks
- `Guest`: Trả về 3 chunks
- `Unknown_Role`: Trả về 0 chunks (Không vượt qua được bước access mask/filter_by_roles).

---

RBAC REUSED: YES
FILTER BEFORE RETRIEVAL: PASS
UNKNOWN ROLE DEFAULT DENY: PASS
