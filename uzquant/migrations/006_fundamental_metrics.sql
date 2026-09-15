CREATE TABLE fundamental_metrics(
 metric_id TEXT PRIMARY KEY,issuer_id TEXT NOT NULL REFERENCES issuers,
 document_id TEXT NOT NULL REFERENCES financial_documents,metric_name TEXT NOT NULL,
 sector_engine TEXT NOT NULL,period_start TEXT,period_end TEXT NOT NULL,
 comparison_horizon TEXT NOT NULL DEFAULT 'CURRENT',metric_value TEXT,metric_currency TEXT,metric_unit TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN('AVAILABLE','UNAVAILABLE')),
 unavailable_reason TEXT,formula_version TEXT NOT NULL,source_observation_ids_json TEXT NOT NULL,
 source_document_ids_json TEXT NOT NULL,created_at TEXT NOT NULL,
 UNIQUE(document_id,metric_name,comparison_horizon,formula_version));
CREATE INDEX fundamental_metrics_lookup ON fundamental_metrics(issuer_id,metric_name,period_end);
CREATE TABLE accounting_quality_flags(
 flag_id TEXT PRIMARY KEY,issuer_id TEXT NOT NULL REFERENCES issuers,
 document_id TEXT NOT NULL REFERENCES financial_documents,flag_name TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN('TRIGGERED','NOT_TRIGGERED','UNAVAILABLE')),
 evidence_json TEXT NOT NULL,formula_version TEXT NOT NULL,created_at TEXT NOT NULL,
 UNIQUE(document_id,flag_name,formula_version));
