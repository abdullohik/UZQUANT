# UZQUANT hard risk gates

Hard gates operate after the tentative attractiveness classification. They cannot be averaged away.

## Deterministic rules and precedence

1. Data Quality below 50 triggers `CRITICAL_DATA_QUALITY` and final `DATA_INSUFFICIENT`.
2. A severe, evidenced governance event triggers `SEVERE_GOVERNANCE_ISSUE` and final `GOVERNANCE_RISK` when data quality is not already critical.
3. Phase 7 `LIQUIDITY_TRAP` or `UNASSESSABLE` triggers `CRITICAL_LIQUIDITY_FAILURE` and final `LIQUIDITY_TRAP` when higher-priority evidence gates do not already apply.
4. Materially unknown preferred-share rights triggers `MATERIALLY_UNKNOWN_SHARE_RIGHTS`, reduces confidence, and caps an otherwise BUY/STRONG_BUY result at `WATCH`. A blocked valuation remains blocked.
5. `UNRELIABLE_LAST_PRICE` or extreme staleness triggers `STALE_PRICE_SUPPRESS_MOMENTUM_AND_EXECUTION_CONFIDENCE` and caps an otherwise BUY/STRONG_BUY result at `WATCH`.
6. Confidence below 50 caps otherwise aggressive BUY/STRONG_BUY classifications at `WATCH`.

The data-quality rule has first precedence because weak evidence cannot support a more specific investment conclusion. All simultaneous gates remain recorded even when one determines the final state.

## Required override demonstrations

Automated tests establish that a synthetic 90/100 attractiveness result becomes `LIQUIDITY_TRAP` after a critical liquidity failure; 95/100 fundamentals become `DATA_INSUFFICIENT` with critical data quality; severe governance becomes `GOVERNANCE_RISK`; unknown rights and stale price each suppress aggressive classifications.

In the real run, AGMKP records both `CRITICAL_LIQUIDITY_FAILURE` and `MATERIALLY_UNKNOWN_SHARE_RIGHTS`, while AGMK records critical liquidity and stale-price suppression. Their final state is `DATA_INSUFFICIENT` because their Data Quality Score is 30. This preserves every failure instead of hiding it behind one label.

These are research classifications, not executable orders.
