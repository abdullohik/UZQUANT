CREATE TABLE valuation_assumption_inputs(
 assumption_id TEXT PRIMARY KEY,
 security_id TEXT REFERENCES securities,
 method TEXT NOT NULL,
 input_name TEXT NOT NULL,
 scenario TEXT NOT NULL CHECK(scenario IN('BEAR','BASE','BULL','COMMON')),
 value TEXT,
 currency TEXT,
 as_of_date TEXT NOT NULL,
 provenance_class TEXT NOT NULL CHECK(provenance_class IN('OBSERVED','SOURCE_DERIVED','MODEL_ESTIMATED','CONFIGURABLE_RESEARCH_ASSUMPTION','UNAVAILABLE')),
 source TEXT,
 created_at TEXT NOT NULL,
 UNIQUE(security_id,method,input_name,scenario,as_of_date)
);

CREATE TABLE valuation_consensus_records(
 consensus_id TEXT PRIMARY KEY,
 security_id TEXT NOT NULL REFERENCES securities,
 valuation_date TEXT NOT NULL,
 bear_value TEXT, base_value TEXT, bull_value TEXT,
 currency TEXT,
 method_weights_json TEXT NOT NULL,
 method_valuation_ids_json TEXT NOT NULL,
 aggregation_version TEXT NOT NULL,
 confidence TEXT NOT NULL,
 created_at TEXT NOT NULL,
 UNIQUE(security_id,valuation_date,aggregation_version)
);
