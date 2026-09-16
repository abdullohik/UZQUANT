# Phase 18 Initial Shadow State

Decision timestamp: `2026-09-16T07:09:40.816778+00:00`

Prospective snapshot: `318617d7-3038-4ad0-b1ce-9a4451f0167a`

## Initial result

The first prospective snapshot was created from the actual stored operational state without running a source refresh or overriding Phase 17 health.

| Item | Result |
|---|---:|
| Shadow portfolios | 3 |
| Signals captured | 7 |
| Eligible securities | 0 |
| Positions | 0 |
| Paper orders | 0 |
| Paper fills | 0 |
| NO_FILL orders | 0 |
| Cash weight | 100% in every style |
| Prospective performance observations | 0 |

No `NO_FILL` row exists initially because no order was admissible or submitted. This is distinct from an admissible order that later encounters no executable future volume.

## Shadow portfolios

| Style | Initial cash | Current cash | Status | Positions |
|---|---:|---:|---|---:|
| CONSERVATIVE | UZS 20,000,000 | UZS 20,000,000 | DEGRADED | 0 |
| BALANCED | UZS 20,000,000 | UZS 20,000,000 | DEGRADED | 0 |
| HIGH_CONVICTION | UZS 20,000,000 | UZS 20,000,000 | DEGRADED | 0 |

## Captured research states

Seven securities with current stored signals were captured:

- five `DATA_INSUFFICIENT`;
- one `HOLD`;
- one `LIQUIDITY_TRAP`.

All seven are `STALE_BLOCKED`. Exact signal IDs, confidence, gates, data snapshots, valuation/liquidity references, and model versions are preserved in `prospective_security_states`.

## Preserved operational blockers

The aggregate upstream state is `FAILED`. The snapshot retained these exact blockers:

- `security_master:FAILED`;
- `market_data:STALE`;
- `financial_documents:STALE`;
- `financial_normalization:STALE`;
- `fundamentals:STALE`;
- `valuation:STALE`;
- `liquidity:STALE`;
- `factors:STALE`;
- `confidence:STALE`;
- `risk_gates:STALE`;
- `signals:STALE`.

The macro pipeline's degraded state remains in the full captured health JSON, although it is contextual rather than part of the direct executable-order dependency set.

## Interpretation

This is the correct initial prospective outcome: the system recorded what it knew, including failure and staleness, and generated no fictional order or fill. It does not establish model performance, forecast accuracy, confidence calibration, or validation. Those conclusions require future timestamped signals and actual subsequent market evidence.
