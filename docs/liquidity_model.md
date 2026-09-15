# UZQUANT liquidity, capacity and realizable-value model

## Purpose and scope

The model answers whether a position can plausibly be entered or exited. It is independent of fundamental attractiveness: a security can be theoretically attractive and still fail the liquidity gate. It creates no investment recommendation.

Version `liquidity-capacity/1.0.0` consumes raw observed market rows only. No-trade placeholders remain distinct from trades, and raw prices are never forward-filled. Each assessment stores its security, as-of/cutoff date, position and participation assumptions, features, values, state, confidence, flags, uncertainty, source observation IDs and model version.

## Features

The engine calculates average and median daily share volume, trading frequency, zero-trade-day ratio, days since last trade and observed close-return volatility. It supports actual turnover value, trade count, bid/ask spread, bid/ask depth, free float, free-float turnover and ownership concentration when supplied.

For the current RSE source, turnover, trade count, bid/ask, depth and reliable free float are unavailable. Those fields remain null. `close × volume` is not mislabeled as actual trading value because intraday execution prices are unavailable. Trading frequency is based only on source-returned dates, not a complete official session calendar.

## Position capacity

For a position in shares:

`liquidation horizon = position shares / (share ADV × participation rate)`

Participation must be greater than zero and no more than 100%. The operator interface accepts any valid rate; 5%, 10% and 20% scenarios are explicitly tested. If share ADV is zero or missing, the horizon is unavailable rather than infinite false precision.

`Position Value / ADV` is calculated only when the source supplies actual daily trading value. It is currently null. The share-based capacity ratio and liquidation horizon remain valid dimensional calculations.

## Mark-to-market and realizable value

Mark-to-market value is `position shares × latest observed close`. It is a reference value, not an executable quote. If no real trade exists, mark-to-market is unavailable.

Estimated realizable value is an explicit model range:

`MTM × (1 − slippage high)` to `MTM × (1 − slippage low)`.

The provisional band combines position/ADV pressure, observed volatility, half-spread when available, and uncertainty penalties for missing spread/depth. This is a conservative scenario framework—not a precise market-impact estimate. With no order book or spread, confidence is reduced and uncertainty reasons are stored. If no positive ADV exists, realizable value remains null.

## States and hard gates

- `INVESTABLE`: standardized position horizon is within the provisional limited threshold and no hard trap condition exists.
- `LIMITED_LIQUIDITY`: horizon or spread indicates meaningful execution constraints.
- `HIGH_LIQUIDITY_RISK`: position exceeds high-risk capacity or cannot be supported normally.
- `LIQUIDITY_TRAP`: zero-volume dominance, extreme staleness or an extreme liquidation horizon makes an opportunity non-investable under the assumptions.
- `UNASSESSABLE`: a required mark price is absent.

Hard flags include `VERY_LOW_ADV`, `EXTREME_STALENESS`, `ZERO_VOLUME_DOMINANCE`, `TINY_FREE_FLOAT`, `EXTREME_OWNERSHIP_CONCENTRATION`, `VERY_WIDE_SPREAD`, `SINGLE_TRADE_PRICE_MOVE`, `POSITION_EXCEEDS_CAPACITY` and `UNRELIABLE_LAST_PRICE`. Unknown free float or ownership is uncertainty, not a fabricated flag.

## Operator command

`python3 -m uzquant assess-liquidity --position-shares 10000 --participation-rate 0.10`

The command is idempotent for the same security, date, position, participation rate and model version.
