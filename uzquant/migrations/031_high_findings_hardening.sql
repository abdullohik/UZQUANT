PRAGMA foreign_keys=ON;

CREATE TABLE financial_observation_versions(
 version_id TEXT PRIMARY KEY,
 observation_id TEXT NOT NULL,
 document_id TEXT NOT NULL REFERENCES financial_documents,
 issuer_id TEXT NOT NULL REFERENCES issuers,
 raw_value_id TEXT REFERENCES financial_raw_values,
 canonical_concept TEXT NOT NULL,
 statement_type TEXT NOT NULL,
 period_start TEXT,
 period_end TEXT NOT NULL,
 publication_date TEXT NOT NULL,
 knowledge_date TEXT NOT NULL,
 raw_value TEXT NOT NULL,
 normalized_value TEXT NOT NULL,
 currency TEXT,
 unit TEXT NOT NULL,
 reporting_perimeter TEXT NOT NULL,
 accounting_standard TEXT NOT NULL,
 audit_status TEXT NOT NULL,
 extraction_method TEXT NOT NULL,
 parser_version TEXT NOT NULL,
 taxonomy_version TEXT NOT NULL,
 normalization_version TEXT NOT NULL,
 confidence TEXT NOT NULL,
 validation_state TEXT NOT NULL,
 value_status TEXT NOT NULL,
 source_location TEXT NOT NULL,
 created_at TEXT NOT NULL,
 supersedes_version_id TEXT REFERENCES financial_observation_versions,
 superseded_by_version_id TEXT REFERENCES financial_observation_versions,
 UNIQUE(document_id,canonical_concept,source_location,parser_version,taxonomy_version,normalization_version)
);
CREATE INDEX financial_observation_versions_pit ON financial_observation_versions(issuer_id,canonical_concept,period_end,knowledge_date);
INSERT INTO financial_observation_versions
 SELECT lower(hex(randomblob(16))),o.observation_id,o.document_id,o.issuer_id,
 (SELECT raw_value_id FROM financial_raw_values r WHERE r.document_id=o.document_id AND r.source_location=o.source_location LIMIT 1),
 o.canonical_concept,o.statement_type,o.period_start,o.period_end,d.publication_date,d.retrieved_at,
 o.raw_value,o.normalized_value,o.currency,o.unit,d.reporting_perimeter,d.accounting_standard,d.audit_status,
 o.extraction_method,d.parser_version,'legacy-taxonomy/unversioned','legacy-normalization/1',o.confidence,
 coalesce((SELECT validation_status FROM financial_document_entity_checks c WHERE c.document_id=o.document_id),'UNVERIFIED'),
 o.value_status,o.source_location,coalesce(d.retrieved_at,datetime('now')),NULL,NULL
 FROM financial_observations o JOIN financial_documents d USING(document_id);
CREATE TRIGGER financial_versions_no_delete BEFORE DELETE ON financial_observation_versions BEGIN SELECT RAISE(ABORT,'normalized financial versions are append-only'); END;
CREATE TRIGGER financial_versions_no_value_update BEFORE UPDATE OF normalized_value,raw_value,currency,unit,canonical_concept,document_id ON financial_observation_versions BEGIN SELECT RAISE(ABORT,'normalized financial values are immutable'); END;

CREATE TABLE analytical_observation_lineage(
 lineage_id TEXT PRIMARY KEY,
 analytical_table TEXT NOT NULL,
 analytical_record_id TEXT NOT NULL,
 observation_version_id TEXT NOT NULL REFERENCES financial_observation_versions,
 created_at TEXT NOT NULL,
 UNIQUE(analytical_table,analytical_record_id,observation_version_id)
);
CREATE TABLE signal_observation_lineage(
 signal_id TEXT NOT NULL REFERENCES research_signals,
 observation_version_id TEXT NOT NULL REFERENCES financial_observation_versions,
 lineage_status TEXT NOT NULL CHECK(lineage_status IN('EXACT','LEGACY_INFERRED')),
 created_at TEXT NOT NULL,
 PRIMARY KEY(signal_id,observation_version_id)
);

CREATE TABLE source_schema_contracts(
 contract_id TEXT PRIMARY KEY,
 pipeline TEXT NOT NULL,
 source_id TEXT NOT NULL,
 parser_version TEXT NOT NULL,
 contract_json TEXT NOT NULL,
 created_at TEXT NOT NULL,
 UNIQUE(pipeline,source_id,parser_version)
);
CREATE TABLE source_schema_checks(
 check_id TEXT PRIMARY KEY,
 contract_id TEXT NOT NULL REFERENCES source_schema_contracts,
 raw_document_id TEXT REFERENCES raw_documents,
 classification TEXT NOT NULL CHECK(classification IN('COSMETIC_CHANGE','COMPATIBLE_SCHEMA_CHANGE','BREAKING_SCHEMA_CHANGE')),
 observed_schema_json TEXT NOT NULL,
 differences_json TEXT NOT NULL,
 checked_at TEXT NOT NULL
);

CREATE TABLE prospective_snapshot_evidence(
 evidence_id TEXT PRIMARY KEY,
 prospective_snapshot_id TEXT NOT NULL UNIQUE REFERENCES prospective_decision_snapshots,
 standard TEXT NOT NULL CHECK(standard IN('FULL_FREEZE_V1','LEGACY_SNAPSHOT_LIMITED')),
 identity_payload_json TEXT NOT NULL,
 raw_documents_payload_json TEXT NOT NULL,
 normalized_financial_payload_json TEXT NOT NULL,
 fundamental_metrics_payload_json TEXT NOT NULL,
 valuation_payload_json TEXT NOT NULL,
 factor_payload_json TEXT NOT NULL,
 liquidity_payload_json TEXT NOT NULL,
 confidence_risk_payload_json TEXT NOT NULL,
 health_freshness_payload_json TEXT NOT NULL,
 portfolio_execution_payload_json TEXT NOT NULL,
 payload_sha256 TEXT NOT NULL,
 created_at TEXT NOT NULL
);
INSERT INTO prospective_snapshot_evidence
 SELECT lower(hex(randomblob(16))),prospective_snapshot_id,'LEGACY_SNAPSHOT_LIMITED','{}','{}','{}','{}','{}','{}','{}','{}',pipeline_health_json,portfolio_state_json,lower(hex(randomblob(32))),created_at
 FROM prospective_decision_snapshots;
CREATE TRIGGER snapshot_evidence_no_update BEFORE UPDATE ON prospective_snapshot_evidence BEGIN SELECT RAISE(ABORT,'prospective evidence is immutable'); END;
CREATE TRIGGER snapshot_evidence_no_delete BEFORE DELETE ON prospective_snapshot_evidence BEGIN SELECT RAISE(ABORT,'prospective evidence is immutable'); END;
