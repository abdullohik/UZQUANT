PRAGMA foreign_keys=ON;

CREATE TABLE backtest_runs(
  backtest_run_id TEXT PRIMARY KEY,
  strategy_name TEXT NOT NULL,
  start_date TEXT,
  end_date TEXT,
  initial_capital TEXT NOT NULL,
  currency TEXT NOT NULL,
  status TEXT NOT NULL CHECK(status IN('COMPLETED','DATA_INSUFFICIENT','FAILED')),
  assumptions_json TEXT NOT NULL,
  insufficiency_reasons_json TEXT NOT NULL,
  model_version TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE backtest_snapshots(
  snapshot_id TEXT PRIMARY KEY,
  backtest_run_id TEXT NOT NULL REFERENCES backtest_runs,
  decision_timestamp TEXT NOT NULL,
  universe_security_ids_json TEXT NOT NULL,
  identifier_ids_json TEXT NOT NULL,
  price_observation_ids_json TEXT NOT NULL,
  financial_document_ids_json TEXT NOT NULL,
  ownership_ids_json TEXT NOT NULL,
  rights_ids_json TEXT NOT NULL,
  event_ids_json TEXT NOT NULL,
  corporate_action_ids_json TEXT NOT NULL,
  dividend_ids_json TEXT NOT NULL,
  macro_observation_ids_json TEXT NOT NULL,
  signal_ids_json TEXT NOT NULL,
  model_versions_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE backtest_orders(
  order_id TEXT PRIMARY KEY,
  backtest_run_id TEXT NOT NULL REFERENCES backtest_runs,
  snapshot_id TEXT REFERENCES backtest_snapshots,
  security_id TEXT NOT NULL REFERENCES securities,
  signal_timestamp TEXT NOT NULL,
  side TEXT NOT NULL CHECK(side IN('BUY','SELL')),
  requested_shares TEXT NOT NULL,
  decision_price TEXT,
  participation_rate TEXT NOT NULL,
  status TEXT NOT NULL CHECK(status IN('PENDING','PARTIALLY_FILLED','FILLED','REJECTED','EXPIRED')),
  rejection_reason TEXT,
  model_version TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE backtest_fills(
  fill_id TEXT PRIMARY KEY,
  order_id TEXT NOT NULL REFERENCES backtest_orders,
  fill_date TEXT NOT NULL,
  shares TEXT NOT NULL,
  reference_price TEXT NOT NULL,
  fill_price TEXT NOT NULL,
  gross_value TEXT NOT NULL,
  transaction_fees TEXT NOT NULL,
  broker_fees TEXT NOT NULL,
  exchange_fees TEXT NOT NULL,
  depository_fees TEXT NOT NULL,
  slippage_value TEXT NOT NULL,
  observed_volume TEXT NOT NULL,
  participation_rate TEXT NOT NULL,
  source_observation_id TEXT NOT NULL REFERENCES market_observations,
  created_at TEXT NOT NULL
);
CREATE TABLE backtest_metrics(
  metric_id TEXT PRIMARY KEY,
  backtest_run_id TEXT NOT NULL REFERENCES backtest_runs,
  metric_name TEXT NOT NULL,
  metric_value TEXT,
  status TEXT NOT NULL CHECK(status IN('AVAILABLE','UNAVAILABLE')),
  reason TEXT,
  UNIQUE(backtest_run_id,metric_name)
);
