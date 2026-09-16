PRAGMA foreign_keys=ON;

CREATE TABLE shadow_portfolios(
 shadow_portfolio_id TEXT PRIMARY KEY,
 portfolio_type TEXT NOT NULL CHECK(portfolio_type IN('CONSERVATIVE','BALANCED','HIGH_CONVICTION')),
 currency TEXT NOT NULL,
 initial_cash TEXT NOT NULL,
 current_cash TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN('ACTIVE','DEGRADED','CLOSED')),
 portfolio_model_version TEXT NOT NULL,
 created_at TEXT NOT NULL,
 UNIQUE(portfolio_type,created_at)
);
CREATE TABLE prospective_decision_snapshots(
 prospective_snapshot_id TEXT PRIMARY KEY,
 decision_timestamp TEXT NOT NULL UNIQUE,
 trigger_type TEXT NOT NULL,
 pipeline_health_json TEXT NOT NULL,
 upstream_state TEXT NOT NULL CHECK(upstream_state IN('HEALTHY','DEGRADED','STALE','FAILED')),
 universe_security_ids_json TEXT NOT NULL,
 market_observation_ids_json TEXT NOT NULL,
 financial_document_ids_json TEXT NOT NULL,
 valuation_ids_json TEXT NOT NULL,
 factor_score_ids_json TEXT NOT NULL,
 signal_ids_json TEXT NOT NULL,
 portfolio_state_json TEXT NOT NULL,
 execution_assumptions_json TEXT NOT NULL,
 model_versions_json TEXT NOT NULL,
 source_record_ids_json TEXT NOT NULL,
 created_at TEXT NOT NULL
);
CREATE TABLE prospective_security_states(
 state_id TEXT PRIMARY KEY,
 prospective_snapshot_id TEXT NOT NULL REFERENCES prospective_decision_snapshots,
 security_id TEXT NOT NULL REFERENCES securities,
 signal_id TEXT REFERENCES research_signals,
 valuation_id TEXT REFERENCES valuation_records,
 liquidity_assessment_id TEXT REFERENCES liquidity_assessments,
 signal_state TEXT NOT NULL,
 confidence TEXT,
 risk_gates_json TEXT NOT NULL,
 position_size_json TEXT NOT NULL,
 market_state_json TEXT NOT NULL,
 financial_state_json TEXT NOT NULL,
 valuation_state_json TEXT NOT NULL,
 factor_state_json TEXT NOT NULL,
 liquidity_state_json TEXT NOT NULL,
 execution_state_json TEXT NOT NULL,
 model_versions_json TEXT NOT NULL,
 admission_status TEXT NOT NULL CHECK(admission_status IN('ELIGIBLE','INELIGIBLE','STALE_BLOCKED')),
 admission_reasons_json TEXT NOT NULL,
 UNIQUE(prospective_snapshot_id,security_id)
);
CREATE TABLE paper_orders(
 paper_order_id TEXT PRIMARY KEY,
 shadow_portfolio_id TEXT NOT NULL REFERENCES shadow_portfolios,
 prospective_snapshot_id TEXT NOT NULL REFERENCES prospective_decision_snapshots,
 security_id TEXT NOT NULL REFERENCES securities,
 signal_id TEXT REFERENCES research_signals,
 submitted_at TEXT NOT NULL,
 side TEXT NOT NULL CHECK(side IN('BUY','SELL')),
 requested_shares TEXT NOT NULL,
 participation_rate TEXT NOT NULL,
 decision_price TEXT,
 status TEXT NOT NULL CHECK(status IN('OPEN','PARTIALLY_FILLED','FILLED','NO_FILL','EXPIRED','REJECTED')),
 reason TEXT,
 execution_assumptions_json TEXT NOT NULL,
 signal_model_version TEXT,
 execution_model_version TEXT NOT NULL,
 created_at TEXT NOT NULL
);
CREATE TABLE paper_fills(
 paper_fill_id TEXT PRIMARY KEY,
 paper_order_id TEXT NOT NULL REFERENCES paper_orders,
 source_observation_id TEXT NOT NULL REFERENCES market_observations,
 fill_timestamp TEXT NOT NULL,
 shares TEXT NOT NULL,
 reference_price TEXT NOT NULL,
 fill_price TEXT NOT NULL,
 gross_value TEXT NOT NULL,
 total_fees TEXT NOT NULL,
 slippage_value TEXT NOT NULL,
 observed_volume TEXT NOT NULL,
 participation_rate TEXT NOT NULL,
 created_at TEXT NOT NULL,
 UNIQUE(paper_order_id,source_observation_id)
);
CREATE TABLE paper_positions(
 shadow_portfolio_id TEXT NOT NULL REFERENCES shadow_portfolios,
 security_id TEXT NOT NULL REFERENCES securities,
 shares TEXT NOT NULL,
 cost_basis TEXT NOT NULL,
 realized_pnl TEXT NOT NULL,
 dividends_received TEXT NOT NULL,
 fees_paid TEXT NOT NULL,
 updated_at TEXT NOT NULL,
 PRIMARY KEY(shadow_portfolio_id,security_id)
);
CREATE TABLE paper_portfolio_ledger(
 ledger_id TEXT PRIMARY KEY,
 shadow_portfolio_id TEXT NOT NULL REFERENCES shadow_portfolios,
 event_timestamp TEXT NOT NULL,
 event_type TEXT NOT NULL CHECK(event_type IN('INITIAL_CASH','FILL','DIVIDEND','MARK','CORPORATE_ACTION')),
 cash_change TEXT NOT NULL,
 cash_balance TEXT NOT NULL,
 security_id TEXT REFERENCES securities,
 paper_fill_id TEXT REFERENCES paper_fills,
 source_record_id TEXT,
 evidence_json TEXT NOT NULL,
 created_at TEXT NOT NULL
);
CREATE TABLE paper_signal_outcomes(
 outcome_id TEXT PRIMARY KEY,
 prospective_snapshot_id TEXT NOT NULL REFERENCES prospective_decision_snapshots,
 security_id TEXT NOT NULL REFERENCES securities,
 signal_id TEXT REFERENCES research_signals,
 evaluation_timestamp TEXT NOT NULL,
 sample_size INTEGER NOT NULL,
 signal_return TEXT,
 realized_return TEXT,
 unrealized_return TEXT,
 execution_shortfall TEXT,
 time_to_fill_days TEXT,
 fill_ratio TEXT,
 maximum_favorable_excursion TEXT,
 maximum_adverse_excursion TEXT,
 drawdown TEXT,
 forecast_error TEXT,
 classification TEXT,
 status TEXT NOT NULL CHECK(status IN('AVAILABLE','INSUFFICIENT_FUTURE_EVIDENCE')),
 evidence_json TEXT NOT NULL,
 UNIQUE(prospective_snapshot_id,security_id,evaluation_timestamp)
);
CREATE TABLE paper_drift_assessments(
 drift_id TEXT PRIMARY KEY,
 assessed_at TEXT NOT NULL,
 sample_size INTEGER NOT NULL,
 factor_drift_json TEXT NOT NULL,
 valuation_drift_json TEXT NOT NULL,
 liquidity_drift_json TEXT NOT NULL,
 market_structure_drift_json TEXT NOT NULL,
 data_availability_drift_json TEXT NOT NULL,
 signal_frequency_json TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN('AVAILABLE','INSUFFICIENT_SAMPLE')),
 model_version TEXT NOT NULL
);

CREATE TRIGGER prospective_snapshots_no_update BEFORE UPDATE ON prospective_decision_snapshots BEGIN SELECT RAISE(ABORT,'prospective snapshots are immutable'); END;
CREATE TRIGGER prospective_snapshots_no_delete BEFORE DELETE ON prospective_decision_snapshots BEGIN SELECT RAISE(ABORT,'prospective snapshots are immutable'); END;
CREATE TRIGGER prospective_states_no_update BEFORE UPDATE ON prospective_security_states BEGIN SELECT RAISE(ABORT,'prospective security states are immutable'); END;
CREATE TRIGGER prospective_states_no_delete BEFORE DELETE ON prospective_security_states BEGIN SELECT RAISE(ABORT,'prospective security states are immutable'); END;
