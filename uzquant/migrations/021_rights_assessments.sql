CREATE TABLE security_rights_assessments(
 assessment_id TEXT PRIMARY KEY,
 security_id TEXT NOT NULL REFERENCES securities,
 as_of_date TEXT NOT NULL,
 classification TEXT NOT NULL CHECK(classification IN('RIGHTS_VERIFIED','RIGHTS_PARTIAL','RIGHTS_UNAVAILABLE')),
 reason TEXT NOT NULL,
 source_url TEXT,
 source_document_id TEXT REFERENCES raw_documents,
 source_provision TEXT,
 created_at TEXT NOT NULL,
 UNIQUE(security_id,as_of_date)
);

