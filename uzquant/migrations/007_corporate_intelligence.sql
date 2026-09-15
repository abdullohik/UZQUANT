CREATE TABLE corporate_actions(
 action_id TEXT PRIMARY KEY,issuer_id TEXT NOT NULL REFERENCES issuers,security_id TEXT REFERENCES securities,
 action_type TEXT NOT NULL,announcement_date TEXT NOT NULL,record_date TEXT,effective_date TEXT,payment_date TEXT,
 adjustment_factor TEXT,details_json TEXT NOT NULL,source_document_id TEXT NOT NULL REFERENCES raw_documents,
 source_url TEXT NOT NULL,confidence TEXT NOT NULL,verification_status TEXT NOT NULL,
 UNIQUE(source_document_id,action_type,security_id));
CREATE INDEX corporate_actions_pit ON corporate_actions(issuer_id,announcement_date,effective_date);
CREATE TABLE dividends(
 dividend_id TEXT PRIMARY KEY,issuer_id TEXT NOT NULL REFERENCES issuers,security_id TEXT NOT NULL REFERENCES securities,
 announcement_date TEXT NOT NULL,ex_date TEXT,record_date TEXT,payment_start_date TEXT,payment_end_date TEXT,
 dividend_per_share TEXT NOT NULL,currency TEXT NOT NULL,dividend_type TEXT NOT NULL,
 source_document_id TEXT NOT NULL REFERENCES raw_documents,source_url TEXT NOT NULL,confidence TEXT NOT NULL,
 UNIQUE(source_document_id,security_id,dividend_type));
CREATE INDEX dividends_pit ON dividends(security_id,announcement_date);
CREATE TABLE ownership_positions(
 ownership_id TEXT PRIMARY KEY,issuer_id TEXT NOT NULL REFERENCES issuers,security_id TEXT REFERENCES securities,
 shareholder_name TEXT NOT NULL,shareholder_type TEXT NOT NULL,
 ownership_percentage TEXT,threshold_operator TEXT,threshold_percentage TEXT,
 effective_date TEXT NOT NULL,disclosure_date TEXT NOT NULL,
 source_document_id TEXT NOT NULL REFERENCES raw_documents,source_url TEXT NOT NULL,confidence TEXT NOT NULL,
 UNIQUE(source_document_id,issuer_id,shareholder_name,effective_date));
CREATE INDEX ownership_positions_pit ON ownership_positions(issuer_id,disclosure_date,effective_date);
CREATE TABLE ownership_metrics(
 metric_id TEXT PRIMARY KEY,issuer_id TEXT NOT NULL REFERENCES issuers,as_of_date TEXT NOT NULL,
 metric_name TEXT NOT NULL,metric_value TEXT,status TEXT NOT NULL,reason TEXT,
 source_document_ids_json TEXT NOT NULL,UNIQUE(issuer_id,as_of_date,metric_name));
CREATE TABLE security_rights(
 rights_id TEXT PRIMARY KEY,security_id TEXT NOT NULL REFERENCES securities,effective_date TEXT,disclosure_date TEXT NOT NULL,
 voting_rights TEXT,dividend_rights TEXT,minimum_dividend TEXT,formula_based_dividend TEXT,cumulative_dividend TEXT,
 liquidation_preference TEXT,conversion_rights TEXT,redemption_rights TEXT,participation_rights TEXT,preemptive_rights TEXT,
 nominal_value TEXT,currency TEXT,source_provision TEXT NOT NULL,rights_summary TEXT NOT NULL,rights_confidence TEXT NOT NULL,
 source_document_id TEXT NOT NULL REFERENCES raw_documents,source_url TEXT NOT NULL,
 UNIQUE(source_document_id,security_id));
CREATE INDEX security_rights_pit ON security_rights(security_id,disclosure_date);
CREATE TABLE governance_events(
 event_id TEXT PRIMARY KEY,issuer_id TEXT NOT NULL REFERENCES issuers,security_id TEXT REFERENCES securities,
 event_type TEXT NOT NULL,event_date TEXT NOT NULL,disclosure_date TEXT NOT NULL,evidence_text TEXT NOT NULL,
 confidence TEXT NOT NULL,classification_method TEXT NOT NULL,source_document_id TEXT NOT NULL REFERENCES raw_documents,
 source_url TEXT NOT NULL,UNIQUE(source_document_id,event_type,event_date,evidence_text));
CREATE INDEX governance_events_pit ON governance_events(issuer_id,disclosure_date,event_date);
CREATE TABLE corporate_data_conflicts(
 conflict_id TEXT PRIMARY KEY,issuer_id TEXT NOT NULL REFERENCES issuers,security_id TEXT REFERENCES securities,
 field_name TEXT NOT NULL,value_a TEXT NOT NULL,value_b TEXT NOT NULL,
 source_document_a TEXT NOT NULL REFERENCES raw_documents,source_document_b TEXT NOT NULL REFERENCES raw_documents,
 status TEXT NOT NULL DEFAULT 'UNRESOLVED',created_at TEXT NOT NULL);
