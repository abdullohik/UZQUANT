# Post-audit HIGH findings hardening

## Disposition

The four Phase 19 engineering HIGH findings were addressed without changing investment thresholds, risk gates, signals, portfolios, or source-health history. Readiness remains **EXPERIMENTAL** because the market/source/model evidence needed for research readiness is still absent. No live trading capability was enabled.

## H-01 — Immutable normalized-financial lineage

**Status: RESOLVED for authoritative production processing; legacy lineage explicitly qualified.**

Migration 031 introduced append-only `financial_observation_versions`. Each version stores the source document/raw row, issuer, concept, period, publication and knowledge dates, raw and normalized values, currency, unit, perimeter, standard, audit state, extraction method, parser/taxonomy/normalization versions, confidence, validation state, creation time, and supersession links. Triggers reject value mutation and deletion.

Financial HTML and attachment ingestion now append versions. Parser, taxonomy, unit, and normalization corrections create successors; they do not overwrite prior values. Fundamentals and valuation read exact current version IDs, and `analytical_observation_lineage` retains links to those versions. New prospective signals receive exact version links. Historical signals were backfilled as `LEGACY_INFERRED` because the old schema did not capture exact version IDs; this limitation is not disguised as exact lineage.

## H-02 — Source-schema alerting in production parsers

**Status: RESOLVED in code and adversarial validation; no real post-migration schema event has occurred.**

Versioned semantic contracts and checks are now invoked inside the RSE security-master, RSE market-history, Openinfo financial-document, Openinfo attachment path, and CBU macro ingestion boundaries. Raw evidence is archived before contract enforcement. Contracts distinguish:

- `COSMETIC_CHANGE`: semantic schema unchanged;
- `COMPATIBLE_SCHEMA_CHANGE`: required fields retained with harmless additions;
- `BREAKING_SCHEMA_CHANGE`: required structure missing or shifted.

A breaking change raises `SourceSchemaChanged`, prevents normal record ingestion, records `SOURCE_SCHEMA_CHANGED`, emits a `SOURCE_SCHEMA_CHANGE` alert, and marks the affected registered pipeline failed. Tests cover renamed/missing fields, reordered fields, added fields, malformed/empty payloads, changed unit/date semantics, and numeric-looking shifted data.

## H-03 — Complete DEGRADED propagation and display

**Status: RESOLVED.**

Scheduler dependency evaluation now distinguishes `DEGRADED` from `HEALTHY`, `STALE`, and `FAILED`. A healthy downstream calculation fed by degraded evidence is itself `DEGRADED`; stale/failed dependencies still block it as `STALE`. Recovery returns downstream processing to `HEALTHY` only after dependencies recover.

Research API universe, security, portfolio, pipeline, and paper-trading responses expose a common health context containing upstream health, freshness, reason, source, affected dependencies, generated time, and as-of time. Security warnings now include degraded financial and market dependencies. Prospective snapshots retain the complete health payload.

## H-04 — Full prospective normalized-financial freeze

**Status: RESOLVED for new snapshots.**

New `FULL_FREEZE_V1` snapshot evidence contains immutable, hashed payloads for canonical identity/share class, raw document hashes, full normalized observation versions, fundamental metrics, valuations and assumptions, factors, liquidity, confidence/risk gates, pipeline health/freshness, portfolio decisions, execution assumptions, and model versions. Reconstruction recomputes the payload hash and verifies equality.

Tests prove a snapshot reconstructs identically after later parser, taxonomy, normalization, signal, and model-version changes. The original Phase 18 snapshot was not rewritten; it is marked `LEGACY_SNAPSHOT_LIMITED`.

## Migration and production audit

| Item | Result |
|---|---:|
| Schema migration | 031 |
| Legacy normalized rows preserved as immutable versions | 342 |
| Analytical observation-version links backfilled | 2,265 |
| Legacy signal-version links marked inferred | 4,774 |
| Existing snapshots marked `LEGACY_SNAPSHOT_LIMITED` | 1 |
| Historical snapshots rewritten | 0 |
| Foreign-key violations | 0 |
| Source-schema checks from real post-migration ingestion | 0 — no source refresh was forced |

The existing RSE failure was not cleared or retried merely for this sprint. Production operational validation preserved one `FAILED`, one `DEGRADED`, and 15 `STALE` pipelines. Existing `STALE_BLOCKED` states, zero paper orders/fills/positions, and 100% cash remain intact.

## Tests and adversarial results

The full suite passes: **187 tests passed**. New cases cover restatement/source replacement, parser-version changes, taxonomy and unit corrections, mutation/deletion rejection, schema renaming/reordering/missing/extra/shifted fields, malformed payloads, degraded propagation and recovery, degraded-plus-stale precedence, API warning visibility, full snapshot reconstruction after taxonomy/model changes, historical supersession, and legacy snapshot labeling.

## Readiness reassessment

Remaining critical findings: **0**.

Remaining Phase 19 engineering HIGH findings: **0**, subject to the explicit legacy qualifications above. Structural risks and data limitations remain: no available real valuation, incomplete units/perimeters/restatements, limited rights/ownership evidence, 20 market dates, absent depth/spread history, incomplete historical universe and macro vintages, no valid backtest/OOS sample, and no prospective fills/outcomes. These are not repaired by lineage engineering.

Final classification remains **EXPERIMENTAL**. `docs/readiness.md` was not changed because the classification did not change.
