CREATE TABLE rse_trade_export_captures(
 capture_id TEXT PRIMARY KEY,
 raw_document_id TEXT NOT NULL REFERENCES raw_documents,
 source_id TEXT NOT NULL REFERENCES data_sources,
 requested_begin TEXT NOT NULL,
 requested_end TEXT NOT NULL,
 market_code TEXT NOT NULL,
 search_key TEXT,
 retrieved_at TEXT NOT NULL,
 first_exchange_timestamp TEXT NOT NULL,
 last_exchange_timestamp TEXT NOT NULL,
 row_count INTEGER NOT NULL CHECK(row_count>=0),
 identity_matched_count INTEGER NOT NULL CHECK(identity_matched_count>=0),
 identity_unresolved_count INTEGER NOT NULL CHECK(identity_unresolved_count>=0),
 coverage_status TEXT NOT NULL CHECK(coverage_status IN('OFFICIAL_EXPORT_PARTIAL_CURRENT_DAY','OFFICIAL_EXPORT_HISTORICAL_RANGE','EMPTY')),
 parser_version TEXT NOT NULL,
 UNIQUE(raw_document_id)
);

CREATE TABLE rse_trade_records(
 trade_record_id TEXT PRIMARY KEY,
 capture_id TEXT NOT NULL REFERENCES rse_trade_export_captures,
 source_row_number INTEGER NOT NULL CHECK(source_row_number>1),
 security_id TEXT REFERENCES securities,
 identity_status TEXT NOT NULL CHECK(identity_status IN('MATCHED_ISIN','UNRESOLVED_ISIN','AMBIGUOUS_ISIN')),
 exchange_timestamp TEXT NOT NULL,
 timezone TEXT NOT NULL,
 isin TEXT NOT NULL,
 ticker TEXT NOT NULL,
 issuer_name TEXT NOT NULL,
 source_security_type TEXT NOT NULL,
 market_code TEXT NOT NULL,
 board_code TEXT NOT NULL,
 price TEXT NOT NULL CHECK(CAST(price AS REAL)>0),
 quantity TEXT NOT NULL CHECK(CAST(quantity AS REAL)>0),
 turnover_value TEXT NOT NULL CHECK(CAST(turnover_value AS REAL)>=0),
 currency TEXT NOT NULL,
 raw_document_id TEXT NOT NULL REFERENCES raw_documents,
 parser_version TEXT NOT NULL,
 UNIQUE(capture_id,source_row_number)
);
CREATE INDEX rse_trade_security_time ON rse_trade_records(security_id,exchange_timestamp);
CREATE INDEX rse_trade_isin_time ON rse_trade_records(isin,exchange_timestamp);
