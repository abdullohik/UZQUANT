PRAGMA foreign_keys=OFF;

CREATE TABLE effective_identifier_evidence_v2(
 evidence_id TEXT PRIMARY KEY,
 entity_type TEXT NOT NULL CHECK(entity_type IN('ISSUER','SECURITY')),
 canonical_issuer_id TEXT REFERENCES canonical_issuers,
 security_id TEXT REFERENCES securities,
 identifier_type TEXT NOT NULL,
 identifier_value TEXT NOT NULL,
 valid_from TEXT,
 valid_to TEXT,
 known_at TEXT NOT NULL,
 source_id TEXT NOT NULL REFERENCES data_sources,
 source_document_id TEXT REFERENCES raw_documents,
 confidence TEXT NOT NULL CHECK(confidence IN('HIGH','MEDIUM','LOW')),
 evidence_status TEXT NOT NULL CHECK(evidence_status IN('VERIFIED','CANDIDATE','REJECTED')),
 CHECK((entity_type='ISSUER' AND canonical_issuer_id IS NOT NULL AND security_id IS NULL) OR
       (entity_type='SECURITY' AND security_id IS NOT NULL)),
 CHECK(valid_to IS NULL OR valid_from IS NULL OR valid_to>=valid_from),
 UNIQUE(entity_type,canonical_issuer_id,security_id,identifier_type,identifier_value,known_at,source_document_id)
);
INSERT INTO effective_identifier_evidence_v2 SELECT * FROM effective_identifier_evidence;
DROP TABLE effective_identifier_evidence;
ALTER TABLE effective_identifier_evidence_v2 RENAME TO effective_identifier_evidence;

PRAGMA foreign_keys=ON;
