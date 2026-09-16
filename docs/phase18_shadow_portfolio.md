# Phase 18 — Prospective Shadow Portfolio and Paper Trading

## Purpose and boundaries

Phase 18 starts a prospective, point-in-time evidence record. It uses no real capital, has no broker integration, and cannot place a live order. It does not reinterpret reconstructed history as prospective evidence. The initial decision snapshot retains the actual Phase 17 pipeline failure and downstream staleness.

The operator command is:

```text
python -m uzquant initialize-shadow-portfolios
```

This command captures a new immutable decision point and initializes the existing `CONSERVATIVE`, `BALANCED`, and `HIGH_CONVICTION` styles. It does not refresh sources, clear health states, weaken admission rules, or force orders.

## Prospective decision snapshots

`prospective_decision_snapshots` is append-only and protected by database triggers against update and deletion. Each row preserves:

- the timezone-aware decision timestamp and trigger;
- the exact pipeline-health projection and aggregate upstream state;
- security universe and source observation/document IDs then known;
- valuation, factor, and signal IDs then known;
- portfolio state and execution assumptions;
- portfolio, snapshot, and execution model versions.

`prospective_security_states` is also immutable. It binds each captured security to the exact signal, valuation, liquidity assessment, market state, financial-document set, factors, position sizing, confidence, risk gates, admission decision, rejection reasons, and model versions available at that decision time. Queries use publication, observation-first-seen, analytical as-of, creation, and generation cutoffs. Later evidence cannot alter an earlier row.

## Shadow portfolios and admission

`shadow_portfolios` stores the three existing Phase 15 styles. Initial cash is UZS 20 million per style. Portfolio admission uses the captured signal and the existing Phase 15 validation requirements. In addition, a security is `STALE_BLOCKED` when any critical research dependency is not healthy.

No position is created merely because a portfolio would otherwise be empty. A failed security master, stale market data, stale risk gates/signals, `DATA_INSUFFICIENT`, `LIQUIDITY_TRAP`, unavailable valuation, or unvalidated model state remains binding. A 100%-cash shadow portfolio is a complete and valid result.

## Paper orders and execution

`paper_orders` references one immutable snapshot, one exact signal version, one shadow portfolio, and one security. Submission is allowed only when the captured security admission is `ELIGIBLE` and the snapshot upstream state is `HEALTHY`; otherwise the attempted order is stored as `REJECTED` with `PROSPECTIVE_ADMISSION_BLOCKED`.

Open orders may consume only market observations whose `first_seen_at` is after submission and no later than the evaluation time. Fill capacity is limited to observed share volume multiplied by the recorded participation rate. The engine supports partial and multi-day fills, observed spread where present, explicit slippage and fee inputs, and source-observation lineage. It never grants a fill from a stale last price or zero/no-trade observation. An open order with no executable future evidence becomes `NO_FILL`.

`paper_fills` records reference and fill price, observed volume, shares, fees, slippage, participation, timestamp, and exact source observation. `paper_positions` and `paper_portfolio_ledger` account for cash, shares, cost basis, realized P&L, dividends, fees, and each cash-changing event.

Verified dividends affect paper cash only after both their announcement and payment dates are known. Unverified or future dividends remain excluded.

## Outcomes, calibration, and drift

`paper_signal_outcomes` provides fields for signal, realized and unrealized returns, execution shortfall, time to fill, fill ratio, favorable/adverse excursion, drawdown, forecast error, and outcome classification. Every row exposes sample size and can remain `INSUFFICIENT_FUTURE_EVIDENCE`.

`paper_drift_assessments` stores factor, valuation, liquidity, market-structure, data-availability, and signal-frequency comparisons. The initial assessment is `INSUFFICIENT_SAMPLE`. No confidence recalibration or validation claim is permitted from a tiny prospective sample.

False positives, missed opportunities, correctly rejected liquidity traps, and data-quality blocks can be classified only after genuine subsequent evidence exists. BUY hit rate alone is not the evaluation objective.

## Interface

`GET /api/v1/paper-trading` exposes shadow portfolios, immutable snapshots, captured security states and historical signals, open/rejected orders, fills, signal outcomes, valuation-forecast status, confidence-calibration evidence, execution shortfall, and drift assessments. The Phase 16 interface adds a Paper Trading view; it performs no investment calculations in the browser.

## Known limitations

- The initial state has no eligible securities, orders, positions, fills, or prospective return observations.
- No verified future market observations exist after the initial snapshot yet, so performance and forecast metrics are unavailable.
- Fee rates must be explicitly configured before an otherwise eligible order is evaluated; they are not guessed.
- Bid/ask spread, depth, and intraday evidence remain unavailable for much of the market and are never fabricated.
- Confidence calibration and drift require a substantially larger prospective sample and elapsed horizon.
- Corporate-action portfolio processing beyond verified cash dividends requires future verified events and additional prospective evidence.
