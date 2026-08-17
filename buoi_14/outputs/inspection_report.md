# Data Inspection Report

## ../../kb+hops/metadata.csv
- **Rows:** 15
- **Encoding:** utf-8
- **Columns:** id, title, so_ky_hieu, ngay_ban_hanh, loai_van_ban, ngay_co_hieu_luc, ngay_het_hieu_luc, nguon_thu_thap, ngay_dang_cong_bao, nganh, linh_vuc, co_quan_ban_hanh, chuc_danh, nguoi_ky, pham_vi, thong_tin_ap_dung, tinh_trang_hieu_luc
- **Duplicates:** 0
- **Nulls:**
  - id: 0
  - title: 0
  - so_ky_hieu: 0
  - ngay_ban_hanh: 0
  - loai_van_ban: 0
  - ngay_co_hieu_luc: 1
  - ngay_het_hieu_luc: 14
  - nguon_thu_thap: 5
  - ngay_dang_cong_bao: 11
  - nganh: 3
  - linh_vuc: 2
  - co_quan_ban_hanh: 0
  - chuc_danh: 0
  - nguoi_ky: 0
  - pham_vi: 0
  - thong_tin_ap_dung: 15
  - tinh_trang_hieu_luc: 0

- **Possible Keys:** id
- **Suitable metadata for citation:** title, so_ky_hieu, ngay_ban_hanh, loai_van_ban, ngay_co_hieu_luc, ngay_het_hieu_luc, nguon_thu_thap, ngay_dang_cong_bao, nganh, linh_vuc, co_quan_ban_hanh, chuc_danh, nguoi_ky, pham_vi, thong_tin_ap_dung, tinh_trang_hieu_luc

---
## ../../kb+hops/content.csv
- **Rows:** 15
- **Encoding:** utf-8
- **Columns:** id, content_html
- **Duplicates:** 0
- **Nulls:**
  - id: 0
  - content_html: 0

- **Possible Keys:** id
- **Suitable text for retrieval:** content_html

---
## ../../kb+hops/relationships.csv
- **Rows:** 8
- **Encoding:** utf-8
- **Columns:** doc_id, other_doc_id, relationship, relationship_type
- **Duplicates:** 0
- **Nulls:**
  - doc_id: 0
  - other_doc_id: 0
  - relationship: 0
  - relationship_type: 0

- **Possible Keys:** doc_id, other_doc_id

---
