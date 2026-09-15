# Phase 9-integrated signal explanations

Run date: 2026-09-15  
Supportable universe: seven securities with real Phase 2 histories  
Data snapshot: `d5635f1005822f49e4f6af41c58fccf0b50c96bc3fa1c939e28a57380247a79a`
Model/scoring versions: `research-ranking/1.1.0` / `factor-scoring/1.1.0`

## Outcome

All seven securities remain `DATA_INSUFFICIENT`. Investment Attractiveness is null, not zero: only two or three components are available, below the four-factor minimum. Catalyst evidence did not bypass critical data, liquidity or rights gates. These are research classifications, not orders.

| Ticker | Available scores | Confidence | Risk-gate explanation |
|---|---|---:|---|
| AGMK | Data Quality 30; Catalyst 40 | 14.75 | Critical data quality; unassessable liquidity; stale execution evidence |
| AGMKP | Data Quality 30; Liquidity 0; Catalyst 40 | 15.75 | Critical data quality; liquidity trap; unknown preferred rights |
| KASU | Data Quality 30; Liquidity 60 | 14.75 | Critical data quality |
| KASUP | Data Quality 30; Liquidity 60 | 14.75 | Critical data quality; unknown preferred rights |
| IPKY | Data Quality 30; Liquidity 60 | 14.75 | Critical data quality |
| UZTL | Data Quality 30; Liquidity 60; Catalyst 40 | 15.75 | Critical data quality |
| QZSM | Data Quality 30; Liquidity 50 | 14.75 | Critical data quality; its neutral OTHER event has no catalyst score |

AGMK/AGMKP and UZTL receive a LOW-confidence Catalyst score of 40 only because their dividend occurrences have `POSSIBLE` relevance. There is no evidence of a dividend increase or resulting valuation-gap closure. The verified UZTL capital increase and management change remain directionally neutral and unscored as catalysts.

Valuation, Growth, Momentum, Dividend, Quality, Governance and Balance-Sheet Risk remain unavailable for the reasons documented in Phase 8. Prior 1.0 signals remain stored; the 1.1 run created new signal IDs and uses a new data snapshot.
