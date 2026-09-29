# Terminal Market-Wide Verification

Date: 2026-09-29

## Backend reconciliation

- Current-equity API rows: **73**
- Common / preferred: **51 / 22**
- Distinct current issuers: **52**
- Historical-only excluded: **7** (`BECMP`, `DRBK`, `FRAZP`, `IPKYP`, `JASM`, `ORFIP`, `UZML`)
- Bonds in API: **0**
- Executable valuation: **IPKY only**
- Research states: 69 `DATA_INSUFFICIENT`, 2 `LIQUIDITY_TRAP`, 1 `HOLD`, 1 `REDUCE`
- Coverage states: 49 partially researchable, 23 data insufficient, 1 research ready
- Foreign-key violations: **0**

## Interface verification

Local browser smoke validation confirmed all eight navigation sections load. The screener reported **73 of 73 current equities** and displayed every required market, valuation, ten-factor, confidence, state and blocker column. Missing fields rendered `n/a`. The terminal showed production health as **17/17 HEALTHY** after the authorized refresh.

## Refresh verification

The successful end-to-end production cycle completed every pipeline as `HEALTHY`. A preceding restricted-network failure was retained in run history; it was not normalized or cleared manually. Recovery occurred only through the later successful source refresh.

## Tests

- Focused API/UI suite: **13 passed**
- Full development suite: **230 passed**
- JavaScript syntax check: passed
- Python compilation check: passed
