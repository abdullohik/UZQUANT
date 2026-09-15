CREATE TABLE liquidity_assessments(
 assessment_id TEXT PRIMARY KEY,
 security_id TEXT NOT NULL REFERENCES securities,
 as_of_date TEXT NOT NULL,
 data_cutoff_date TEXT NOT NULL,
 position_shares TEXT NOT NULL,
 participation_rate TEXT NOT NULL,
 mark_price TEXT,
 mark_to_market_value TEXT,
 estimated_realizable_value_low TEXT,
 estimated_realizable_value_high TEXT,
 slippage_low TEXT,
 slippage_high TEXT,
 liquidation_horizon_days TEXT,
 liquidity_state TEXT NOT NULL CHECK(liquidity_state IN('INVESTABLE','LIMITED_LIQUIDITY','HIGH_LIQUIDITY_RISK','LIQUIDITY_TRAP','UNASSESSABLE')),
 liquidity_confidence TEXT NOT NULL,
 hard_flags_json TEXT NOT NULL,
 features_json TEXT NOT NULL,
 assumptions_json TEXT NOT NULL,
 uncertainty_json TEXT NOT NULL,
 source_observation_ids_json TEXT NOT NULL,
 liquidity_model_version TEXT NOT NULL,
 created_at TEXT NOT NULL,
 UNIQUE(security_id,as_of_date,position_shares,participation_rate,liquidity_model_version)
);
CREATE INDEX liquidity_assessments_pit ON liquidity_assessments(security_id,data_cutoff_date,as_of_date);

CREATE TABLE liquidity_threshold_versions(
 threshold_version TEXT PRIMARY KEY,
 effective_date TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status='PROVISIONAL'),
 universe_size INTEGER NOT NULL,
 thresholds_json TEXT NOT NULL,
 empirical_distribution_json TEXT NOT NULL,
 rationale TEXT NOT NULL,
 created_at TEXT NOT NULL
);
