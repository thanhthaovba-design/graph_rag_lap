# Wiki Risk Graph Project

Dự án này giúp chuẩn hóa dữ liệu rủi ro từ CSV để tạo ra một hệ thống Wiki (Markdown) cho Obsidian và nạp vào Neo4j làm Knowledge Graph phục vụ Graph RAG.

## Luồng thực hiện (Hướng dẫn chạy code)

Chạy các lệnh sau theo đúng thứ tự từ thư mục gốc `buoi_13/`:

1. **Kiểm tra dữ liệu gốc**:
   ```bash
   python scripts/inspect_data.py
   ```
2. **Chuẩn hóa dữ liệu thành Node và Edge**:
   ```bash
   python scripts/build_entities.py
   ```
3. **Sinh trang Wiki Markdown**:
   ```bash
   python scripts/build_wiki.py
   ```
4. **Kiểm tra (Validate) hệ thống Wiki**:
   ```bash
   python scripts/validate_wiki.py
   ```
5. **Nạp dữ liệu vào Neo4j**:
   ```bash
   python scripts/load_neo4j.py
   ```

## Cấu hình Neo4j
Để chạy được bước nạp dữ liệu (Bước 5), bạn cần tạo file `.env` tại thư mục gốc với các thông tin kết nối tới Neo4j:
```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password_here
NEO4J_DATABASE=neo4j
```

Các query Cypher mẫu có thể xem tại thư mục `cypher/demo_queries.cypher`.
