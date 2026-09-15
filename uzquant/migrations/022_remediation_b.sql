CREATE TABLE financial_document_entity_checks(
 document_id TEXT PRIMARY KEY REFERENCES financial_documents,
 expected_issuer_id TEXT NOT NULL REFERENCES issuers,
 observed_entity TEXT,
 observed_tickers_json TEXT NOT NULL,
 validation_status TEXT NOT NULL CHECK(validation_status IN('MATCHED','MISMATCH','UNVERIFIED')),
 reason TEXT NOT NULL,
 checked_at TEXT NOT NULL
);
CREATE TABLE financial_document_metadata_evidence(
 evidence_id TEXT PRIMARY KEY, document_id TEXT NOT NULL REFERENCES financial_documents,
 field_name TEXT NOT NULL, field_value TEXT NOT NULL,
 confidence TEXT NOT NULL CHECK(confidence IN('HIGH','MEDIUM','LOW')),
 source_document_id TEXT REFERENCES raw_documents, source_url TEXT NOT NULL,
 source_location TEXT NOT NULL, parser_version TEXT NOT NULL, created_at TEXT NOT NULL,
 UNIQUE(document_id,field_name,source_url,source_location)
);
CREATE TABLE valuation_model_attempts(
 attempt_id TEXT PRIMARY KEY, security_id TEXT NOT NULL REFERENCES securities,
 valuation_date TEXT NOT NULL, model_name TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN('EXECUTED','REJECTED')),
 missing_inputs_json TEXT NOT NULL, failed_validations_json TEXT NOT NULL,
 reason TEXT NOT NULL, source_record_ids_json TEXT NOT NULL,
 model_version TEXT NOT NULL, created_at TEXT NOT NULL,
 UNIQUE(security_id,valuation_date,model_name,model_version)
);
CREATE INDEX valuation_model_attempts_pit ON valuation_model_attempts(security_id,valuation_date);
