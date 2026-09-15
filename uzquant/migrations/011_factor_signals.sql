CREATE TABLE factor_scores(
 factor_score_id TEXT PRIMARY KEY,
 security_id TEXT NOT NULL REFERENCES securities,
 data_snapshot_id TEXT NOT NULL,
 as_of_date TEXT NOT NULL,
 factor_name TEXT NOT NULL,
 raw_metric_json TEXT NOT NULL,
 transformation TEXT NOT NULL,
 score TEXT,
 status TEXT NOT NULL CHECK(status IN('AVAILABLE','UNAVAILABLE')),
 unavailable_reason TEXT,
 sector_engine TEXT,
 source_record_ids_json TEXT NOT NULL,
 scoring_version TEXT NOT NULL,
 created_at TEXT NOT NULL
);
CREATE INDEX factor_scores_snapshot ON factor_scores(data_snapshot_id,security_id,factor_name);

CREATE TABLE research_signals(
 signal_id TEXT PRIMARY KEY,
 security_id TEXT NOT NULL REFERENCES securities,
 signal_state TEXT NOT NULL CHECK(signal_state IN('STRONG_BUY','BUY','ACCUMULATE','WATCH','HOLD','REDUCE','AVOID','LIQUIDITY_TRAP','GOVERNANCE_RISK','DATA_INSUFFICIENT')),
 investment_attractiveness TEXT,
 confidence TEXT NOT NULL,
 factor_scores_json TEXT NOT NULL,
 triggered_gates_json TEXT NOT NULL,
 explanation_json TEXT NOT NULL,
 model_version TEXT NOT NULL,
 scoring_version TEXT NOT NULL,
 valuation_version TEXT NOT NULL,
 liquidity_version TEXT NOT NULL,
 data_snapshot_id TEXT NOT NULL,
 generated_at TEXT NOT NULL
);
CREATE INDEX research_signals_history ON research_signals(security_id,generated_at);
