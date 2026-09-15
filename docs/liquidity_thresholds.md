# Provisional liquidity thresholds

Threshold version: `uzse-provisional/1.0.0`  
Status: **PROVISIONAL**  
Validation date: 2026-09-15

These are initial safety gates, not optimized trading parameters. They were not imported from US or other developed markets.

## Empirical basis

The verified RSE history currently covers seven securities and only 18 source-returned dates from 2026-08-17 through 2026-09-11. This is the actual data-covered Uzbek sample, not a claim of full exchange coverage.

- Positive share ADV: minimum 906.5; median 32,132.11; maximum 360,273,632.78.
- Zero-share-ADV securities: 1 of 7.
- AGMKP at 906.5 shares/day is separated by more than 21× from the next positive ADV, QZSM at 19,609.11.
- Six securities show trading frequency 1.0 and AGMK 0.0 only over source-returned dates. A complete official trading calendar is not available.
- Trading-value ADV, trade count, spread, depth, free float and exact ownership concentration are unavailable for all seven.

Share counts do not measure capital capacity across securities with very different prices. Consequently, the initial absolute ADV threshold is only a warning; classification relies principally on position-relative liquidation horizon.

## Thresholds

| Rule | Provisional threshold | Rationale |
|---|---:|---|
| `VERY_LOW_ADV` | ≤1,000 shares/day | Brackets the isolated smallest positive observation; must be recalibrated with broader history |
| Stale warning | ≥5 calendar days | Existing Phase 2 convention |
| `EXTREME_STALENESS` | ≥20 calendar days or no observed trade | Existing Phase 2 severe-staleness convention |
| `ZERO_VOLUME_DOMINANCE` | ≥80% source-returned dates | Conservative hard gate for persistent no-trade observations |
| Limited horizon | >5 trading days | Position-specific provisional execution gate |
| High-risk horizon / capacity flag | >20 trading days | Position-specific provisional execution gate |
| Trap horizon | >100 trading days | Impractical standardized exit horizon |
| `VERY_WIDE_SPREAD` | ≥10% of midpoint | Provisional until real quote histories exist |
| `TINY_FREE_FLOAT` | ≤5% | Inactive until verified free float exists |
| `EXTREME_OWNERSHIP_CONCENTRATION` | ≥90% | Inactive until exact ownership exists |

All thresholds and the empirical distribution are persisted. A material recalibration requires a new threshold/model version and must not rewrite old assessments.
