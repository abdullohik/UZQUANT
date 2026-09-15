# Phase 12 Execution Case Studies

Generated as of 2026-09-15 for a hypothetical 10,000-share entry. This is execution research, not an order, fill promise, brokerage instruction, or personalized financial advice.

## Evidence boundary

The real stored sample contains 126 daily observations across seven securities and 18 dates. It contains no bid, ask, order-book depth, exchange timestamps, individual trades, trade counts, verified lot sizes, current price-limit state, or verified auction/session mechanics. Consequently:

- all seven cases return `INTRADAY_TIMING_NOT_RELIABLE`;
- maximum suggested child order is unavailable;
- acceptable entry range is unavailable because both a valid Phase 11 valuation range and bid/ask evidence are absent;
- execution confidence is LOW;
- slippage values, where available, are broad Phase 7 uncertainty bands rather than order-book impact estimates.

## Real outputs

| Security | Result | Preferred style | Maximum participation | Estimated horizon | Expected slippage range | Confidence |
|---|---|---|---:|---:|---:|---|
| AGMK | CANNOT_ESTIMATE_EXECUTION_RELIABLY | NO_EXECUTION_ESTIMATE | 0% | Unavailable | Unavailable | LOW |
| AGMKP | CANNOT_ESTIMATE_EXECUTION_RELIABLY | NO_EXECUTION_ESTIMATE | 0% | Unavailable | Unavailable | LOW |
| IPKY | ESTIMATE_AVAILABLE | Daily participation schedule; limit order only if supported | 10% | 3 trading days | 0.12%–14.71% | LOW |
| KASU | ESTIMATE_AVAILABLE | Daily participation schedule; limit order only if supported | 10% | 1 trading day | 0.00%–10.00% | LOW |
| KASUP | ESTIMATE_AVAILABLE | Daily participation schedule; limit order only if supported | 10% | 1 trading day | 0.00%–17.76% | LOW |
| QZSM | ESTIMATE_AVAILABLE | Daily participation schedule; limit order only if supported | 5% | 11 trading days | 0.25%–15.30% | LOW |
| UZTL | ESTIMATE_AVAILABLE | Daily participation schedule; limit order only if supported | 10% | 5 trading days | 0.23%–19.27% | LOW |

“Estimate available” means only that observed daily volume supports a provisional multi-day participation calculation. It does not mean the quoted historical close is currently executable or that the daily capacity will actually be available.

AGMK has no reported trades in the stored window and no usable mark price. AGMKP has traded observations but its Phase 7 `LIQUIDITY_TRAP` state blocks execution estimation. These cases demonstrate the required fail-safe result instead of manufactured timing or impact precision.

QZSM illustrates partial-fill logic: its `LIMITED_LIQUIDITY` state reduces maximum participation to 5%, producing an estimated 11-session horizon for 10,000 shares. The schedule is a capacity model, not a fill guarantee.

## Tested edge cases

Automated tests cover missing order books, a very wide spread, multi-day partial fills, a zero-trade security, an illiquid preferred share, a liquid security, and an explicitly supplied price-limit condition. The price-limit test returns a wait/verify style and does not assume execution. Intraday guidance is released only when at least 60 intraday trade days exist, the pattern passes an explicit robustness indicator, and trading frequency is at least 80%.

## Limitations

Current venue mechanics have not been verified to a production standard, so the engine does not claim that a particular order type, lot size, price band, session, or auction mechanism is available. A user or broker must verify current venue rules before interpreting the conditional limit-order style. Better execution estimates require timestamped trades, bid/ask history, depth snapshots, and actual fill evidence.
