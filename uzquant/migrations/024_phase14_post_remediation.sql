PRAGMA foreign_keys=ON;

ALTER TABLE validation_runs ADD COLUMN phase13_classification TEXT;
ALTER TABLE validation_runs ADD COLUMN evidence_outcome TEXT;

ALTER TABLE experiment_registry ADD COLUMN strategy_version TEXT;
ALTER TABLE experiment_registry ADD COLUMN data_snapshot_id TEXT;
ALTER TABLE experiment_registry ADD COLUMN period_start TEXT;
ALTER TABLE experiment_registry ADD COLUMN period_end TEXT;
ALTER TABLE experiment_registry ADD COLUMN training_start TEXT;
ALTER TABLE experiment_registry ADD COLUMN training_end TEXT;
ALTER TABLE experiment_registry ADD COLUMN validation_start TEXT;
ALTER TABLE experiment_registry ADD COLUMN validation_end TEXT;
ALTER TABLE experiment_registry ADD COLUMN oos_start TEXT;
ALTER TABLE experiment_registry ADD COLUMN oos_end TEXT;
