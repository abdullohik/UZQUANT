CREATE TABLE rse_history_acquisition_jobs(
 job_id TEXT PRIMARY KEY,
 isin TEXT NOT NULL,
 ticker TEXT,
 requested_begin TEXT NOT NULL,
 requested_end TEXT NOT NULL,
 market_code TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN('PENDING','IN_PROGRESS','DOWNLOADED','IMPORTED','EMPTY','VALIDATION_FAILED','SOURCE_BLOCKED','FAILED')),
 attempt_count INTEGER NOT NULL DEFAULT 0 CHECK(attempt_count>=0),
 last_attempt_at TEXT,
 downloaded_path TEXT,
 file_sha256 TEXT,
 capture_id TEXT REFERENCES rse_trade_export_captures,
 error_details TEXT,
 created_at TEXT NOT NULL,
 updated_at TEXT NOT NULL,
 UNIQUE(isin,requested_begin,requested_end,market_code)
);
CREATE INDEX rse_history_jobs_status ON rse_history_acquisition_jobs(status,requested_begin,isin);
