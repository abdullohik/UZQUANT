# Entry-Zone Engine

The entry engine converts a valid security-level bear/base/bull valuation into five configurable research zones. It never derives technical support/resistance levels and does not invent a fair value when Phase 6 returns `VALUATION_INSUFFICIENT`.

For an available monotonic valuation range, the engine starts with a base margin of safety, adds an explicit risk allowance, then widens the margin as valuation dispersion rises and confidence falls. Version 1.0 defaults are a 20% base margin, 5% risk addition, 25% uncertainty weight, and a 5%–60% clamp. These are model assumptions, not source facts.

The four ascending boundaries around base value classify observed price as `STRONG_BUY_ZONE`, `ACCUMULATE_ZONE`, `FAIR_VALUE_ZONE`, `TRIM_ZONE`, or `OVERVALUED_ZONE`. Bear and bull values affect the uncertainty adjustment; base value anchors the boundaries. Invalid, missing, non-positive, or non-monotonic ranges return `ENTRY_INSUFFICIENT`.

Every stored result retains the valuation record, observed price, boundaries, effective margin, assumptions, reasons, as-of date, and `valuation-entry-zones/1.0.0` version. A zone is research model output and is not an executable order or personalized financial advice.
