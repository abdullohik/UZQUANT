CREATE TABLE valuation_assumption_details(
 assumption_id TEXT PRIMARY KEY REFERENCES valuation_assumption_inputs,
 nominal_real_basis TEXT NOT NULL CHECK(nominal_real_basis IN('NOMINAL','REAL','NOT_APPLICABLE')),
 source_date TEXT NOT NULL,
 source_url TEXT NOT NULL,
 methodology TEXT NOT NULL,
 derivation_json TEXT NOT NULL,
 confidence TEXT NOT NULL CHECK(confidence IN('HIGH','MEDIUM','LOW')),
 assumption_version TEXT NOT NULL,
 created_at TEXT NOT NULL
);

CREATE TABLE valuation_reconciliations(
 reconciliation_id TEXT PRIMARY KEY,
 valuation_id TEXT NOT NULL UNIQUE REFERENCES valuation_records,
 independently_computed_bear TEXT NOT NULL,
 independently_computed_base TEXT NOT NULL,
 independently_computed_bull TEXT NOT NULL,
 stored_bear TEXT NOT NULL,
 stored_base TEXT NOT NULL,
 stored_bull TEXT NOT NULL,
 maximum_absolute_difference TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN('PASSED','FAILED')),
 calculation_json TEXT NOT NULL,
 reconciliation_version TEXT NOT NULL,
 created_at TEXT NOT NULL
);
