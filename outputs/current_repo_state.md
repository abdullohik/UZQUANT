# Current Repository State

Verified: 2026-10-03  
Repository: `abdullohik/UZQUANT`  
Branch: `main`

## Git

- Baseline local HEAD: `cae8a11329d6ce685a483b895c970b47ef66e7dc`
- Baseline remote HEAD: `cae8a11329d6ce685a483b895c970b47ef66e7dc`
- Baseline local/remote match: yes
- Baseline tracked drift: none
- Report-only candidate: local only; not pushed
- `AGENTS.md` and unrelated pre-existing untracked files: excluded

## Current production evidence

| Metric | Result |
| --- | ---: |
| Verified current RSE instruments | 86 |
| Common equities | 51 |
| Preferred equities | 22 |
| Bonds | 13 |
| Other / unknown current instruments | 0 |
| Historical-only securities | 7 |
| UZQUANT securities before reconciliation | 76 |
| Legitimate securities added | 4 |
| Identifier conflicts | 0 |
| Classification conflicts | 0 |
| Current equities processed | 73 |
| Equities with market data | 50 |
| Equities with financial reports | 16 |
| Equities with normalized fundamentals | 14 |
| Equities with verified share evidence | 40 |
| Equities with verified rights evidence | 4 |
| Equities with ownership evidence | 2 |
| Equities with liquidity assessment | 7 |
| Equities with executable valuations | 1 |
| Available valuation methods | 1 |
| Equities with 4+ factors | 5 |
| Equities with non-insufficient research states | 4 |
| `DATA_INSUFFICIENT` | 69 |
| `VALUATION_INSUFFICIENT` | 72 |
| `LIQUIDITY_TRAP` | 2 |
| `HOLD` | 1 |
| `REDUCE` | 1 |
| Raw market observations | 837 |
| Unique market dates | 74 |
| Earliest market date | 2024-09-27 |
| Latest market date | 2026-09-28 |
| RSE backfill pending | 1,784 |
| RSE backfill source-blocked | 1 |
| Pipeline health | 17 HEALTHY / 0 DEGRADED / 0 STALE / 0 FAILED |
| Foreign-key violations | 0 |

## Verification

- Development full suite: 234 passed.
- Clean-checkout full suite: 234 passed using the same read-only production evidence database; source code came exclusively from the exact archived SHA.
- Focused clean-checkout adversarial suite: 48 passed.
- Python compilation: passed.
- JavaScript syntax validation: passed.
- Clean-checkout server startup: passed.
- Clean-checkout `/api/v1/health`: HTTP 200.
- Clean-checkout `/api/v1/coverage`: HTTP 200; 73 current equities.
- Terminal equity count: 73.
- Terminal executable valuations visible: 1, IPKY.
- Terminal research states visible: 73.
- UI/backend mismatches: 0 found.
- Automatic refresh status: fully automated for the existing 17-pipeline production chain; external source availability remains an operational dependency and failures fail closed.

