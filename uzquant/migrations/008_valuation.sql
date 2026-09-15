CREATE TABLE valuation_records(
 valuation_id TEXT PRIMARY KEY,
 security_id TEXT NOT NULL REFERENCES securities,
 issuer_id TEXT NOT NULL REFERENCES issuers,
 valuation_date TEXT NOT NULL,
 data_cutoff_date TEXT NOT NULL,
 financial_period_inputs_json TEXT NOT NULL,
 method TEXT NOT NULL,
 sector_engine TEXT NOT NULL,
 currency TEXT,
 assumptions_json TEXT NOT NULL,
 bear_value TEXT,
 base_value TEXT,
 bull_value TEXT,
 confidence TEXT NOT NULL,
 valuation_model_version TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN ('AVAILABLE','VALUATION_INSUFFICIENT')),
 insufficiency_reasons_json TEXT NOT NULL,
 source_document_ids_json TEXT NOT NULL,
 source_observation_ids_json TEXT NOT NULL,
 created_at TEXT NOT NULL,
 UNIQUE(security_id,valuation_date,method,valuation_model_version)
);
CREATE INDEX valuation_records_pit ON valuation_records(security_id,data_cutoff_date,valuation_date);

CREATE TABLE valuation_sensitivities(
 sensitivity_id TEXT PRIMARY KEY,
 valuation_id TEXT NOT NULL REFERENCES valuation_records ON DELETE CASCADE,
 dimension TEXT NOT NULL,
 assumption_value TEXT NOT NULL,
 enterprise_value TEXT,
 equity_value TEXT,
 fair_value_per_share TEXT,
 UNIQUE(valuation_id,dimension,assumption_value)
);

CREATE TABLE valuation_peer_sets(
 peer_set_id TEXT PRIMARY KEY,
 valuation_id TEXT NOT NULL REFERENCES valuation_records ON DELETE CASCADE,
 as_of_date TEXT NOT NULL,
 selection_logic TEXT NOT NULL,
 member_security_ids_json TEXT NOT NULL,
 source_json TEXT NOT NULL
);

CREATE TABLE valuation_fx_inputs(
 fx_input_id TEXT PRIMARY KEY,
 valuation_id TEXT REFERENCES valuation_records ON DELETE CASCADE,
 from_currency TEXT NOT NULL,
 to_currency TEXT NOT NULL,
 rate TEXT NOT NULL,
 rate_date TEXT NOT NULL,
 source TEXT NOT NULL,
 UNIQUE(valuation_id,from_currency,to_currency,rate_date,source)
);
