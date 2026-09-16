PRAGMA foreign_keys=ON;

INSERT OR IGNORE INTO effective_identifier_evidence
 SELECT lower(hex(randomblob(16))),'ISSUER',i.canonical_issuer_id,NULL,
 'LEGAL_NAME',n.name,n.valid_from,n.valid_to,n.known_at,r.source_id,n.document_id,
 'MEDIUM','CANDIDATE'
 FROM issuer_name_history n JOIN issuers i USING(issuer_id)
 JOIN raw_documents r ON r.document_id=n.document_id;

CREATE TABLE effective_security_attributes(
 attribute_evidence_id TEXT PRIMARY KEY,
 security_id TEXT NOT NULL REFERENCES securities,
 attribute_type TEXT NOT NULL CHECK(attribute_type IN('SECURITY_CLASS','LISTING_STATUS')),
 attribute_value TEXT NOT NULL,
 valid_from TEXT,
 valid_to TEXT,
 known_at TEXT NOT NULL,
 source_document_id TEXT NOT NULL REFERENCES raw_documents,
 confidence TEXT NOT NULL CHECK(confidence IN('HIGH','MEDIUM','LOW')),
 CHECK(valid_to IS NULL OR valid_from IS NULL OR valid_to>=valid_from),
 UNIQUE(security_id,attribute_type,attribute_value,known_at,source_document_id)
);
INSERT OR IGNORE INTO effective_security_attributes
 SELECT lower(hex(randomblob(16))),s.security_id,'SECURITY_CLASS',s.security_class_code,
 NULL,NULL,s.created_at,l.document_id,'MEDIUM'
 FROM securities s JOIN listings l ON l.security_id=s.security_id
 GROUP BY s.security_id;
INSERT OR IGNORE INTO effective_security_attributes
 SELECT lower(hex(randomblob(16))),l.security_id,'LISTING_STATUS',l.listing_status,
 l.listing_date,l.delisting_date,l.known_at,l.document_id,'MEDIUM'
 FROM listings l;

CREATE TABLE analytical_identity_invalidations(
 invalidation_id TEXT PRIMARY KEY,
 table_name TEXT NOT NULL,
 record_id TEXT NOT NULL,
 reason TEXT NOT NULL,
 source_document_id TEXT REFERENCES financial_documents,
 invalidated_at TEXT NOT NULL,
 superseded_by_record_id TEXT,
 UNIQUE(table_name,record_id,reason)
);
