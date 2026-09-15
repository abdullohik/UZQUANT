PRAGMA foreign_keys=ON;

CREATE TABLE entry_zone_records(
  entry_zone_id TEXT PRIMARY KEY,
  security_id TEXT NOT NULL REFERENCES securities,
  valuation_id TEXT REFERENCES valuation_records,
  as_of_date TEXT NOT NULL,
  currency TEXT,
  bear_value TEXT,
  base_value TEXT,
  bull_value TEXT,
  effective_margin_of_safety TEXT,
  strong_buy_upper TEXT,
  accumulate_upper TEXT,
  fair_value_upper TEXT,
  trim_upper TEXT,
  observed_price TEXT,
  observed_zone TEXT,
  status TEXT NOT NULL CHECK(status IN('AVAILABLE','ENTRY_INSUFFICIENT')),
  reasons_json TEXT NOT NULL,
  assumptions_json TEXT NOT NULL,
  model_version TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX entry_zones_history ON entry_zone_records(security_id,as_of_date,created_at);

CREATE TABLE position_sizing_records(
  sizing_id TEXT PRIMARY KEY,
  security_id TEXT NOT NULL REFERENCES securities,
  entry_zone_id TEXT REFERENCES entry_zone_records,
  liquidity_assessment_id TEXT REFERENCES liquidity_assessments,
  signal_id TEXT REFERENCES research_signals,
  as_of_date TEXT NOT NULL,
  portfolio_value TEXT NOT NULL,
  currency TEXT NOT NULL,
  fundamental_maximum_pct TEXT,
  liquidity_maximum_pct TEXT,
  risk_maximum_pct TEXT,
  portfolio_maximum_pct TEXT NOT NULL,
  free_float_maximum_pct TEXT,
  final_maximum_pct TEXT NOT NULL,
  final_position_value TEXT NOT NULL,
  binding_constraint TEXT NOT NULL,
  status TEXT NOT NULL CHECK(status IN('AVAILABLE','POSITION_SIZE_INSUFFICIENT')),
  inputs_json TEXT NOT NULL,
  assumptions_json TEXT NOT NULL,
  explanation_json TEXT NOT NULL,
  sizing_model_version TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX position_sizing_history ON position_sizing_records(security_id,as_of_date,created_at);
