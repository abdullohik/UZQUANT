# Launch Valuation & Backfill Closure

Audit date: 2026-09-27. Governing accuracy rules and the existing readiness rubric were unchanged.

## Result

UZQUANT completed a healthy 17/17 production cycle, substantially enlarged its exact public RSE evidence, added two verified Openinfo reporting periods, and created its first production `FULL_FREEZE_V1` prospective snapshot. No valuation was forced: all five targets still lack at least one mandatory, source-defensible input or security-specific legal/economic fact.

The formal status remains **EXPERIMENTAL / BUILD_COMPLETE_BUT_EVIDENCE_LIMITED**. The system is operational for evidence collection and constrained research, but not yet `RESEARCH_READY` for dependable valuation conclusions.

## Before / after

| Measure | Before | After |
|---|---:|---:|
| Pipeline health | 17 HEALTHY | 17 HEALTHY |
| Market observations | 355 | 551 |
| Unique market dates | 73 | 73 |
| Historical span | 2024-09-27–2026-09-25 | 2024-09-27–2026-09-25 |
| RSE archived HTML pages | 125 | 268 |
| Exact RSE trade rows | 5,873 | 9,870 |
| Pending RSE windows | 1,885 | 1,804 |
| Verified-empty windows | 3 | 34 |
| Source-blocked windows | 1 | 1 |
| Financial documents | 29 | 31 |
| Current normalized observations | 603 | 654 |
| Available fundamentals | 60 | 64 |
| Available valuations | 0 | 0 |
| `FULL_FREEZE_V1` snapshots | 0 | 1 |
| Eligible prospective states | 0 | 0 |

## Work performed

- Processed 81 of the original 1,885 pending RSE monthly windows: 50 imported and 31 verified empty.
- Archived every retrieved page and retained exact trade-to-daily-observation lineage.
- Stopped at a safe resumable checkpoint when RSE returned HTTP 429; no job remains `IN_PROGRESS`.
- Added the official KASUP 2021 annual report (`insurance/annual/73`) and QZSM 2024 annual report (`jsc/annual/5408`). Their source does not explicitly resolve reporting perimeter or unit scale, so those fields remain unknown.
- Added `AUTHORITATIVE_SOURCE` to the enforced valuation-assumption provenance vocabulary; a citation remains mandatory.
- Ran fundamentals, every sector-routed valuation method, liquidity, factors, confidence, gates, and signals without changing methodology.
- Ran one real complete scheduler cycle: 17/17 pipelines were healthy.
- Generated one new `FULL_FREEZE_V1` snapshot with 51 current security states, three cash shadow portfolios, zero orders and zero fills.
- Prevented legacy valuation observation IDs from being mislabeled as exact immutable version IDs during snapshot lineage linking.

## Market-history quality

The database now holds observations for 51 securities. Five have at least 30 dates, three at least 60, and none at least 120, 250, or 500 dates. The 73-date cross-universe calendar supports better short-sample ADV, trading-frequency, volatility and staleness descriptions, but not long-window momentum, robust event studies, or historical strategy validation.

| Target | First | Last | Trade dates | Trade rows | Turnover (UZS) | Interpretation |
|---|---|---|---:|---:|---:|---|
| AGMKP | 2024-09-27 | 2026-09-25 | 73 | 942 | 136,857,265.29 | ADV usable with low confidence; capacity remains highly constrained. |
| IPKY | 2024-09-27 | 2026-09-25 | 73 | 2,277 | 136,014,317.27 | Best target trading sample, still only 73 observed dates. |
| KASUP | 2026-08-17 | 2026-09-25 | 28 | 0 in aggregate source field | 0 | Insufficient trade-history evidence; displayed observations do not justify inferred trades. |
| QZSM | 2024-09-27 | 2026-09-25 | 73 | 1,312 | 202,300,872.69 | Short-sample liquidity interpretation only. |
| UZTL | 2024-09-27 | 2026-09-25 | 52 | 842 | 107,520,110.31 | Short-sample liquidity interpretation only. |

Zero-trade sessions are not reported because the backfill queue is incomplete and an authoritative complete trading calendar by security was not established.

## Valuation closure

All five targets have verified identities, class-specific share counts and observed market prices. They do not have a complete defensible valuation evidence set. Method-specific attempts are stored; missing DCF inputs do not block independent P/B or P/E assessment.

- **IPKY:** P/B is partially supported by consolidated IFRS evidence and verified shares, but the current point-in-time input assembly still includes later unknown-perimeter reports and no verified Bear/Base/Bull peer multiple. P/TBV lacks a verified tangible-book input; P/E lacks a current normalized net-income input; residual-income/DDM lack sourced cost-of-equity/growth assumptions.
- **KASUP:** preferred rights are unverified; report units and perimeter remain unresolved; no verified insurer peer multiples or sourced cost-of-equity assumptions exist.
- **AGMKP:** preferred rights and perimeter remain unverified; DCF/mining inputs and discount assumptions are incomplete; no verified multiples exist.
- **UZTL:** perimeter remains unknown; DCF cash-flow inputs and discount assumptions are incomplete; no verified multiples exist.
- **QZSM:** perimeter remains unknown; DCF cash-flow inputs and discount assumptions are incomplete; no verified multiples exist.

No valuation method executed to `AVAILABLE`, so manual numeric reconciliation was correctly not applicable. Producing Bear/Base/Bull numbers would have required invented peer multiples, discount rates, growth, or preferred-security allocation.

## Readiness

The healthy real cycle and first full freeze now pass two previously missing operational requirements. Research readiness still fails because there is no reproducible valuation subset, market history remains too short for reliability characterization, preferred rights/ownership/free-float remain incomplete, and no prospective outcome series exists. These are evidence limitations, not a reason to weaken gates.

## External blockers

| Blocker | Classification |
|---|---|
| Remaining 1,804 public RSE windows | `PUBLIC_DATA_STILL_NOT_EXHAUSTED`; resumable, presently rate-limited |
| Preferred rights for AGMKP/KASUP | `REQUIRES_ISSUER_DOCUMENT` or `REQUIRES_CSD/DEPOSITORY_SOURCE` |
| Authoritative peer multiples and valuation anchors | `REQUIRES_ISSUER_DOCUMENT` / approved market research source; not safely derivable from current public set |
| Bid/ask, depth, queues, historical spread | `REQUIRES_BROKER_DATA` or `REQUIRES_AUTHORIZED_RSE_DATA` |
| Full ownership/free float | `REQUIRES_CSD/DEPOSITORY_SOURCE` |
| Prospective calibration and outcomes | `REQUIRES_TIME` |

## Mandatory answers

1. **81** of the 1,885 pending windows were processed.
2. **1,804** remain pending; one historical job remains `SOURCE_BLOCKED`; none is `IN_PROGRESS`.
3. Final verified public span: **2024-09-27 through 2026-09-25**.
4. **Five** securities have 30+ observed dates; 51 have at least one observation.
5. IPKY valuation-ready: **No**.
6. KASUP valuation-ready: **No**.
7. UZTL valuation-ready: **No**.
8. QZSM valuation-ready: **No**.
9. AGMKP valuation-ready: **No**.
10. Successfully executed valuation methods: **none**; every unsupported method failed closed with stored reasons.
11. Exact evidence blockers are listed under “Valuation closure” and in `outputs/target_valuation_readiness.md`.
12. New `FULL_FREEZE_V1` snapshots: **1**.
13. Healthy end-to-end current research cycle: **Yes, 17/17 HEALTHY**.
14. `RESEARCH_READY`: **No; remains EXPERIMENTAL**.
15. Smallest remaining blockers: a defensible valuation subset, completed target market backfill, verified preferred rights/perimeter/units where material, and prospective evidence over time.
16. Public-data-alone blockers: order-book/execution history, complete beneficial ownership/free float, and possibly preferred-security legal terms require authorized RSE, broker, CSD/depository, or issuer documents.
