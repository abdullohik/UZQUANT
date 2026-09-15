PRAGMA foreign_keys=ON;

CREATE TABLE validation_runs(
  validation_run_id TEXT PRIMARY KEY,
  strategy_name TEXT NOT NULL,
  classification TEXT NOT NULL CHECK(classification IN('ROBUST','PROMISING_BUT_UNPROVEN','FRAGILE','UNRELIABLE')),
  status TEXT NOT NULL CHECK(status IN('COMPLETED','DATA_INSUFFICIENT','FAILED')),
  reasons_json TEXT NOT NULL,
  validation_version TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE walk_forward_splits(
  split_id TEXT PRIMARY KEY,
  validation_run_id TEXT NOT NULL REFERENCES validation_runs,
  split_number INTEGER NOT NULL,
  train_start TEXT NOT NULL,
  train_end TEXT NOT NULL,
  validation_start TEXT,
  validation_end TEXT,
  out_of_sample_start TEXT NOT NULL,
  out_of_sample_end TEXT NOT NULL,
  final_test_locked INTEGER NOT NULL CHECK(final_test_locked IN(0,1)),
  UNIQUE(validation_run_id,split_number)
);
CREATE TABLE experiment_registry(
  experiment_id TEXT PRIMARY KEY,
  validation_run_id TEXT NOT NULL REFERENCES validation_runs,
  experiment_name TEXT NOT NULL,
  experiment_family TEXT NOT NULL,
  parent_experiment_id TEXT REFERENCES experiment_registry,
  parameters_json TEXT NOT NULL,
  hypothesis TEXT NOT NULL,
  registered_at TEXT NOT NULL,
  uses_final_oos_for_tuning INTEGER NOT NULL CHECK(uses_final_oos_for_tuning=0),
  status TEXT NOT NULL CHECK(status IN('REGISTERED','COMPLETED','DATA_INSUFFICIENT','FAILED')),
  result_json TEXT NOT NULL,
  UNIQUE(validation_run_id,experiment_name)
);
CREATE TABLE robustness_results(
  robustness_result_id TEXT PRIMARY KEY,
  experiment_id TEXT NOT NULL REFERENCES experiment_registry,
  split_id TEXT REFERENCES walk_forward_splits,
  sample_name TEXT NOT NULL,
  total_return TEXT,
  sharpe TEXT,
  maximum_drawdown TEXT,
  turnover TEXT,
  capacity TEXT,
  confidence_interval_low TEXT,
  confidence_interval_high TEXT,
  status TEXT NOT NULL CHECK(status IN('AVAILABLE','UNAVAILABLE')),
  reason TEXT,
  created_at TEXT NOT NULL
);
CREATE TABLE model_risk_findings(
  finding_id TEXT PRIMARY KEY,
  validation_run_id TEXT NOT NULL REFERENCES validation_runs,
  risk_type TEXT NOT NULL,
  severity TEXT NOT NULL CHECK(severity IN('LOW','MEDIUM','HIGH','CRITICAL')),
  evidence_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);
