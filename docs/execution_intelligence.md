# Execution Intelligence

Phase 12 estimates whether and over how many trading days a hypothetical entry or exit might be attempted. It never submits orders, guarantees fills, or treats the latest price as executable.

## Supported evidence

The current verified UZSE sample supports daily trade dates, OHLC, and reported share volume for seven securities over 18 dates. It has no bid, ask, spread, depth, exchange timestamp, individual-trade sequence, trade count, verified minimum lot, price-limit state, auction type, or session mechanics. These fields remain unavailable.

The engine therefore calculates only a conservative daily participation schedule. Default provisional participation limits are 10% for `INVESTABLE`, 5% for `LIMITED_LIQUIDITY`, 2% for `HIGH_LIQUIDITY_RISK`, and zero for `LIQUIDITY_TRAP` or `UNASSESSABLE`. Estimated horizon is proposed shares divided into daily ADV capacity. Partial fills are modeled as a schedule, never as guaranteed fills.

## Output policy

`maximum_suggested_child_order` requires verified depth and is NULL without it. `acceptable_entry_range` requires both a supported Phase 11 valuation entry range and a current bid/ask; otherwise it is NULL. Slippage is the Phase 7 provisional uncertainty band and remains low-confidence when depth/spread are missing.

When daily activity supports a rough schedule but microstructure is absent, the preferred style is `DAILY_PARTICIPATION_SCHEDULE_LIMIT_ORDER_IF_SUPPORTED`. This is conditional on current broker/venue support; it is not a claim about verified exchange order types. Wide-spread fixtures select patient limit behavior with an explicit no-fill assumption. A verified active price-limit state pauses ordinary estimation.

Critical liquidity failure, zero/unknown trading frequency, or missing mark price returns `CANNOT_ESTIMATE_EXECUTION_RELIABLY`. The engine suppresses slippage precision in that state.

## Intraday timing gate

Intraday guidance requires at least 60 intraday trade days, a robust pattern indicator, and trading frequency of at least 80%. All current real cases return `INTRADAY_TIMING_NOT_RELIABLE`; no time-of-day guidance is generated.

Records preserve proposed side/size, each output, uncertainty, source observation IDs, linked liquidity and entry records, assumptions, as-of date, and `execution-intelligence/1.0.0` version. Run with `python3 -m uzquant assess-execution`.
