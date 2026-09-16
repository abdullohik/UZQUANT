# UZQUANT Known Limitations

## Software limitations

- Canonical issuer IDs are currently derived from normalized legal name, creating a critical silent-collision risk.
- Financial reports are resolved by ticker without publication-date validity or corroborating permanent issuer identifiers.
- A ticker string occurring in a document is insufficient entity verification.
- Normalized financial observations can be deleted and recreated/updated under the same logical identity during reparse.
- Prospective snapshots do not embed a complete immutable normalized-financial payload.
- Generic source-schema checks are not wired into production parser boundaries.
- `DEGRADED` dependencies are not treated as blocking/stale by the generic scheduler and are omitted from security freshness warnings.
- The event/anomaly engine covers only a conservative subset of planned anomaly families.
- External scheduling, authentication, multi-user authorization, deployment hardening, backups, recovery drills, and alert delivery are not implemented.
- Paper dividends have deterministic accounting mechanics but no end-to-end scheduled portfolio event processor; broader corporate actions are incomplete.

## Source-data limitations

- RSE automation is currently unavailable; the security master is `FAILED` and direct dependants are `STALE`.
- RSE is registered `PARTIAL`, and no supported official bulk market-data API is verified.
- Historical bid/ask, depth, queue position, intraday continuity, and price-limit histories are unavailable.
- Reporting perimeter is unknown for 16 of 17 financial documents.
- Eighty-one normalized financial observations have unspecified source units.
- Preferred-share charter/issue rights are not verified at high confidence.
- Ownership is sparse; free float and concentration are generally unavailable.
- No complete corporate-action, dividend, historical identifier, listing/delisting, or failed-security master exists.
- No verified peer-multiple, discount-rate, country-risk, and valuation-assumption set supports current valuations.
- Macro original release/revision dates are absent for all 259 observations; only first-observed vintages are available.

## Historical-data limitations

- Market history contains only 20 dates from 2026-08-17 through 2026-09-15.
- Historical universe membership is not reconstructable because listing/delisting dates are absent.
- There is no verified total-return series or Uzbekistan benchmark series.
- Historical financial, ownership, rights, actions, and signal vintages are insufficient for strategy reconstruction.
- There are zero legitimate historical signals with a subsequent execution/holding window, zero backtest orders, and zero fills.
- Survivorship bias, execution realism, and capacity cannot be empirically quantified over a useful period.

## Model limitations

- Every stored valuation is `VALUATION_INSUFFICIENT`; there is no real fair-value range to validate.
- Phase 14 is `UNRELIABLE — INSUFFICIENT EVIDENCE`; strategy success or failure is not established.
- Sector fields are incomplete and some routing relies on known source URL categories.
- Factor coverage is sparse; momentum, dividend, governance, and catalyst evidence are often unavailable.
- Liquidity thresholds are provisional and depth-free slippage remains an uncertainty range.
- No empirical confidence calibration, forecast calibration, parameter stability, or factor monotonicity result exists.
- Current portfolio output cannot validate allocation or risk behavior with real eligible positions.

## Market-structure limitations

- Last prices may be stale and are not assumed executable.
- Many securities trade infrequently or not at all during the observed window.
- No order-book depth exists to support precise impact or child-order estimates.
- Ownership concentration and free float are unknown for most securities.
- Large reported price moves may reflect one or very few trades.
- Capacity can fall sharply with AUM, but real portfolio capacity is not measurable with zero eligible positions.

## Prospective-evidence limitations

- There is one prospective decision snapshot and seven security states, all captured during a failed/stale production condition.
- There are zero eligible paper orders, fills, positions, return observations, or forecast outcomes.
- Confidence calibration and model drift are `INSUFFICIENT_SAMPLE`.
- No elapsed prospective horizon exists to evaluate false positives, missed opportunities, drawdown, execution shortfall, or valuation error.
- A zero-position, 100%-cash state is correct but supplies no evidence of investment performance.
