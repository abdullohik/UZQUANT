# Position-Sizing Methodology

The sizing engine calculates five constraints independently and chooses the smallest available constraint. Percentages are decimal portfolio weights.

- **Fundamental maximum:** configurable 5% cap × upside/(upside + downside) × confidence. Missing valuation-derived upside or downside blocks final sizing.
- **Liquidity maximum:** ADV value × participation rate × allowed liquidation days ÷ portfolio value, then reduced for the stored liquidity state. Defaults are 10% participation and five days. `LIQUIDITY_TRAP` yields zero. Missing ADV or an unassessable state blocks final sizing.
- **Risk maximum:** configurable 4% cap × volatility scalar × the minimum of confidence, governance, and data-quality scores. Missing evidence leaves this constraint unavailable and exposed.
- **Portfolio maximum:** the smaller remaining capacity under the security concentration cap and sector limit. Defaults are 4% per security and 25% per sector.
- **Free-float maximum:** verified free-float market value × configurable 1% participation cap ÷ portfolio value. Unknown free float remains NULL and is explicitly flagged; it is never estimated.

The final maximum is the binding minimum. Required fundamental or liquidity inputs being absent returns `POSITION_SIZE_INSUFFICIENT`, a zero final maximum, and `DATA_INSUFFICIENT` as the binding reason. This prevents other constraints from creating an apparently precise position when core evidence is missing.

Volatility is based only on actual observed trade prices. ADV is derived from stored real market activity and the most recent observed trade price; no-trade days are not converted into synthetic returns. Spread/depth precision is not claimed when those fields are absent.

Stored records retain each independent maximum, all inputs and assumptions, source record links, the binding constraint, explanation, date, currency, and `constraint-sizing/1.0.0` model version. Outputs are research and portfolio-construction model results, not personalized financial advice or brokerage instructions.
