CREATE TABLE research_event_conflicts(
 conflict_id TEXT PRIMARY KEY,
 event_id TEXT NOT NULL REFERENCES research_events,
 incoming_source_document_id TEXT NOT NULL REFERENCES raw_documents,
 conflicting_fields_json TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'UNRESOLVED',
 created_at TEXT NOT NULL,
 UNIQUE(event_id,incoming_source_document_id,conflicting_fields_json)
);
