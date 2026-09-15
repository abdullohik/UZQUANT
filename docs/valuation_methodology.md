# UZQUANT valuation methodology

## Governing principle

Valuation is a point-in-time, security-specific analytical record, not an investment recommendation. `ACCURACY_RULES.md` governs this engine. A numerical result is emitted only when every required input is verified, compatible, dated no later than the data cutoff, and linked to stored observations. Otherwise the status is `VALUATION_INSUFFICIENT` and values remain null.

Each record stores the security, valuation and cutoff dates, financial-period inputs, method, sector engine, currency, explicit assumptions, bear/base/bull values, confidence, model version, source documents and observations. Assumptions are data, not hidden constants. Country risk must appear as a distinct input.

## Sector routing

- General industrial companies: DCF and relevant relative measures.
- Banks: P/B, P/TBV, P/E, residual income and, when justified, dividend discount. Industrial EV/EBITDA is never the primary route.
- Insurers: P/B, P/E, ROE-adjusted P/B, residual income and dividend models.
- Mining/commodity companies: production × commodity-price × FX scenarios, costs and CapEx, plus relevant relative measures.

Unavailable sector inputs return null; they are not replaced with generic-company assumptions.

## Industrial DCF

For each forecast year:

`Revenue(t) = Revenue(t-1) × (1 + growth)`

`EBIT = Revenue × EBIT margin`

`FCF = EBIT × (1 − tax rate) + D&A − CapEx − change in working capital`

`Terminal value = FCF(n) × (1 + g) / (WACC − g)`

Enterprise value is discounted forecast FCF plus discounted terminal value. Equity value is enterprise value less net debt. Fair value per share is equity value divided by verified total shares outstanding. WACC must exceed terminal growth; shares must be positive.

Bear, base and bull scenarios are independently calculated. Sensitivity grids vary WACC, terminal growth, revenue growth and EBIT margin. Suspicious or invalid combinations remain unavailable.

## Financial-sector models

Residual income begins with book equity, discounts annual excess return (`book value × (ROE − cost of equity)`), and adds a continuing residual-income value. Dividend discount uses next-period dividend divided by cost of equity less growth. P/TBV requires verified tangible book value. Preferred-share valuation additionally requires authoritative class rights; a ticker suffix is not evidence of economics.

## Relative valuation and peers

The engine calculates P/E, P/B, EV/EBITDA, EV/EBIT, EV/Sales, FCF yield and dividend yield only with compatible point-in-time inputs. P/E and earnings-based implied values are unavailable for non-positive earnings. A peer set must persist its as-of date, member security IDs, sources, and written selection logic covering sector, business model, geography, size, accounting period and liquidity decisions. No undocumented peer median is accepted.

## Mining scenarios

Operating scenario value before further discounting is `production × commodity price × sourced FX − production × unit cost − CapEx`. Production, commodity-price basis, costs, FX date/source and CapEx must be compatible and explicit.

## Currency and inflation controls

Cash flows and discount rates must use the same nominal/real basis. Their currencies must match unless a positive FX rate with date and source is stored. The engine rejects real cash flows with nominal rates and cross-currency discounting without a sourced conversion. Inflation and country-risk assumptions may not be buried inside an unexplained discount rate.

## Current real-data gate

The Phase 3–5 approved store has one report per validation issuer, source units and currency are unverified, reporting perimeter is unknown, and verified total shares outstanding are missing. Industrial issuers also lack normalized operating cash flow, CapEx and D&A. Those facts prevent compliant numerical valuations. The real Phase 6 run therefore stores explicit insufficiency records, preserving the source-document lineage and the exact missing requirements.
