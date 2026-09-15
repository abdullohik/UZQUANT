# Phase 8 real signal explanations

Run date: 2026-09-15  
Supportable universe: seven securities with real Phase 2 histories  
Data snapshot: `d9969797b6cb8eb98ef47b065a428f64cc41fdcd7e2b3a06a14302019a16d1b0`

## Outcome

All seven securities are classified `DATA_INSUFFICIENT`. Investment Attractiveness is null, not zero: only one or two of the required components are available, below the four-factor minimum. These outputs are research classifications, not executable orders.

| Ticker | Available scores | Confidence | Risk-gate explanation |
|---|---|---:|---|
| AGMK | Data Quality 30 | 13.75 | Critical data quality; no assessable traded mark/capacity; stale-price and execution suppression |
| AGMKP | Data Quality 30; Liquidity 0 | 14.75 | Critical data quality; Phase 7 liquidity trap; materially unknown preferred rights |
| KASU | Data Quality 30; Liquidity 60 | 14.75 | Critical data quality |
| KASUP | Data Quality 30; Liquidity 60 | 14.75 | Critical data quality; materially unknown preferred rights |
| IPKY | Data Quality 30; Liquidity 60 | 14.75 | Critical data quality |
| UZTL | Data Quality 30; Liquidity 60 | 14.75 | Critical data quality |
| QZSM | Data Quality 30; Liquidity 50 | 14.75 | Critical data quality |

## Why the other factors are unavailable

- Valuation: all Phase 6 cases are `VALUATION_INSUFFICIENT`; KASU and AGMK have no valid security valuation either.
- Growth: each issuer has only one approved report, so no compatible prior period exists.
- Momentum: only 18 raw observed rows exist, below the documented 60-observation minimum; AGMK also has no trades.
- Dividend: historical dividends cannot be mixed with current prices without a date-compatible methodology.
- Quality and Balance-Sheet Risk: specialist sector inputs and sufficient comparable history are incomplete; the engine does not force general-company ratios onto banks or insurers.
- Governance: observed events are evidence, but absence of a severe event is not evidence of good governance and is not scored as 100.
- Catalyst: explicit unavailable placeholder.

## Override verification

The production gate logic and tests demonstrate:

- a 90/100 tentative `STRONG_BUY` plus failed liquidity becomes `LIQUIDITY_TRAP`;
- 95/100 fundamentals plus critical data quality becomes `DATA_INSUFFICIENT`;
- unknown share rights or stale price suppress aggressive classifications;
- severe governance becomes `GOVERNANCE_RISK`;
- missing factors and peer groups smaller than five remain unavailable.

Prior signals are append-only. Every generated row retains its signal ID, model/scoring/valuation/liquidity versions, data snapshot and generation timestamp. Re-running the model creates new records and does not rewrite the earlier signal.
