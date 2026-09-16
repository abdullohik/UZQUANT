# Post-audit HIGH hardening forensic trace

## Cross-finding chain

```text
raw source payload
  → immutable raw document/hash
  → production semantic schema contract
      → cosmetic/compatible: continue with recorded check
      → breaking: SOURCE_SCHEMA_CHANGED + alert + FAILED, no accepted records
  → immutable normalized financial version
  → exact observation-version lineage
  → fundamentals / valuation / factors / signal
  → health context (HEALTHY / DEGRADED / STALE / FAILED)
  → immutable FULL_FREEZE_V1 prospective evidence bundle + SHA-256
```

## Normalized lineage evidence

- `financial_observation_versions`: 342 migrated production versions.
- `analytical_observation_lineage`: 2,265 backfilled metric/valuation links.
- `signal_observation_lineage`: 4,774 historical links labeled `LEGACY_INFERRED`.
- New signal captures use `EXACT` lineage.
- Superseded versions remain queryable by publication/knowledge date.
- Database triggers reject deletion or mutation of financial values.

The original 342 legacy rows remain in place for compatibility; they were not deleted. Authoritative production readers use the versioned table. The earlier 81 identity-invalidated observations remain invalidated and do not become valid through this migration.

## Schema-change evidence

Production parsers now call the contract boundary after raw archival and before accepted normalized/market/macro records. Adversarial payloads demonstrated:

| Change | Classification/action |
|---|---|
| Cosmetic markup or reordered semantic fields | COSMETIC_CHANGE; continue |
| Added harmless field | COMPATIBLE_SCHEMA_CHANGE; continue and record |
| Renamed/missing required field | BREAKING_SCHEMA_CHANGE; fail closed |
| Changed unit/date semantic marker | BREAKING_SCHEMA_CHANGE; fail closed |
| Wrong field count or malformed payload | BREAKING_SCHEMA_CHANGE; fail closed |
| Numeric but shifted value | BREAKING_SCHEMA_CHANGE; fail closed |

No real parser was forced against the unavailable RSE source, so the production database correctly has zero post-migration schema-check events. This is absence of a new ingestion attempt, not fabricated successful validation.

## Health propagation evidence

Tests establish:

- one degraded dependency → downstream result `DEGRADED` with `UPSTREAM_DEGRADED` reason;
- degraded plus stale dependency → downstream `STALE`;
- dependency recovery → downstream can return `HEALTHY` on a successful run;
- research API health context exposes status, freshness, reasons, sources, dependencies, generated time, and as-of time;
- new prospective snapshots freeze the full health context.

Current real health remains:

| State | Count |
|---|---:|
| FAILED | 1 |
| DEGRADED | 1 |
| STALE | 15 |

## Snapshot evidence

The one existing Phase 18 snapshot is marked `LEGACY_SNAPSHOT_LIMITED`; it was not rewritten. New snapshots use `FULL_FREEZE_V1` and preserve identity, source documents, normalized versions, metrics, valuation inputs/assumptions, factors, liquidity, confidence, gates, pipeline health, portfolio state, and execution assumptions in an immutable hashed bundle.

An adversarial reconstruction remained byte-equivalent by canonical JSON hash after later normalized values, taxonomy/parser versions, and signal/model versions were added.

## Final audit state

- Tests: **187 passed**.
- Foreign-key violations: **0**.
- Critical findings: **0**.
- Remaining four Phase 19 engineering HIGH findings: **0**, with legacy rows/snapshots explicitly qualified rather than upgraded falsely.
- Readiness: **EXPERIMENTAL**.
- Live trading: disabled.
- Phase 20: not started.
