CREATE TABLE financial_documents(
 document_id TEXT PRIMARY KEY, issuer_id TEXT NOT NULL REFERENCES issuers,
 raw_document_id TEXT NOT NULL REFERENCES raw_documents, reporting_entity TEXT NOT NULL,
 reporting_perimeter TEXT NOT NULL CHECK(reporting_perimeter IN('CONSOLIDATED','STANDALONE','UNKNOWN')),
 period_start TEXT, period_end TEXT NOT NULL, publication_date TEXT NOT NULL,
 publication_timestamp TEXT, document_type TEXT NOT NULL, document_format TEXT NOT NULL,
 accounting_standard TEXT NOT NULL, audit_status TEXT NOT NULL,
 currency TEXT, source_id TEXT NOT NULL REFERENCES data_sources, source_url TEXT NOT NULL,
 source_identifier TEXT NOT NULL, retrieved_at TEXT NOT NULL, content_hash TEXT NOT NULL,
 parser_version TEXT NOT NULL, revision_status TEXT NOT NULL CHECK(revision_status IN('ORIGINAL','RESTATED','REVISED')),
 revises_document_id TEXT REFERENCES financial_documents, UNIQUE(source_id,source_identifier,content_hash));
CREATE INDEX financial_documents_pit ON financial_documents(issuer_id,period_end,publication_date);
CREATE TABLE financial_raw_values(
 raw_value_id TEXT PRIMARY KEY,document_id TEXT NOT NULL REFERENCES financial_documents,
 statement_type TEXT NOT NULL,raw_label TEXT NOT NULL,row_code TEXT,raw_value TEXT NOT NULL,
 comparative_label TEXT,source_location TEXT NOT NULL,extraction_method TEXT NOT NULL,
 UNIQUE(document_id,source_location));
CREATE TABLE financial_observations(
 observation_id TEXT PRIMARY KEY,document_id TEXT NOT NULL REFERENCES financial_documents,
 issuer_id TEXT NOT NULL REFERENCES issuers,statement_type TEXT NOT NULL,canonical_concept TEXT NOT NULL,
 period_start TEXT,period_end TEXT NOT NULL,raw_value TEXT NOT NULL,normalized_value TEXT NOT NULL,
 currency TEXT,unit TEXT NOT NULL,sign_convention TEXT NOT NULL,source_location TEXT NOT NULL,
 extraction_method TEXT NOT NULL,confidence TEXT NOT NULL,value_status TEXT NOT NULL CHECK(value_status IN('REPORTED','DERIVED','ESTIMATED')),
 UNIQUE(document_id,canonical_concept,period_end,source_location));
CREATE INDEX financial_observations_pit ON financial_observations(issuer_id,canonical_concept,period_end);
CREATE TABLE financial_validation_issues(
 issue_id TEXT PRIMARY KEY,document_id TEXT NOT NULL REFERENCES financial_documents,
 issue_type TEXT NOT NULL,severity TEXT NOT NULL,details TEXT NOT NULL,created_at TEXT NOT NULL);
