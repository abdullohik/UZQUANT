CREATE TABLE share_capital_observations(
 observation_id TEXT PRIMARY KEY,
 issuer_id TEXT NOT NULL REFERENCES issuers,
 security_id TEXT REFERENCES securities,
 effective_date TEXT NOT NULL,
 disclosure_date TEXT NOT NULL,
 total_issuer_shares TEXT,
 class_shares_outstanding TEXT,
 nominal_value TEXT,
 currency TEXT,
 verification_status TEXT NOT NULL CHECK(verification_status IN('VERIFIED','PARTIAL','CONFLICT','UNAVAILABLE')),
 unavailable_reason TEXT,
 source_document_id TEXT REFERENCES raw_documents,
 source_url TEXT,
 source_provision TEXT,
 parser_version TEXT NOT NULL,
 created_at TEXT NOT NULL,
 UNIQUE(issuer_id,security_id,effective_date,source_url)
);
CREATE INDEX share_capital_pit ON share_capital_observations(security_id,disclosure_date,effective_date);

CREATE TABLE source_coverage_audits(
 audit_id TEXT PRIMARY KEY,
 source_id TEXT NOT NULL REFERENCES data_sources,
 dataset TEXT NOT NULL,
 attempted_at TEXT NOT NULL,
 requested_scope TEXT NOT NULL,
 retrieved_scope TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN('COMPLETE','PARTIAL','BLOCKED','UNAVAILABLE')),
 limitation TEXT,
 evidence_url TEXT,
 parser_version TEXT NOT NULL
);

