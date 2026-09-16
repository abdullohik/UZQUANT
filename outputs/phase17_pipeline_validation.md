# Phase 17 Pipeline Validation

Validation date: 2026-09-16 (Asia/Tashkent)

## Result

Phase 17 is operational and fail-safe. Seventeen pipelines are registered. A complete successful controlled cycle was followed by a real source-unavailable cycle. The latter correctly failed the security master after bounded retries and propagated staleness through every dependent research layer. No stale downstream result was represented as current.

## Real cycles

The successful cycle at `2026-09-16T06:51:17.582337+00:00` completed all 17 pipeline health projections as `HEALTHY`. It processed, among other existing production outputs, 12 financial-document results, 12 fundamental calculations, 31 valuation cases, seven liquidity assessments, and seven securities through each scoring/signal projection. Several source handlers reported zero new logical records, which is valid for an idempotent rerun.

The subsequent cycle at `2026-09-16T06:54:12.420566+00:00` encountered a real failure retrieving the configured RSE asking-prices endpoint. Security-master ingestion exhausted three attempts and was recorded `FAILED`. Market data, financial documents, corporate data, events, normalization, fundamentals, valuation, liquidity, factors, confidence, risk gates, and signals were recorded `STALE` with their explicit upstream dependency. Macro completed `DEGRADED` with 11 reported source errors. This final state is intentionally preserved rather than falsely marked healthy.

Current health after that validation cycle:

| Status | Pipelines |
|---|---:|
| FAILED | 1 |
| DEGRADED | 1 |
| STALE | 15 |
| HEALTHY | 0 |

The run ledger contains 51 Phase 17 pipeline-run records across three controlled cycles. Historical successful runs remain queryable.

## Fail-safe scenarios

| Scenario | Evidence/result |
|---|---|
| Source unavailable | Real RSE retrieval failure exhausted bounded retries; security master became `FAILED`. |
| Parser failure | Simulated runner exception persisted its exception and retry state, then emitted a critical failure alert. |
| Stale market data | A failed/stale security-master dependency blocked market data; liquidity then became stale; scoring/signals were blocked. |
| New financial document | Existing real financial ingestion returned 12 document results in the successful cycle; document identity/content-hash rules remained active. |
| Changed share count | Detector compares successive verified `share_capital_observations` and creates an evidence-linked `SHARES_OUTSTANDING_CHANGE` anomaly. |
| Duplicate document | Production store currently contains 17 financial documents and 17 distinct content hashes; idempotent reruns did not add a duplicate hash. |
| Conflicting source data | Conflicts remain explicit source/validation records; they are not auto-resolved or promoted into repaired values. |
| Source schema change | Missing required columns return `FAILED` and create a configurable, deduplicated `SOURCE_SCHEMA_CHANGE` alert. |
| Recovery | A focused simulated recovery changed health back to `HEALTHY` and resolved its prior operational alert without deleting either run. |

## Anomaly and transition validation

The real stored-data scan created four deduplicated `UNUSUAL_VOLUME` anomalies. Repeating the scan created no duplicate anomalies. Two genuine historical signal state changes were captured with their old/new states, data snapshots, change-driver evidence, and model lineage. They generated two deduplicated signal-state alerts. Anomalies remain research flags and never become signals automatically.

## Idempotency evidence

- Scheduler due-time validation showed an immediate second non-forced invocation created no run.
- Alert and anomaly deduplication keys prevented duplicate logical notifications.
- Signal transition uniqueness is enforced by the new signal ID.
- Existing domain unique keys and financial content hashes remained unchanged.
- The production database held 76 securities, 140 market observations, and 17 uniquely hashed financial documents after the cycles; repeated orchestration did not manufacture a new universe or duplicate documents.

## Interface validation

The Phase 16 API now exposes operational health and full Phase 17 detail. Pipeline payloads include current status, last success, expected refresh, stale/error state, retry state, downstream impact, recent runs, and open alerts. Security detail warnings inherit market and financial staleness. Existing read-only interface behavior remains intact.

## Final interpretation

The present `FAILED`/`DEGRADED`/`STALE` state is evidence that fail-closed behavior works; it is not a claim that upstream data is current. Operators should retry on the normal configured cadence. Recovery may restore health only after the authoritative handler completes successfully. No risk gate, signal, valuation, or stale observation was forced through this validation.
