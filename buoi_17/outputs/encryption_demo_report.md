# Báo cáo Demo Encryption cục bộ

## 1. Mục tiêu
Minh họa kỹ thuật bảo vệ dữ liệu at-rest (mã hóa tập tin audit log) bằng thư viện `cryptography.fernet`. Lưu ý đây chỉ là demo nhỏ cho mục đích học tập, không đủ tiêu chuẩn cho hệ thống Production thực tế.

## 2. Quá trình mã hóa
- **Key Generation**: 
  - Đã sử dụng `Fernet.generate_key()` để sinh ra khóa mã hóa ngẫu nhiên và lưu vào `buoi_17/outputs/audit.key`.
  - Khóa này hoàn toàn không hard-code trong mã nguồn, và file `.key` đã được đưa vào `.gitignore` để tránh bị lộ lên source control.
- **Encrypt**: 
  - Đầu vào là file `audit_log.jsonl` nguyên bản.
  - Sau khi mã hóa, đã sinh ra file `audit_log.jsonl.enc` có kích thước lớn hơn 0, minh chứng cho việc ghi thành công dữ liệu cyphertext.
- **Decrypt**: 
  - Khôi phục ngược lại từ `audit_log.jsonl.enc` sử dụng lại đúng key đó.
  - File giải mã được lưu thành `audit_log.jsonl.dec`.
  - Dữ liệu hoàn toàn không bị ảnh hưởng, nguồn ban đầu của hệ thống vẫn được giữ nguyên.

## 3. So khớp (Match)
Đã thực hiện đọc nhị phân (binary read) hai file `audit_log.jsonl` gốc và `audit_log.jsonl.dec` sau giải mã, kết quả hoàn toàn trùng khớp 100% từng byte.

---

ENCRYPT: PASS
DECRYPT MATCH: PASS
PRODUCTION READY: NO

> [!WARNING]
> Giải thích thêm: Đối với một hệ thống Production thật sự, việc chỉ dùng Fernet cục bộ là không đủ. Hệ thống cần có TLS bảo vệ in-transit, Key Management System (KMS) chuyên nghiệp (như AWS KMS, Azure Key Vault), cơ chế rotation đổi key định kỳ, phân quyền (IAM) chặt chẽ và cơ chế backup khóa.
