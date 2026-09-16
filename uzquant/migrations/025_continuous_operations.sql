PRAGMA foreign_keys=ON;

CREATE TABLE pipeline_definitions(
 pipeline TEXT PRIMARY KEY, source TEXT NOT NULL, handler_group TEXT NOT NULL,
 refresh_interval_seconds INTEGER NOT NULL, dependencies_json TEXT NOT NULL,
 data_version TEXT NOT NULL, enabled INTEGER NOT NULL CHECK(enabled IN(0,1)), created_at TEXT NOT NULL);
CREATE TABLE scheduled_pipeline_runs(
 run_id TEXT PRIMARY KEY, pipeline TEXT NOT NULL REFERENCES pipeline_definitions,
 started_at TEXT NOT NULL, finished_at TEXT, status TEXT NOT NULL CHECK(status IN('HEALTHY','STALE','DEGRADED','FAILED')),
 source TEXT NOT NULL, records_attempted INTEGER NOT NULL, records_succeeded INTEGER NOT NULL,
 records_failed INTEGER NOT NULL, error TEXT, retry_state TEXT NOT NULL, data_version TEXT NOT NULL,
 expected_refresh_at TEXT, upstream_state_json TEXT NOT NULL);
CREATE INDEX scheduled_pipeline_runs_latest ON scheduled_pipeline_runs(pipeline,started_at);
CREATE TABLE pipeline_health(
 pipeline TEXT PRIMARY KEY REFERENCES pipeline_definitions, status TEXT NOT NULL CHECK(status IN('HEALTHY','STALE','DEGRADED','FAILED')),
 last_attempt_at TEXT, last_success_at TEXT, expected_refresh_at TEXT, stale_since TEXT,
 latest_error TEXT, retry_state TEXT NOT NULL, source TEXT NOT NULL, data_version TEXT NOT NULL,
 affected_downstream_json TEXT NOT NULL, updated_at TEXT NOT NULL);
CREATE TABLE research_anomalies(
 anomaly_id TEXT PRIMARY KEY, anomaly_type TEXT NOT NULL, severity TEXT NOT NULL,
 entity_type TEXT NOT NULL, entity_id TEXT, observed_at TEXT NOT NULL,
 evidence_json TEXT NOT NULL, source_record_ids_json TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN('OPEN','ACKNOWLEDGED','RESOLVED')), detector_version TEXT NOT NULL,
 dedupe_key TEXT NOT NULL UNIQUE, created_at TEXT NOT NULL);
CREATE TABLE research_alerts(
 alert_id TEXT PRIMARY KEY, alert_type TEXT NOT NULL, severity TEXT NOT NULL,
 entity_type TEXT NOT NULL, entity_id TEXT, title TEXT NOT NULL, message TEXT NOT NULL,
 evidence_json TEXT NOT NULL, source_record_ids_json TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN('OPEN','ACKNOWLEDGED','RESOLVED')),
 dedupe_key TEXT NOT NULL UNIQUE, created_at TEXT NOT NULL, resolved_at TEXT);
CREATE TABLE signal_state_transitions(
 transition_id TEXT PRIMARY KEY, security_id TEXT NOT NULL REFERENCES securities,
 old_signal_id TEXT REFERENCES research_signals, new_signal_id TEXT NOT NULL REFERENCES research_signals,
 old_state TEXT, new_state TEXT NOT NULL, change_driver_json TEXT NOT NULL,
 changed_at TEXT NOT NULL, data_snapshot_id TEXT NOT NULL, model_version TEXT NOT NULL,
 scoring_version TEXT NOT NULL, valuation_version TEXT NOT NULL, liquidity_version TEXT NOT NULL,
 UNIQUE(new_signal_id));
