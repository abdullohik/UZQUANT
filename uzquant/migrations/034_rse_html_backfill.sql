CREATE TABLE rse_trade_html_pages(
 page_capture_id TEXT PRIMARY KEY,
 job_id TEXT NOT NULL REFERENCES rse_history_acquisition_jobs,
 page_number INTEGER NOT NULL CHECK(page_number>0),
 raw_document_id TEXT NOT NULL REFERENCES raw_documents,
 source_url TEXT NOT NULL,
 retrieved_at TEXT NOT NULL,
 row_count INTEGER NOT NULL CHECK(row_count>=0),
 parser_version TEXT NOT NULL,
 UNIQUE(job_id,page_number)
);

CREATE TABLE rse_trade_html_records(
 trade_record_id TEXT PRIMARY KEY,
 page_capture_id TEXT NOT NULL REFERENCES rse_trade_html_pages,
 source_row_number INTEGER NOT NULL CHECK(source_row_number>0),
 security_id TEXT NOT NULL REFERENCES securities,
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
 UNIQUE(page_capture_id,source_row_number)
);
CREATE INDEX rse_html_trade_security_time ON rse_trade_html_records(security_id,exchange_timestamp);

CREATE TABLE market_observation_trade_lineage(
 observation_id TEXT NOT NULL REFERENCES market_observations,
 trade_record_id TEXT NOT NULL REFERENCES rse_trade_html_records,
 PRIMARY KEY(observation_id,trade_record_id)
);
