# Phase 17 — Continuous Operations

## Scope and safety

Phase 17 adds an operator-controlled scheduling layer around the existing production ingestors and analytical engines. It does not execute trades, bypass access controls, repair suspicious data automatically, or weaken any existing research gate. All observations, signals, runs, anomalies, and transitions remain versioned or append-only according to their existing domain rules.

The operator entry points are:

```text
python -m uzquant operations-tick
python -m uzquant operations-tick --force
python -m uzquant operations-tick --pipeline market_data
python -m uzquant operations-check
```

The first command runs only due pipelines. `--force` is for controlled validation and recovery. A named pipeline limits the run without changing its dependency checks. An external operating-system scheduler may invoke the first command; UZQUANT itself does not install a daemon.

## Pipeline schedule and dependency graph

| Pipeline | Refresh interval | Direct dependencies |
|---|---:|---|
| security_master | 24 hours | — |
| market_data | 6 hours | security_master |
| financial_documents | 24 hours | security_master |
| corporate_actions | 24 hours | security_master |
| dividends | 24 hours | security_master |
| ownership | 7 days | security_master |
| security_rights | 7 days | security_master |
| events | 6 hours | security_master |
| macro | 24 hours | — |
| financial_normalization | 24 hours | financial_documents |
| fundamentals | 24 hours | financial_normalization |
| valuation | 24 hours | fundamentals, security_rights |
| liquidity | 6 hours | market_data |
| factors | 6 hours | valuation, liquidity, fundamentals |
| confidence | 6 hours | factors |
| risk_gates | 6 hours | confidence |
| signals | 6 hours | risk_gates |

Pipelines sharing one underlying production handler are coalesced into one source call. This prevents corporate actions, dividends, ownership, and rights—or factor, confidence, risk-gate, and signal labels—from hammering the same source or recomputing the same snapshot four times.

## Run and health records

`scheduled_pipeline_runs` is the immutable run ledger. It records the run ID, pipeline, timestamps, status, source, attempted/succeeded/failed counts, error, retry state, data version, next expected refresh, and upstream state. `pipeline_health` is the current projection used by the API and interface.

Statuses have strict meanings:

- `HEALTHY`: the handler completed with no reported record failures.
- `DEGRADED`: the handler completed but reported one or more source/record failures.
- `FAILED`: all controlled attempts failed, or no handler exists.
- `STALE`: execution was blocked by a failed or stale direct dependency.

The scheduler retries exceptions at most three times with bounded exponential backoff. It never attempts to circumvent authentication, CAPTCHA, anti-bot measures, rate limits, or terms restrictions. A persistent source failure is stored as `FAILED`; dependent pipelines are stored as `STALE`. Successful recovery resolves related operational alerts while preserving the full run history.

## Idempotency and source integrity

Phase 17 invokes the existing idempotent domain writers. Their logical identifiers, source identifiers, content hashes, effective dates, unique constraints, and immutable version records remain authoritative. Scheduler reruns add run-ledger rows but do not create duplicate logical source records. Financial documents remain content-hash deduplicated, and research signals remain append-only.

`detect_source_schema` and `record_source_schema_check` compare required and observed fields. Missing required fields fail closed and can create a deduplicated `SOURCE_SCHEMA_CHANGE` alert. Unexpected extra fields are retained in the check result for investigation but do not alone justify interpreting them. Source-specific parser validation remains responsible for invoking the check at the deterministic extraction boundary.

## Anomalies and alerts

`research_anomalies` stores investigation flags separately from signals. The production scan currently detects extreme consecutive price moves, unusual volume changes, and verified shares-outstanding changes. The mechanism stores evidence, source-record IDs, detector version, status, and a stable deduplication key. It does not alter prices, statements, valuations, or signals.

`research_alerts` stores deduplicated operational/research notifications. `alert_rules` makes each supported alert type independently enableable and sets its minimum severity. Supported types cover disclosures, financial reports, dividends, capital and ownership changes, governance, valuation/signal state changes, liquidity and data-quality deterioration, failed/stale/degraded pipelines, source-schema changes, and general anomalies. Delivery to an external messaging service is intentionally out of scope; alerts are exposed through the Phase 16 interface/API.

## Signal transitions

`signal_state_transitions` is append-only and unique by new signal ID. Each genuine state change records old/new signal IDs and states, the gate/confidence change driver, timestamp, snapshot, and model/scoring/valuation/liquidity versions. Existing signal history is never overwritten. An alert is emitted for each new transition.

## API and interface integration

`GET /api/v1/pipelines` presents current health, last success, expected refresh, staleness/error, retry state, affected downstream pipelines, recent runs, and open alerts. `GET /api/v1/operations` provides the full operational payload: health, run history, anomalies, alerts, and signal transitions. Security research responses add `STALE_DATA` or `STALE_FINANCIALS` warnings when relevant pipeline health is failed/stale/degraded.

## Known limitations

- Scheduling requires an external periodic invoker; no always-on daemon is installed.
- Public-source availability remains outside UZQUANT's control. A source outage intentionally propagates visible staleness.
- Alert delivery is API/UI based; email, SMS, and brokerage actions are excluded.
- Automated anomaly coverage is deliberately conservative. Unimplemented anomaly families are not inferred or silently repaired.
- A healthy run means the implemented handler completed; it does not imply that every public source published new records.
