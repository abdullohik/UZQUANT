# Final Forensic Trace

Audit snapshot: Phase 18 prospective snapshot `318617d7-3038-4ad0-b1ce-9a4451f0167a`

## Ten-security trace

| Ticker | Class | Source/raw | Normalization | Features | Valuation | Liquidity | Factor/confidence | Gate/signal | Size/report |
|---|---|---|---|---|---|---|---|---|---|
| AGMKP | PREFERRED | RSE/Openinfo traced | Present; perimeter/unit limitations | 8 metrics | INSUFFICIENT | LIQUIDITY_TRAP | Present / 21.25 | data-quality, liquidity, rights gates → DATA_INSUFFICIENT | POSITION_SIZE_INSUFFICIENT; stale warnings |
| KASUP | PREFERRED | RSE/Openinfo traced | Present; perimeter/unit limitations | Unavailable | INSUFFICIENT | INVESTABLE on short sample | Present / 38.75 | unknown-rights gate → DATA_INSUFFICIENT | POSITION_SIZE_INSUFFICIENT; stale warnings |
| IPKY | COMMON | RSE/Openinfo traced | Present; bank reports, unknown perimeter | 6 metrics | INSUFFICIENT | INVESTABLE on short sample | Present / 41.75 | insufficient factor coverage → DATA_INSUFFICIENT | POSITION_SIZE_INSUFFICIENT; stale warnings |
| UZTL | COMMON | RSE/Openinfo traced | Present; unknown perimeter | 8 metrics | INSUFFICIENT | INVESTABLE on short sample | Present / 25.25 | no hard gate; tentative evidence → HOLD | POSITION_SIZE_INSUFFICIENT; stale warnings |
| QZSM | COMMON | RSE/Openinfo traced | Present; unknown perimeter/unit gaps | 8 metrics | INSUFFICIENT | LIMITED_LIQUIDITY | Present / 23.25 | insufficient factor coverage → DATA_INSUFFICIENT | POSITION_SIZE_INSUFFICIENT; stale warnings |
| AGMK | COMMON | RSE/Openinfo traced | Issuer financials present | 8 metrics | No latest stored method record | UNASSESSABLE | Present / 23.25 | critical liquidity + stale-price gates → LIQUIDITY_TRAP | No available size; stale warnings |
| KASU | COMMON | RSE/Openinfo traced | Issuer financials present | Unavailable | No latest stored method record | INVESTABLE on short sample | Present / 41.75 | insufficient factor coverage → DATA_INSUFFICIENT | No available size; stale warnings |
| AGBA | UNKNOWN | Identity evidence only | Unavailable | Unavailable | Unavailable | Unavailable | Unavailable | Unavailable | Unavailable, correctly not promoted |
| AGBAP | UNKNOWN | Identity evidence only | Unavailable | Unavailable | Unavailable | Unavailable | Unavailable | Unavailable | Unavailable, correctly not promoted |
| ALKB | UNKNOWN | Identity evidence only | Unavailable | Unavailable | Unavailable | Unavailable | Unavailable | Unavailable | Unavailable, correctly not promoted |

## Priority-security dependency findings

### AGMKP

The preferred security is distinct from AGMK by ISIN and security ID. Its class-specific shares and observed dividend evidence do not establish complete preferred economics. Unknown rights, missing reporting perimeter/unit evidence, unavailable valuation assumptions, short market history, and current stale pipelines correctly prevent valuation, sizing, and order admission.

### KASUP

KASUP remains distinct from KASU. It has normalized issuer statements but no available fundamental metric set for its insurance route and no high-confidence preferred-rights evidence. An `INVESTABLE` liquidity label based on only 20 observations does not override valuation, rights, confidence, model-validation, or stale-state gates.

### IPKY

Bank routing is based on the verified Openinfo bank report path. Some bank metrics exist, but reporting perimeter, units, peer assumptions, cost of equity, and valuation inputs are insufficient. No industrial EV/EBITDA valuation is promoted as a bank primary method. The final signal remains DATA_INSUFFICIENT.

### UZTL

UZTL has the broadest ownership/governance/corporate evidence in the sample and a HOLD signal, but all valuation methods remain insufficient and confidence is low. A verified new issuance has state-registration effective date before later disclosure; this is stored as separate effective and announcement dates, not treated as advance public knowledge. Current stale dependencies block prospective admission.

### QZSM

QZSM has normalized financials and limited-liquidity evidence, but missing perimeter/unit/DCF inputs and relative assumptions prevent valuation. No price or factor substitutes for those missing inputs. The result remains DATA_INSUFFICIENT and stale-blocked.

## Cross-layer evidence

- Production database integrity: `ok`; foreign-key check returned no violations.
- Current pipeline state: 1 FAILED, 1 DEGRADED, 15 STALE.
- Market observations: 140 raw rows, including 20 explicit no-trade placeholders; no logical duplicates; zero bid/ask records.
- Financials: 17 documents, 12 matched; 16 unknown perimeters; 81 unspecified-unit observations.
- Valuation: 41 records, all `VALUATION_INSUFFICIENT`.
- Latest researched signals: 5 DATA_INSUFFICIENT, 1 HOLD, 1 LIQUIDITY_TRAP.
- Portfolio: 27 historical runs, all 100% cash; zero positions.
- Prospective: 3 shadow portfolios, 7 stale-blocked states, zero orders/fills/positions.
- Backtest: 14 insufficient runs, zero orders/fills.
- Full automated suite: 158 passed.

## Adversarial checks

Eight of nine focused in-memory checks passed: TTM unit mismatch, FX mismatch, missing-factor coverage, liquidity override, no-trade no-fill, missing-column failure, future restatement exclusion, and future macro-vintage exclusion. The issuer-name collision check failed because distinct display forms normalized to the same canonical issuer ID. That failure is the audit's critical finding and blocks readiness.
