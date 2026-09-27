CREATE TABLE valuation_assumption_observation_lineage(
 assumption_id TEXT NOT NULL REFERENCES valuation_assumption_inputs,
 observation_version_id TEXT NOT NULL REFERENCES financial_observation_versions,
 input_role TEXT NOT NULL,
 transformation TEXT NOT NULL,
 created_at TEXT NOT NULL,
 PRIMARY KEY(assumption_id,observation_version_id,input_role)
);
