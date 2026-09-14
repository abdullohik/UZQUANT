# UZQUANT Market Data Methodology

## Source and scope

Phase 2 uses the public RSE security-history route:

https://uzse.uz/isu_infos/STK?isu_cd={ISIN}

The embedded chart explicitly publishes trade date, open, high, low, close and share volume. Those six source fields are ingested as RAW_OBSERVED. The parser does not construct OHLC from a displayed last price.

Unsupported fields remain null: exchange timestamp, trading session, auction type, trade type, last, individual trade price, turnover, trade count, bid/ask and sizes. Currency is UZS and source timestamp is the UTC retrieval time. Date-only exchange observations are associated with Asia/Tashkent; no artificial intraday time is created.

## Raw, adjusted and total-return series

The database supports three separate series types:

- RAW_OBSERVED
- CORPORATE_ACTION_ADJUSTED
- TOTAL_RETURN

Only RAW_OBSERVED is populated in Phase 2. Adjusted and total-return data remain empty until verified corporate actions and dividends are available. Raw observations are never overwritten.

## No-trade handling

A source row with zero share volume is retained as NO_TRADE_PLACEHOLDER. It is not treated as a trade and is excluded from observed-return calculations. A missing date is not inserted, forward-filled or assigned a zero return.

Trading frequency and zero-trade ratio are calculated only when an explicit trading calendar is supplied or when the source itself supplies dated placeholders. SOURCE_REPORTED_DATES does not prove coverage of every exchange session.

## Calculations

- Trading frequency: trade-reported dates divided by supported denominator dates.
- Zero-trade-day ratio: explicit no-trade dates divided by supported denominator dates.
- Average/median share volume: source-published daily values.
- Average/median trading value and trade count: null when the source does not publish them.
- Days since last trade: calendar days from the latest TRADE_REPORTED row to the as-of date.
- Returns: close-to-close only between successive TRADE_REPORTED observations. No missing date creates a return.

## Quality flags

- STALE_PRICE: at least 5 calendar days since last reported trade.
- VERY_STALE_PRICE: at least 20 calendar days.
- LOW_OBSERVATION_COUNT: fewer than 20 rows.
- ABNORMAL_PRICE_MOVE: absolute close-to-close move at least 50%.
- SINGLE_TRADE_MOVE: abnormal move with explicitly reported trade count equal to one.
- POSSIBLE_UNIT_CHANGE: close changes by at least 10 times.
- POSSIBLE_CORPORATE_ACTION: large discontinuity requiring investigation.
- MISSING_VOLUME: source row has no volume.
- DUPLICATE_RECORD: duplicate row in a source response.
- IMPOSSIBLE_PRICE: non-positive OHLC or low above high.

Flags never repair data automatically.

## Pipeline behavior

Every run records source, timing, status, counts, errors and parser version. Raw documents are archived with URL, retrieval time and SHA-256. Observation identity includes security, date and payload hash: identical reruns update last-seen metadata without duplicating observations; changed source values create a separate version. Per-security failures yield PARTIAL rather than erasing successful work.

Operator command:

    python3 -m uzquant update-market-data
