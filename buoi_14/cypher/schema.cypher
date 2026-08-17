// Create constraints (if using Neo4j Enterprise, else use indexes)
CREATE INDEX IF NOT EXISTS FOR (v:VanBan) ON (v.id);
CREATE INDEX IF NOT EXISTS FOR (d:DieuKhoan) ON (d.id);
