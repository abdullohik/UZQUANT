# Phase 13 Post-Remediation Backtest Rerun

## Classification

**BACKTEST_INSUFFICIENT**

The existing Phase 13 framework remains structurally compatible with the post-Remediation-C database and analytical outputs. A legitimate historical strategy backtest cannot currently be performed. The result reflects missing historical evidence, not profitability and not a new remediation failure.

No valuation, confidence, liquidity, factor, or risk threshold was changed. No historical signal, universe member, price, return, benchmark, fee, spread, or fill was manufactured.

## Compatibility audit

The existing implementation retains the required controls:

- `backtest_snapshots` stores the eligible universe and source-record IDs for identifiers, prices, financials, ownership, rights, events, actions, dividends, macro vintages, signals, and model versions.
- financial documents are selected by publication date, with later restatements unavailable before their own publication;
- macro observations are selected by vintage-known timestamp;
- universe membership uses stable security IDs and listing/delisting validity rather than current survival;
- raw observations are separate from adjusted and total-return series;
- only positive observed volume can fill an order;
- participation limits, execution delay, finite fill windows, partial fills, rejected orders, spread, slippage, and separate fee components are supported;
- verified dividends, splits, and delisting outcomes remain security-specific and point-in-time;
- every order and fill has source/model lineage and is append-only.

One concrete compatibility defect was fixed: repeated current ingestion and signal-generation timestamps could be counted as historical universe/signal dates. Readiness now measures analytical `as_of_date` and actual listing/delisting validity dates. A rerun of the same current snapshot can no longer masquerade as historical evidence.

## Verified historical coverage

| Data family | Earliest | Latest | Observations / dates | Point-in-time integrity | Known gaps | Backtest use |
|---|---|---|---|---|---|---|
| Security identifiers | 2026-09-14 known | 2026-09-15 known | 298 / 2 ingestion dates | `known_at`, validity fields retained | repeated current snapshots; not historical ticker chronology | Insufficient |
| Listings/universe | 2026-09-14 known | 2026-09-15 known | 149 / 2 ingestion dates | stable security IDs retained | zero listing dates and zero delisting dates | Insufficient: `HISTORICAL_UNIVERSE_INSUFFICIENT` |
| Raw market observations | 2026-08-17 | 2026-09-15 | 140 / 20 trade dates / 7 securities | trade date, first-seen timestamp, raw series retained | short rolling window; one security represented by no-trade placeholders | Insufficient |
| Trading calendar | 2026-08-17 | 2026-09-15 | implicit 20 observed dates | no-trade status is explicit | no complete exchange calendar | Insufficient |
| Financial documents | 2018-07-13 | 2026-07-10 | 17 documents; 12 explicitly MATCHED | publication dates and original documents retained | sparse vintages; unknown reporting perimeter; no historical factor snapshots | Source evidence usable, strategy reconstruction insufficient |
| Restatements | — | — | no verified usable restatement sequence | schema preserves revision links | no real historical revision sequence | Insufficient |
| Corporate actions | 2026-04-01 | 2026-04-01 | 1 / 1 date | announcement/effective lineage retained | not a complete universe history | Insufficient |
| Dividends | 2021-06-21 | 2025-07-09 | 4 / 2 announcement dates | security-class linkage and dates retained | incomplete total-return history | Insufficient |
| Shares outstanding | 2019-07-09 | 2026-09-14 | 14 / 6 disclosure dates | effective/disclosure dates retained | complete historical class-share sequences unavailable | Insufficient |
| Ownership | 2026-07-10 | 2026-07-10 | 2 / 1 date | disclosure dates retained | most securities absent; no sequence | Insufficient |
| Security rights | 2021-06-21 | 2025-07-09 | 4 / 2 dates | disclosure/source lineage retained | preferred rights remain partial | Insufficient for affected securities |
| Valuations | 2026-09-15 | 2026-09-15 | 41 / 1 date; zero AVAILABLE | model and cutoff lineage retained | no validated valuation and no historical sequence | Insufficient |
| Factors | 2026-09-15 | 2026-09-15 | 980 stored rows / 1 analytical date | snapshot/scoring lineage retained | reruns created multiple IDs for the same as-of date | Insufficient |
| Signals | generated 2026-09-15 | 2026-09-16 | 98 stored / 1 underlying analytical date | immutable model/snapshot lineage retained | current reruns, not historical signals | 0 legitimate historical signals |
| Macro | 1994-05-02 | 2026-09-15 | 130 / 129 periods | vintage-known timestamps retained | long macro history does not cure security-level gaps | Not sufficient to enable test |
| Total-return series | — | — | 0 | separate series type exists | no verified series | Insufficient |
| Benchmark | — | — | 0 verified observations | unavailable is explicit | no credible point-in-time Uzbekistan benchmark series | `BENCHMARK_UNAVAILABLE` |
| Historical execution | 2026-08-17 | 2026-09-15 | daily volume only | observed volumes retained | no verified bid/ask series, depth, intraday sequence, or historical fee schedule | Insufficient |

## Usable test window and signal eligibility

The observed raw-market window is 2026-08-17 through 2026-09-15, only 20 dates. It is not a usable strategy-test window. The sole analytical as-of date is 2026-09-15, and there is no subsequent verified execution/holding window. Consequently:

- legitimate historical signals: **0**;
- orders: **0**;
- fills: **0**;
- trade ledger rows: **0**;
- completed strategies: **0 of 7**.

Equal Weight Universe, Value, Quality, Value + Quality, Top Overall Ranking, Overall Ranking + Liquidity Gates, and Overall Ranking + Confidence Threshold all remain ineligible. Running them would require applying current classifications backward, using today's survivors, or inventing return/execution evidence.

## Blocking classifications

- `INSUFFICIENT_MARKET_HISTORY`
- `INSUFFICIENT_POINT_IN_TIME_FINANCIALS`
- `INSUFFICIENT_HISTORICAL_SIGNALS`
- `HISTORICAL_UNIVERSE_INSUFFICIENT`
- `TOTAL_RETURN_HISTORY_INSUFFICIENT`
- `EXECUTION_HISTORY_INSUFFICIENT`
- `BENCHMARK_UNAVAILABLE`

## Interpretation

No conclusion about strategy profitability, alpha, risk-adjusted return, or robustness is possible. The framework failed safely: it did not count a later price increase for an unfilled order, turn no-trade days into zero returns, forward-fill stale prices, or infer past universe membership from the current universe.
