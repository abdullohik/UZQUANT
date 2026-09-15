# Phase 11 Position Examples

Generated as of 2026-09-15 using stored real UZSE market observations, Phase 6 valuation records, Phase 7 liquidity assessments, and Phase 8 confidence records. Portfolio values are hypothetical UZS amounts. These are model outputs for research and portfolio construction, not personalized financial advice.

## Result

All five test securities remain `ENTRY_INSUFFICIENT` because Phase 6 correctly returned `VALUATION_INSUFFICIENT`. Expected upside and downside therefore cannot be calculated from verified valuations. The engine consequently returns `POSITION_SIZE_INSUFFICIENT` and a final maximum of 0% for every portfolio example. It does not turn liquidity capacity alone into a position recommendation.

Free float is unknown for these securities and remains NULL. Governance factor scores are also unavailable, so the risk maximum remains unavailable rather than receiving an assumed average value.

## Real security examples

The liquidity maximum below is an independent capacity constraint based on observed ADV value, 10% participation, a five-day horizon, and the stored liquidity-state adjustment. It is shown even though the final maximum is blocked by insufficient fundamental evidence.

| Security | Stored liquidity state | Observed ADV value (UZS) | Portfolio (UZS) | Liquidity maximum | Entry status | Final maximum | Binding result |
|---|---:|---:|---:|---:|---|---:|---|
| AGMKP | LIQUIDITY_TRAP | 21,756,906.50 | 100,000,000 | 0.0000% | ENTRY_INSUFFICIENT | 0% | DATA_INSUFFICIENT |
| AGMKP | LIQUIDITY_TRAP | 21,756,906.50 | 1,000,000,000 | 0.0000% | ENTRY_INSUFFICIENT | 0% | DATA_INSUFFICIENT |
| AGMKP | LIQUIDITY_TRAP | 21,756,906.50 | 10,000,000,000 | 0.0000% | ENTRY_INSUFFICIENT | 0% | DATA_INSUFFICIENT |
| IPKY | INVESTABLE | 7,881,214.71 | 100,000,000 | 3.9406% | ENTRY_INSUFFICIENT | 0% | DATA_INSUFFICIENT |
| IPKY | INVESTABLE | 7,881,214.71 | 1,000,000,000 | 0.3941% | ENTRY_INSUFFICIENT | 0% | DATA_INSUFFICIENT |
| IPKY | INVESTABLE | 7,881,214.71 | 10,000,000,000 | 0.0394% | ENTRY_INSUFFICIENT | 0% | DATA_INSUFFICIENT |
| KASUP | INVESTABLE | 3,616,922.47 | 100,000,000 | 1.8085% | ENTRY_INSUFFICIENT | 0% | DATA_INSUFFICIENT |
| KASUP | INVESTABLE | 3,616,922.47 | 1,000,000,000 | 0.1808% | ENTRY_INSUFFICIENT | 0% | DATA_INSUFFICIENT |
| KASUP | INVESTABLE | 3,616,922.47 | 10,000,000,000 | 0.0181% | ENTRY_INSUFFICIENT | 0% | DATA_INSUFFICIENT |
| QZSM | LIMITED_LIQUIDITY | 28,805,784.22 | 100,000,000 | 10.8022% | ENTRY_INSUFFICIENT | 0% | DATA_INSUFFICIENT |
| QZSM | LIMITED_LIQUIDITY | 28,805,784.22 | 1,000,000,000 | 1.0802% | ENTRY_INSUFFICIENT | 0% | DATA_INSUFFICIENT |
| QZSM | LIMITED_LIQUIDITY | 28,805,784.22 | 10,000,000,000 | 0.1080% | ENTRY_INSUFFICIENT | 0% | DATA_INSUFFICIENT |
| UZTL | INVESTABLE | 379,184,166.67 | 100,000,000 | 100.0000% cap | ENTRY_INSUFFICIENT | 0% | DATA_INSUFFICIENT |
| UZTL | INVESTABLE | 379,184,166.67 | 1,000,000,000 | 18.9592% | ENTRY_INSUFFICIENT | 0% | DATA_INSUFFICIENT |
| UZTL | INVESTABLE | 379,184,166.67 | 10,000,000,000 | 1.8959% | ENTRY_INSUFFICIENT | 0% | DATA_INSUFFICIENT |

AGMKP demonstrates the liquidity override directly: its stored `LIQUIDITY_TRAP` state forces the liquidity maximum to zero at every portfolio size, independent of any hypothetical conviction.

## Acceptance checks with controlled model inputs

Deterministic tests isolate the requested behavior without presenting synthetic fixtures as real validation data. With the same 50% upside, 20% downside, 80 confidence, and UZS 1,000,000 portfolio:

- the baseline case produces a 2.40% maximum, with risk binding;
- reducing ADV from UZS 100,000 to UZS 1,000 and changing the state to `HIGH_LIQUIDITY_RISK` shrinks the maximum to 0.0175%, with liquidity binding;
- increasing observed volatility from 2% to 20% shrinks the maximum from 2.40% to 0.24%;
- reducing confidence from 80 to 30 shrinks the maximum from 2.40% to 0.90%;
- a verified tiny free float becomes the binding constraint;
- missing liquidity blocks sizing completely;
- existing portfolio concentration reduces the remaining portfolio maximum and can bind.

## Limitations

The observed history is short, liquidity confidence is low, order-book depth and spreads are unavailable, and verified free float is missing. ADV value uses actual observed share volume multiplied by the latest stored trade price; it is a capacity input, not proof that the whole position could execute at that price. No brokerage integration or order generation exists.
