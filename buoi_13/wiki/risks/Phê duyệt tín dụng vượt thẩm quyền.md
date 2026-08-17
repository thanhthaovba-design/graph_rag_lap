---
id: RR-002
type: RuiRo
verification_status: VERIFIED
data_origin: SYNTHETIC
---
# Phê duyệt tín dụng vượt thẩm quyền

**ID**: RR-002
**Category**: Rui ro tin dung
**Owner Unit ID**: DV-CREDIT
**Inherent Level**: Cao
**Residual Level**: Trung binh

## Mô tả
Kiểm tra hạn mức phê duyệt không hiệu lực

## Nguyên nhân (Cause)
Phân quyền trên hệ thống không cập nhật

## Sự kiện (Event)
Khoản vay được phê duyệt vượt thẩm quyền

## Tác động (Impact)
Tăng nợ xấu và vi phạm quy định

## Kiểm soát liên quan
- MITIGATES [[Kiểm tra hạn mức phê duyệt trên hệ thống]] (Evidence: Dữ liệu mô phỏng: kiểm tra hạn mức ngăn phê duyệt vượt thẩm quyền, Status: VERIFIED)

## Sự kiện liên quan
- OBSERVED_AS [[Sự kiện SK-002]] (Evidence: Dữ liệu mô phỏng: sự kiện vượt thẩm quyền, Status: VERIFIED)
