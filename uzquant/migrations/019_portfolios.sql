PRAGMA foreign_keys=ON;

CREATE TABLE portfolio_runs(
  portfolio_id TEXT PRIMARY KEY,
  portfolio_type TEXT NOT NULL CHECK(portfolio_type IN('CONSERVATIVE','BALANCED','HIGH_CONVICTION')),
  as_of_date TEXT NOT NULL,
  aum TEXT NOT NULL,
  currency TEXT NOT NULL,
  status TEXT NOT NULL CHECK(status IN('CONSTRUCTED','DATA_INSUFFICIENT')),
  cash_weight TEXT NOT NULL,
  constraints_json TEXT NOT NULL,
  reasons_json TEXT NOT NULL,
  validation_run_id TEXT REFERENCES validation_runs,
  portfolio_model_version TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE portfolio_positions(
  portfolio_position_id TEXT PRIMARY KEY,
  portfolio_id TEXT NOT NULL REFERENCES portfolio_runs,
  security_id TEXT NOT NULL REFERENCES securities,
  ticker TEXT NOT NULL,
  target_weight TEXT NOT NULL,
  maximum_weight TEXT NOT NULL,
  binding_constraint TEXT NOT NULL,
  investment_thesis_reference TEXT NOT NULL,
  valuation_json TEXT NOT NULL,
  confidence TEXT NOT NULL,
  liquidity_capacity_value TEXT NOT NULL,
  exit_horizon_days TEXT,
  risk_contribution TEXT,
  sector TEXT NOT NULL,
  factor_exposures_json TEXT NOT NULL,
  macro_exposures_json TEXT NOT NULL,
  source_record_ids_json TEXT NOT NULL,
  UNIQUE(portfolio_id,security_id)
);
CREATE TABLE portfolio_metrics(
  portfolio_metric_id TEXT PRIMARY KEY,
  portfolio_id TEXT NOT NULL REFERENCES portfolio_runs,
  metric_name TEXT NOT NULL,
  metric_json TEXT NOT NULL,
  status TEXT NOT NULL CHECK(status IN('AVAILABLE','UNAVAILABLE')),
  reason TEXT,
  UNIQUE(portfolio_id,metric_name)
);
