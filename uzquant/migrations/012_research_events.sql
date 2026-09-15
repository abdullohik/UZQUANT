CREATE TABLE research_events(
 event_id TEXT PRIMARY KEY,
 issuer_id TEXT NOT NULL REFERENCES issuers,
 publication_at TEXT NOT NULL,
 effective_date TEXT,
 event_type TEXT NOT NULL CHECK(event_type IN('DIVIDEND','PRIVATIZATION','STATE_STAKE_SALE','STRATEGIC_INVESTOR','ACQUISITION','MERGER','CAPITAL_INCREASE','BUYBACK','LARGE_CONTRACT','BORROWING','REFINANCING','MANAGEMENT_CHANGE','AUDITOR_CHANGE','RELATED_PARTY','LEGAL','REGULATORY','PRODUCTION_EXPANSION','ASSET_SALE','RESTRUCTURING','BANKRUPTCY','OTHER')),
 summary TEXT NOT NULL,
 materiality TEXT NOT NULL CHECK(materiality IN('LOW','MEDIUM','HIGH','UNKNOWN')),
 direction TEXT NOT NULL CHECK(direction IN('STRONG_NEGATIVE','NEGATIVE','NEUTRAL','POSITIVE','STRONG_POSITIVE')),
 time_horizon TEXT NOT NULL CHECK(time_horizon IN('IMMEDIATE','SHORT_TERM','MEDIUM_TERM','LONG_TERM','UNKNOWN')),
 confidence TEXT NOT NULL CHECK(confidence IN('LOW','MEDIUM','HIGH')),
 classification_method TEXT NOT NULL,
 model_version TEXT,
 prompt_version TEXT,
 canonical_key TEXT NOT NULL UNIQUE,
 created_at TEXT NOT NULL
);
CREATE INDEX research_events_pit ON research_events(issuer_id,publication_at,effective_date);

CREATE TABLE research_event_securities(
 event_id TEXT NOT NULL REFERENCES research_events ON DELETE CASCADE,
 security_id TEXT NOT NULL REFERENCES securities,
 PRIMARY KEY(event_id,security_id)
);

CREATE TABLE research_event_sources(
 event_source_id TEXT PRIMARY KEY,
 event_id TEXT NOT NULL REFERENCES research_events ON DELETE CASCADE,
 source_document_id TEXT NOT NULL REFERENCES raw_documents,
 source_record_type TEXT NOT NULL,
 source_record_id TEXT NOT NULL,
 source_url TEXT NOT NULL,
 publication_at TEXT NOT NULL,
 evidence_text TEXT NOT NULL,
 UNIQUE(event_id,source_document_id,source_record_type,source_record_id)
);

CREATE TABLE catalyst_assessments(
 catalyst_id TEXT PRIMARY KEY,
 event_id TEXT NOT NULL REFERENCES research_events,
 event_materiality TEXT NOT NULL,
 catalyst_theme TEXT,
 catalyst_relevance TEXT NOT NULL CHECK(catalyst_relevance IN('NONE','POSSIBLE','DIRECT')),
 catalyst_score TEXT,
 catalyst_confidence TEXT NOT NULL CHECK(catalyst_confidence IN('LOW','MEDIUM','HIGH')),
 rationale TEXT NOT NULL,
 catalyst_model_version TEXT NOT NULL,
 created_at TEXT NOT NULL,
 UNIQUE(event_id,catalyst_model_version)
);
