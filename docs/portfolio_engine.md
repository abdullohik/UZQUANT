# Portfolio Construction and Risk

## Construction method

UZQUANT portfolio version `transparent-portfolio/1.0.0` uses deterministic constrained allocation. It does not estimate unstable expected-return covariance inputs or perform unconstrained mean-variance optimization. Candidates are ordered by an explainable payoff/confidence/volatility measure, then admitted only if validation, signal, valuation, confidence, liquidity horizon, thesis lineage, governance, and data-quality gates pass.

The engine supports `CONSERVATIVE`, `BALANCED`, and `HIGH_CONVICTION` configurations. The names describe constraint sets, not personalized suitability recommendations.

## Constraint stack

Each candidate receives an independent maximum from:

- single-name weight;
- sector remaining capacity;
- liquidity capacity value divided by AUM;
- maximum liquidation horizon;
- verified free-float capacity, when available;
- government-linked, commodity, and FX exposure caps;
- factor concentration caps;
- highly correlated group capacity;
- remaining portfolio capital;
- minimum confidence and model-validation gates.

Unknown free float remains unavailable and is never estimated. Unknown government, commodity, or FX exposure remains distinguishable from zero in source candidates; a production admission policy may block material unknowns. The smallest numeric constraint is stored as the binding constraint. Positions rejected by nonnumeric gates retain their reasons.

Default caps are explicit. Conservative/Balanced/High Conviction single-name caps are 3%/5%/8%, sector caps 15%/25%/35%, maximum exit horizons 5/10/15 days, and confidence minimums 70/60/55. Exposure and correlation caps vary by type and are stored with every portfolio run.

## Capacity and AUM

Liquidity maximum equals verified position capacity value divided by portfolio AUM. Therefore the same security consumes a smaller permissible weight as AUM rises. The engine leaves unused capital as cash; it does not redistribute beyond binding market capacity merely to reach 100% investment.

## Correlation and risk

Pairwise correlations are used only when supported. Securities above the configurable 0.80 absolute-correlation threshold share a correlated-group cap. A missing pairwise correlation is treated conservatively as fully correlated for allocation capacity, but it makes covariance-based portfolio volatility and risk contributions unavailable; the engine never assumes that unknown correlation is zero. Risk contributions use target weights, observed volatility, and the supplied correlation matrix.

Portfolio metrics include sector and factor exposures, liquidity and liquidation-horizon distributions, FX, commodity and government-linked exposures, concentration HHI, and risk contribution/volatility where meaningful. Every position stores ticker, target and maximum weights, binding constraint, signal/thesis reference, valuation inputs, confidence, liquidity capacity, exit horizon, risk contribution, exposures, and source references.

## Current production gate

Phase 14 classifies the model `UNRELIABLE`; all current Phase 8 signals are `DATA_INSUFFICIENT`, Phase 6 valuations are insufficient, and Phase 11 produces no eligible nonzero size. The production portfolio generator therefore creates empty 100%-cash research portfolios. This is a validation outcome, not a cash investment recommendation.

Run with `python3 -m uzquant construct-portfolios`.
