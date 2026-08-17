// 1. Node tối thiểu
// :RuiRo, :KiemSoat, :SuKienRuiRo

// 2. Ràng buộc duy nhất (Unique constraints)
CREATE CONSTRAINT ruiro_id IF NOT EXISTS FOR (r:RuiRo) REQUIRE r.id IS UNIQUE;
CREATE CONSTRAINT kiemsoat_id IF NOT EXISTS FOR (k:KiemSoat) REQUIRE k.id IS UNIQUE;
CREATE CONSTRAINT sukien_id IF NOT EXISTS FOR (s:SuKienRuiRo) REQUIRE s.id IS UNIQUE;
