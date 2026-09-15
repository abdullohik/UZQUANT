# Phase 15 Sample Portfolios

Generated as of 2026-09-15. These are research-system outputs, not personalized financial advice, portfolio recommendations, or executable orders.

## Production outcome

No security passes the portfolio admission gate. Phase 14 is `UNRELIABLE`; all stored research signals are `DATA_INSUFFICIENT`; verified valuation upside/downside is unavailable; and every Phase 11 final position maximum is zero. The engine therefore preserves capital as unallocated cash instead of forcing holdings.

| Portfolio type | AUM (UZS) | Status | Positions | Cash weight |
|---|---:|---|---:|---:|
| CONSERVATIVE | 20,000,000 | DATA_INSUFFICIENT | 0 | 100% |
| BALANCED | 20,000,000 | DATA_INSUFFICIENT | 0 | 100% |
| HIGH_CONVICTION | 20,000,000 | DATA_INSUFFICIENT | 0 | 100% |
| CONSERVATIVE | 1,000,000,000 | DATA_INSUFFICIENT | 0 | 100% |
| BALANCED | 1,000,000,000 | DATA_INSUFFICIENT | 0 | 100% |
| HIGH_CONVICTION | 1,000,000,000 | DATA_INSUFFICIENT | 0 | 100% |
| CONSERVATIVE | 20,000,000,000 | DATA_INSUFFICIENT | 0 | 100% |
| BALANCED | 20,000,000,000 | DATA_INSUFFICIENT | 0 | 100% |
| HIGH_CONVICTION | 20,000,000,000 | DATA_INSUFFICIENT | 0 | 100% |

Because there are no proposed positions, position-level ticker, valuation, thesis, confidence, capacity, exit horizon, binding constraint, and risk-contribution fields have no legitimate production values. They remain absent rather than being populated with hypothetical securities or assumptions.

## AUM-capacity acceptance test

The deterministic acceptance fixture holds candidate quality and UZS 1,000,000 security capacity constant while changing portfolio AUM:

| AUM | Maximum target weight | Binding constraint |
|---:|---:|---|
| UZS 20,000,000 | 5.0000% | LIQUIDITY |
| UZS 1,000,000,000 | 0.1000% | LIQUIDITY |
| UZS 20,000,000,000 | 0.0050% | LIQUIDITY |

This fixture validates model mechanics and is not presented as real security performance. It demonstrates the acceptance condition: increasing capital reduces the feasible allocation when market capacity is fixed.

## Other tested controls

- highly correlated holdings share a group cap;
- same-sector holdings cannot exceed the sector cap;
- an illiquid holding receives less weight than an otherwise identical liquid holding;
- confidence below the configured minimum excludes the candidate;
- deteriorating liquidity reduces target weight;
- unused allocation remains cash;
- risk contribution is calculated only when volatility and correlation inputs support it.

## Current metric availability

Sector, factor, liquidity, FX, commodity, government-linked, concentration, liquidation, correlation, and historical-risk metrics are unavailable for the empty production portfolios. They are stored with explicit `UNAVAILABLE / NO_ELIGIBLE_POSITIONS` status. No diversification or historical-risk benefit is inferred.
