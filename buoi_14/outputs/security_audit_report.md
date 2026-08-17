# Security Audit Report

**Mục tiêu**: Kiểm thử tính an toàn của hệ thống RAG RBAC.
**Số lượng Test Case**: 5

## Test Case 1
- **Query**: `Quy trình tuyển dụng và bổ nhiệm nhân sự cấp cao`
- **Unauthorized Roles**: `['Guest']`
- **Authorized Roles**: `['HR']`
- **Target Sensitive Doc ID**: `44209`
- **Result**: PASSED ✅
- **Evidence**: Unauthorized roles received 0 sensitive chunks.
## Test Case 2
- **Query**: `Quy định về lương thưởng và phụ cấp`
- **Unauthorized Roles**: `['Staff']`
- **Authorized Roles**: `['Admin']`
- **Target Sensitive Doc ID**: `166269`
- **Result**: PASSED ✅
- **Evidence**: Unauthorized roles received 0 sensitive chunks.
## Test Case 3
- **Query**: `Quy trình phê duyệt duyệt vay và hạn mức tín dụng`
- **Unauthorized Roles**: `['Guest']`
- **Authorized Roles**: `['Risk_Manager']`
- **Target Sensitive Doc ID**: `95652`
- **Result**: PASSED ✅
- **Evidence**: Unauthorized roles received 0 sensitive chunks.
## Test Case 4
- **Query**: `Đánh giá rủi ro tín dụng khách hàng doanh nghiệp`
- **Unauthorized Roles**: `['HR']`
- **Authorized Roles**: `['Staff']`
- **Target Sensitive Doc ID**: `117310`
- **Result**: PASSED ✅
- **Evidence**: Unauthorized roles received 0 sensitive chunks.
## Test Case 5
- **Query**: `Hồ sơ nhân sự và đánh giá hiệu suất nhân viên`
- **Unauthorized Roles**: `['Risk_Manager']`
- **Authorized Roles**: `['Admin']`
- **Target Sensitive Doc ID**: `163441`
- **Result**: PASSED ✅
- **Evidence**: Unauthorized roles received 0 sensitive chunks.

## Kết Luận
**Hệ thống ĐẠT CHỨNG NHẬN AN TOÀN DỮ LIỆU MỨC CƠ BẢN. ✅**