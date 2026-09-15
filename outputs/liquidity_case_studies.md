# Phase 7 real liquidity case studies

Validation date: 2026-09-15  
Source: Republican Stock Exchange “Toshkent” raw observed history  
Source window: 2026-08-17 to 2026-09-11 (18 source-returned dates)  
Model: `liquidity-capacity/1.0.0`; thresholds: `uzse-provisional/1.0.0` (**PROVISIONAL**)

All cases use a hypothetical standardized 10,000-share position at 10% of observed share ADV. This is a capacity scenario, not an investment recommendation. Mark prices are last observed closes, not executable quotes. All confidence is LOW because the window is short and turnover, trade count, spread, order-book depth, free float and exact ownership concentration are unavailable.

## Required cases

| Security | Share ADV | Mark-to-market | Realizable-value range | Slippage range | Horizon | State |
|---|---:|---:|---:|---:|---:|---|
| AGMKP | 906.50 | 240,010,000 UZS | 170,627,716–226,771,721 UZS | 5.52%–28.91% | 110.31 days | `LIQUIDITY_TRAP` |
| KASUP | 20,094,013.72 | 1,800 UZS | 1,480–1,800 UZS | 0.00%–17.76% | 0.005 days | `INVESTABLE` (LOW confidence) |
| KASU, relatively liquid by share capacity | 360,273,632.78 | 100 UZS | 90–100 UZS | 0.00%–10.00% | 0.0003 days | `INVESTABLE` (LOW confidence) |
| AGMK, severely illiquid | 0 | unavailable | unavailable | unavailable | unavailable | `UNASSESSABLE` |

KASU and KASUP have extremely low nominal observed prices, so share ADV must not be confused with large monetary capacity. Actual turnover is unavailable.

## Participation sensitivity: AGMKP

For the same 10,000-share position:

| Participation rate | Liquidation horizon |
|---:|---:|
| 5% | 220.63 trading days |
| 10% | 110.31 trading days |
| 20% | 55.16 trading days |

Even an aggressive 20% participation assumption produces a horizon above the provisional 20-day capacity limit. With no order-book depth, the model does not claim a precise impact price.

## Acceptance-gate demonstration

AGMKP demonstrates the hard override. If a separate fundamental/valuation process hypothetically labelled it attractive, the real observed share ADV and the standardized position produce `POSITION_EXCEEDS_CAPACITY` and `LIQUIDITY_TRAP`. The liquidity engine therefore automatically blocks investability independently of theoretical upside. This is a hypothetical attractiveness premise—not a claim that AGMKP is undervalued; Phase 6 returned `VALUATION_INSUFFICIENT`.

AGMK is even less assessable: all 18 rows are explicit no-trade placeholders, no last traded price exists in the window, and the model refuses both mark-to-market and realizable values. It raises `ZERO_VOLUME_DOMINANCE`, `EXTREME_STALENESS` and `UNRELIABLE_LAST_PRICE` rather than forward-filling the displayed close.

## Limitations

The rankings cover only the seven securities with verified Phase 2 histories, not all 74 security-master records. A complete exchange calendar and long historical series are unavailable. Slippage ranges are provisional model estimates with explicit missing-depth penalties; they are not measured execution costs. Free-float turnover and ownership flags remain unavailable because exact verified inputs do not exist.
