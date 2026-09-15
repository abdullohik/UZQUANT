PRAGMA foreign_keys=ON;

CREATE TABLE macro_series(
  series_id TEXT PRIMARY KEY,
  series_code TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  category TEXT NOT NULL,
  frequency TEXT NOT NULL,
  unit TEXT NOT NULL,
  currency TEXT,
  source_id TEXT NOT NULL REFERENCES data_sources,
  source_url TEXT NOT NULL,
  release_date_basis TEXT NOT NULL,
  revision_policy TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE macro_observations(
  observation_id TEXT PRIMARY KEY,
  series_id TEXT NOT NULL REFERENCES macro_series,
  period_start TEXT NOT NULL,
  period_end TEXT NOT NULL,
  initial_release_date TEXT,
  revision_date TEXT,
  vintage_known_at TEXT NOT NULL,
  value TEXT NOT NULL,
  unit TEXT NOT NULL,
  currency TEXT,
  source_url TEXT NOT NULL,
  source_document_id TEXT NOT NULL REFERENCES raw_documents,
  retrieved_at TEXT NOT NULL,
  parser_version TEXT NOT NULL,
  observation_status TEXT NOT NULL CHECK(observation_status IN('REPORTED','REVISED')),
  UNIQUE(series_id,period_start,period_end,vintage_known_at)
);
CREATE INDEX macro_asof_lookup ON macro_observations(series_id,vintage_known_at,period_end);

CREATE TABLE macro_regimes(
  regime_id TEXT PRIMARY KEY,
  as_of_date TEXT NOT NULL,
  label TEXT NOT NULL,
  state TEXT NOT NULL CHECK(state IN('ACTIVE','INACTIVE','UNAVAILABLE')),
  evidence_json TEXT NOT NULL,
  rules_version TEXT NOT NULL,
  generated_at TEXT NOT NULL,
  UNIQUE(as_of_date,label,rules_version)
);

CREATE TABLE sector_macro_exposures(
  exposure_id TEXT PRIMARY KEY,
  sector_code TEXT NOT NULL,
  macro_series_code TEXT NOT NULL,
  transmission_channel TEXT NOT NULL,
  directional_effect TEXT NOT NULL,
  evidence_basis TEXT NOT NULL,
  basis_type TEXT NOT NULL CHECK(basis_type IN('ECONOMIC_ASSUMPTION','EMPIRICAL_EVIDENCE')),
  mapping_version TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(sector_code,macro_series_code,transmission_channel,mapping_version)
);
