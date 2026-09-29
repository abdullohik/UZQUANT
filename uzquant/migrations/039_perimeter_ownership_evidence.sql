PRAGMA foreign_keys=ON;
CREATE TABLE perimeter_ownership_evidence(
 evidence_id TEXT PRIMARY KEY, issuer_id TEXT NOT NULL REFERENCES issuers,
 classification TEXT NOT NULL CHECK(classification IN('NO_SUBSIDIARIES_CONFIRMED','SUBSIDIARIES_PRESENT','OWNERSHIP_EVIDENCE_UNAVAILABLE')),
 effective_from TEXT,effective_to TEXT,known_at TEXT NOT NULL,source_url TEXT NOT NULL,
 source_document_id TEXT REFERENCES raw_documents,evidence_text TEXT NOT NULL,
 provenance_class TEXT NOT NULL CHECK(provenance_class IN('OBSERVED','AUTHORITATIVE_SOURCE','SOURCE_DERIVED','MODEL_DERIVED','MODEL_ESTIMATED','CONFIGURABLE_RESEARCH_ASSUMPTION','STRUCTURAL_INFERENCE_NO_SUBSIDIARIES','UNKNOWN','UNAVAILABLE')),
 parser_version TEXT NOT NULL,created_at TEXT NOT NULL,
 CHECK(effective_to IS NULL OR effective_from IS NULL OR effective_to>=effective_from));
CREATE TABLE financial_document_perimeter_assessments(
 assessment_id TEXT PRIMARY KEY,document_id TEXT NOT NULL REFERENCES financial_documents,
 classification TEXT NOT NULL CHECK(classification IN('NO_SUBSIDIARIES_CONFIRMED','SUBSIDIARIES_PRESENT','OWNERSHIP_EVIDENCE_UNAVAILABLE')),
 resolved_perimeter TEXT CHECK(resolved_perimeter IS NULL OR resolved_perimeter='CONSOLIDATED'),
 provenance_class TEXT NOT NULL CHECK(provenance_class IN('AUTHORITATIVE_SOURCE','STRUCTURAL_INFERENCE_NO_SUBSIDIARIES','UNAVAILABLE')),
 evidence_id TEXT REFERENCES perimeter_ownership_evidence,
 period_match_status TEXT NOT NULL CHECK(period_match_status IN('MATCHED','NOT_MATCHED','NO_PERIOD_EVIDENCE')),
 blocker_taxonomy TEXT,reason TEXT NOT NULL,assessed_at TEXT NOT NULL,model_version TEXT NOT NULL,
 UNIQUE(document_id,model_version),
 CHECK(classification!='NO_SUBSIDIARIES_CONFIRMED' OR (resolved_perimeter='CONSOLIDATED' AND provenance_class='STRUCTURAL_INFERENCE_NO_SUBSIDIARIES' AND evidence_id IS NOT NULL AND period_match_status='MATCHED')),
 CHECK(classification='NO_SUBSIDIARIES_CONFIRMED' OR resolved_perimeter IS NULL));
CREATE TABLE perimeter_source_search_log(
 search_id TEXT PRIMARY KEY,issuer_id TEXT NOT NULL REFERENCES issuers,searched_at TEXT NOT NULL,
 query_scope TEXT NOT NULL,source_url TEXT NOT NULL,
 outcome TEXT NOT NULL CHECK(outcome IN('SUBSIDIARIES_PRESENT','NO_SUBSIDIARIES_CONFIRMED','NO_PERIOD_MATCHED_EVIDENCE','SOURCE_UNAVAILABLE')),
 evidence_note TEXT NOT NULL,model_version TEXT NOT NULL);
CREATE INDEX perimeter_evidence_issuer_period ON perimeter_ownership_evidence(issuer_id,effective_from,effective_to);
CREATE INDEX perimeter_assessment_document ON financial_document_perimeter_assessments(document_id,classification);
