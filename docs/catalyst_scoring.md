# UZQUANT catalyst scoring

Catalyst model: `catalyst-relevance/1.0.0`  
Integrated scoring model: `research-ranking/1.1.0` / `factor-scoring/1.1.0`

## Separation of concepts

The system stores event occurrence, event materiality, direction, catalyst relevance and catalyst confidence independently. A positive event is not an investment signal and cannot repair an overvaluation, liquidity failure or data-quality failure.

Catalyst relevance is:

- `DIRECT`: a high-confidence positive event has an evidenced mechanism that may close a valuation gap;
- `POSSIBLE`: the event belongs to a plausible catalyst theme, but direction/comparative effect is incomplete;
- `NONE`: no defensible gap-closing mechanism is established from the event alone.

Supported themes include privatization/state-stake sale, strategic investor, buyback, dividend, debt/refinancing, production/capacity expansion, governance improvement, liquidity improvement and reform. Themes are assigned only when supported by the classified event—not by speculation.

## Initial scores

A HIGH-confidence positive `DIRECT` event receives 80 when materiality is HIGH and 70 otherwise. A `POSSIBLE` event receives 40 with LOW catalyst confidence. `NONE` remains unscored. These are explicit initial model assumptions, not learned return predictions.

The Phase 8 Catalyst component preserves the contributing event IDs and takes the maximum supported relevance score. Catalyst currently retains zero attractiveness weight during validation, though it contributes to model-coverage evidence. This is a versioned 1.1 update; old 1.0 signals remain unchanged.

## Real sample

The two historical dividend occurrences are `POSSIBLE` relevance scored 40 because no date-compatible evidence establishes an increase or valuation-gap effect. The capital increase is `NONE`: the issuance is verified, but its use of proceeds and economic direction are not. Management change and the QZSM decision are also `NONE`; neither is automatically treated as governance improvement or deterioration.

All real Phase 9-integrated signals remain `DATA_INSUFFICIENT`. Event positivity cannot independently convert an overvalued security into BUY, and event negativity cannot independently turn a cheap security into SELL; tests enforce both rules.
