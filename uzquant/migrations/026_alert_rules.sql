CREATE TABLE alert_rules(
 alert_type TEXT PRIMARY KEY,
 enabled INTEGER NOT NULL CHECK(enabled IN(0,1)),
 minimum_severity TEXT NOT NULL CHECK(minimum_severity IN('INFO','WARNING','HIGH','CRITICAL')),
 updated_at TEXT NOT NULL
);
