CREATE TABLE government_yield_curve_vintages(
 curve_vintage_id TEXT PRIMARY KEY,
 source_result_id INTEGER NOT NULL,
 curve_date TEXT NOT NULL,
 currency TEXT NOT NULL CHECK(currency='UZS'),
 rate_basis TEXT NOT NULL CHECK(rate_basis='NOMINAL'),
 compounding TEXT NOT NULL CHECK(compounding='CONTINUOUS'),
 methodology TEXT NOT NULL,
 source_id TEXT NOT NULL REFERENCES data_sources,
 source_url TEXT NOT NULL,
 methodology_url TEXT NOT NULL,
 retrieved_at TEXT NOT NULL,
 raw_results_document_id TEXT NOT NULL REFERENCES raw_documents,
 raw_points_document_id TEXT NOT NULL REFERENCES raw_documents,
 source_api_version TEXT,
 provenance_class TEXT NOT NULL CHECK(provenance_class='AUTHORITATIVE_SOURCE'),
 UNIQUE(source_result_id,retrieved_at)
);

CREATE INDEX government_curve_asof
 ON government_yield_curve_vintages(curve_date,retrieved_at);

CREATE TABLE government_yield_curve_points(
 curve_point_id TEXT PRIMARY KEY,
 curve_vintage_id TEXT NOT NULL REFERENCES government_yield_curve_vintages ON DELETE RESTRICT,
 source_point_id INTEGER NOT NULL,
 tenor_label TEXT NOT NULL,
 tenor_days INTEGER NOT NULL CHECK(tenor_days>=0),
 maturity_date TEXT NOT NULL,
 zero_rate_percent TEXT NOT NULL,
 discount_factor TEXT NOT NULL,
 forward_rate_percent TEXT,
 observation_class TEXT NOT NULL CHECK(observation_class='OBSERVED'),
 UNIQUE(curve_vintage_id,source_point_id),
 UNIQUE(curve_vintage_id,tenor_days)
);

CREATE TABLE valuation_method_eligibility(
 eligibility_id TEXT PRIMARY KEY,
 security_id TEXT NOT NULL REFERENCES securities,
 valuation_date TEXT NOT NULL,
 method TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN('EXECUTABLE','PARTIALLY_SUPPORTED','UNSUPPORTED')),
 blocker_codes_json TEXT NOT NULL,
 available_inputs_json TEXT NOT NULL,
 reference_curve_vintage_id TEXT REFERENCES government_yield_curve_vintages,
 model_version TEXT NOT NULL,
 assessed_at TEXT NOT NULL,
 UNIQUE(security_id,valuation_date,method,model_version)
);
