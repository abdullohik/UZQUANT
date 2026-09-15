PRAGMA foreign_keys=ON;

CREATE TABLE execution_assessments(
  execution_assessment_id TEXT PRIMARY KEY,
  security_id TEXT NOT NULL REFERENCES securities,
  as_of_date TEXT NOT NULL,
  side TEXT NOT NULL CHECK(side IN('ENTER','EXIT')),
  proposed_shares TEXT NOT NULL,
  preferred_execution_style TEXT NOT NULL,
  maximum_suggested_child_order TEXT,
  maximum_participation_rate TEXT NOT NULL,
  estimated_execution_horizon_days TEXT,
  acceptable_entry_low TEXT,
  acceptable_entry_high TEXT,
  expected_slippage_low TEXT,
  expected_slippage_high TEXT,
  execution_confidence TEXT NOT NULL,
  intraday_timing_status TEXT NOT NULL,
  status TEXT NOT NULL CHECK(status IN('ESTIMATE_AVAILABLE','CANNOT_ESTIMATE_EXECUTION_RELIABLY')),
  flags_json TEXT NOT NULL,
  uncertainty_json TEXT NOT NULL,
  assumptions_json TEXT NOT NULL,
  source_observation_ids_json TEXT NOT NULL,
  liquidity_assessment_id TEXT REFERENCES liquidity_assessments,
  entry_zone_id TEXT REFERENCES entry_zone_records,
  execution_model_version TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX execution_history ON execution_assessments(security_id,as_of_date,created_at);
