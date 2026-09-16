PRAGMA foreign_keys=ON;

ALTER TABLE issuers ADD COLUMN canonical_issuer_id TEXT;

CREATE TABLE canonical_issuers(
 canonical_issuer_id TEXT PRIMARY KEY,
 status TEXT NOT NULL CHECK(status IN('ACTIVE','QUARANTINED','SUPERSEDED')),
 created_at TEXT NOT NULL
);
UPDATE issuers SET canonical_issuer_id=lower(hex(randomblob(16))) WHERE canonical_issuer_id IS NULL;
INSERT INTO canonical_issuers(canonical_issuer_id,status,created_at)
 SELECT canonical_issuer_id,'ACTIVE',created_at FROM issuers;
CREATE UNIQUE INDEX issuers_canonical_identity ON issuers(canonical_issuer_id);

CREATE TABLE issuer_identity_migrations(
 migration_id TEXT PRIMARY KEY,
 old_issuer_id TEXT NOT NULL UNIQUE REFERENCES issuers,
 new_canonical_issuer_id TEXT NOT NULL UNIQUE REFERENCES canonical_issuers,
 migration_basis TEXT NOT NULL,
 source_record_ids_json TEXT NOT NULL,
 migrated_at TEXT NOT NULL
);
INSERT INTO issuer_identity_migrations
 SELECT lower(hex(randomblob(16))),issuer_id,canonical_issuer_id,
 'ONE_TO_ONE_OPAQUE_CANONICALIZATION_PRESERVING_LEGACY_FOREIGN_KEYS','[]',datetime('now')
 FROM issuers;

CREATE TABLE effective_identifier_evidence(
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
INSERT OR IGNORE INTO effective_identifier_evidence
 SELECT lower(hex(randomblob(16))),'SECURITY',i.canonical_issuer_id,h.security_id,
 h.identifier_type,h.identifier_value,h.valid_from,h.valid_to,h.known_at,r.source_id,h.document_id,
 'MEDIUM','VERIFIED'
 FROM identifier_history h JOIN securities s USING(security_id)
 JOIN issuers i ON i.issuer_id=s.issuer_id JOIN raw_documents r ON r.document_id=h.document_id
 WHERE h.entity_type='SECURITY';

CREATE TABLE identity_resolution_conflicts(
 conflict_id TEXT PRIMARY KEY,
 conflict_type TEXT NOT NULL,
 identifier_type TEXT,
 identifier_value TEXT,
 observation_date TEXT,
 candidate_ids_json TEXT NOT NULL,
 evidence_json TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN('UNRESOLVED','RESOLVED','REJECTED')),
 created_at TEXT NOT NULL
);

CREATE TABLE financial_document_identity_assignments(
 assignment_id TEXT PRIMARY KEY,
 document_id TEXT NOT NULL UNIQUE REFERENCES financial_documents,
 canonical_issuer_id TEXT REFERENCES canonical_issuers,
 security_id TEXT REFERENCES securities,
 publication_date TEXT NOT NULL,
 assignment_status TEXT NOT NULL CHECK(assignment_status IN('VERIFIED','IDENTITY_UNRESOLVED','IDENTITY_CONFLICT','IDENTIFIER_OUT_OF_RANGE','QUARANTINED')),
 assignment_method TEXT NOT NULL,
 evidence_json TEXT NOT NULL,
 assigned_at TEXT NOT NULL
);

CREATE TABLE identity_contamination_audit(
 audit_id TEXT PRIMARY KEY,
 table_name TEXT NOT NULL,
 record_id TEXT NOT NULL,
 old_issuer_id TEXT,
 canonical_issuer_id TEXT,
 determination TEXT NOT NULL CHECK(determination IN('CORRECT','AMBIGUOUS','MISASSIGNED','REQUIRES_RECOMPUTATION')),
 reason TEXT NOT NULL,
 audited_at TEXT NOT NULL,
 UNIQUE(table_name,record_id)
);
