PRAGMA foreign_keys=ON;
CREATE TABLE rse_universe_captures(
 capture_id TEXT PRIMARY KEY,run_id TEXT NOT NULL REFERENCES ingestion_runs,retrieved_at TEXT NOT NULL,
 listing_url TEXT NOT NULL,quotation_url TEXT NOT NULL,
 listing_document_id TEXT NOT NULL REFERENCES raw_documents,quotation_document_id TEXT NOT NULL REFERENCES raw_documents,
 source_reported_total INTEGER,page_count INTEGER NOT NULL,page_row_counts_json TEXT NOT NULL,
 raw_row_count INTEGER NOT NULL,unique_instrument_count INTEGER NOT NULL,duplicate_count INTEGER NOT NULL,
 pagination_complete INTEGER NOT NULL CHECK(pagination_complete IN(0,1)),parser_version TEXT NOT NULL);
CREATE TABLE rse_universe_instruments(
 capture_id TEXT NOT NULL REFERENCES rse_universe_captures,
 source_view TEXT NOT NULL CHECK(source_view IN('LISTING','QUOTATION')),
 isin TEXT NOT NULL,ticker TEXT NOT NULL,issuer_name TEXT NOT NULL,
 instrument_class TEXT NOT NULL CHECK(instrument_class IN('COMMON_EQUITY','PREFERRED_EQUITY','BOND','OTHER','UNKNOWN')),
 classification_reason TEXT NOT NULL,listing_category TEXT,listing_status TEXT NOT NULL,
 listing_date TEXT,delisting_date TEXT,shares_listed TEXT,nominal_value TEXT,currency TEXT,
 detail_document_id TEXT REFERENCES raw_documents,raw_evidence_json TEXT NOT NULL,
 PRIMARY KEY(capture_id,source_view,isin,ticker));
CREATE INDEX rse_universe_instruments_lookup ON rse_universe_instruments(isin,ticker,instrument_class);
