---
id: RR-001
type: RuiRo
verification_status: VERIFIED
data_origin: SYNTHETIC
---
# Giao dịch chuyển tiền bị hạch toán sai

**ID**: RR-001
**Category**: Rui ro van hanh
**Owner Unit ID**: DV-OPS
**Inherent Level**: Cao
**Residual Level**: Trung binh

## Mô tả
Đối soát giao dịch cuối ngày không đầy đủ

## Nguyên nhân (Cause)
Thiếu đối chiếu giữa hệ thống thanh toán và sổ cái

## Sự kiện (Event)
Giao dịch được ghi nhận sai trạng thái

## Tác động (Impact)
Tổn thất tài chính và khiếu nại khách hàng

## Kiểm soát liên quan
- MITIGATES [[Đối soát tự động giao dịch và sổ cái]] (Evidence: Dữ liệu mô phỏng: đối soát tự động giảm nguy cơ hạch toán sai, Status: VERIFIED)

## Sự kiện liên quan
- OBSERVED_AS [[Sự kiện SK-001]] (Evidence: Dữ liệu mô phỏng: sự kiện đối soát giao dịch, Status: VERIFIED)
