# Phase 2 Market Data Quality Report

Validation date: 2026-09-14  
Final run: f2fa34a9-1d81-4ed2-b5aa-d575d79f261b  
Parser: rse-daily-history/1.0.0  
Status: SUCCEEDED

## Real source and stored range

Source: Republican Stock Exchange “Toshkent” public security-history pages.

| Security | Real range retrieved | Rows | Trade-reported | No-trade placeholders |
|---|---|---:|---:|---:|
| AGMK | 2026-08-17 to 2026-09-11 | 18 | 0 | 18 |
| AGMKP | 2026-08-17 to 2026-09-11 | 18 | 18 | 0 |
| KASU | 2026-08-17 to 2026-09-11 | 18 | 18 | 0 |
| KASUP | 2026-08-17 to 2026-09-11 | 18 | 18 | 0 |
| IPKY | 2026-08-17 to 2026-09-11 | 18 | 18 | 0 |
| UZTL | 2026-08-17 to 2026-09-11 | 18 | 18 | 0 |
| QZSM | 2026-08-17 to 2026-09-11 | 18 | 18 | 0 |

Total unique stored rows: 126. A real rerun processed the same 126 source rows and left the stored count at 126, confirming idempotency.

## Available fields

security_id, trade_date, source_timestamp, timezone, open, high, low, close, share_volume, currency, source, provenance document, series type and parser version.

## Unavailable fields

exchange timestamp, intraday trade price, trading session, auction type, trade type, last, turnover value, trade count, historical bid/ask, bid/ask size and order-book depth.

No unsupported field was synthesized. Adjusted and total-return series are empty.

## Quality results

- LOW_OBSERVATION_COUNT: 7 securities.
- Severe staleness: 0 securities with a calculable last trade.
- AGMK has no reported trade in the retrieved source window; all 18 rows have zero volume. Its zero-trade ratio is 1.0 over SOURCE_REPORTED_DATES and days-since-last-trade is unknown.
- Other six securities have no zero-volume placeholder in the returned window. A value of 0.0 for their ratio applies only to dates returned by this source, not all official exchange sessions.
- No impossible prices, duplicate stored observations, abnormal 50% moves, possible unit changes or suspected corporate-action discontinuities were detected in this limited window.

## Limitations

The live page returned only a recent 18-row window. Phase 0 showed older dated trade pages exist, but complete pagination and historical extraction have not been established within access constraints. Therefore this is a working real-history pipeline, not a complete long-horizon market database.

Turnover and trade count statistics remain unavailable. Without an official calendar, omitted dates cannot be classified as exchange holidays or zero-trade sessions. Without individual trades, a single-trade move cannot be detected for this source series. Without corporate actions, raw discontinuities are flagged but never repaired.
