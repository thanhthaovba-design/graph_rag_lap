// A. Xem toàn bộ graph
MATCH (n)
OPTIONAL MATCH (n)-[r]->(m)
RETURN n, r, m;

// B. Tìm kiểm soát giảm thiểu một rủi ro (Ví dụ: RR-001)
MATCH (k:KiemSoat)-[r:MITIGATES]->(ru:RuiRo {id: 'RR-001'})
RETURN k, r, ru;

// C. Tìm sự kiện của một rủi ro (Ví dụ: RR-001)
MATCH (ru:RuiRo {id: 'RR-001'})-[r:OBSERVED_AS]->(s:SuKienRuiRo)
RETURN ru, r, s;

// D. Tìm đường: KiemSoat -> RuiRo -> SuKienRuiRo
MATCH path = (k:KiemSoat)-[:MITIGATES]->(ru:RuiRo)-[:OBSERVED_AS]->(s:SuKienRuiRo)
RETURN path;

// E. Tìm rủi ro không có kiểm soát
MATCH (ru:RuiRo)
WHERE NOT ()-[:MITIGATES]->(ru)
RETURN ru;

// F. Tìm relation chưa VERIFIED
MATCH ()-[r]->()
WHERE r.verification_status <> 'VERIFIED' OR r.verification_status IS NULL
RETURN r;
