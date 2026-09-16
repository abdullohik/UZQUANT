# UZQUANT Model Risk Register

## Governing conclusion

Model risk is dominated by entity integrity and missing evidence, not by measured return instability. No performance sample exists, so absence of observed failure must not be interpreted as robustness.

| Risk | Severity | Current evidence | Control | Residual risk |
|---|---|---|---|---|
| Issuer collision / report misassignment | CRITICAL | Name-derived issuer ID and ticker-only report lookup reproduced | Security IDs use ISIN; some entity checks exist | Unacceptable until canonical issuer mapping is repaired and re-audited |
| Normalized financial reinterpretation | HIGH | Reparse deletes/replaces normalized observations | Raw documents and hashes retained | Historical normalized version cannot always be reconstructed |
| Source format drift | HIGH | Generic check exists but no production integration | Required-label parsers often raise | Silent semantic shifts remain possible |
| Degraded upstream propagation | HIGH | DEGRADED is neither blocked nor shown in security warnings | FAILED/STALE propagation works | Partial failures may look more current than warranted |
| Prospective financial lineage | HIGH | Snapshot freezes documents/factors/signals, not all normalized values | Snapshot/state tables immutable | Exact financial input version not self-contained |
| Wrong units/currency/perimeter | HIGH inherent, currently gated | 81 unspecified units; 16 unknown perimeters | Valuation returns insufficient; TTM/FX checks | Prevents valuation rather than producing an observed wrong value |
| Preferred rights/value allocation | HIGH inherent, currently gated | Preferred rights low/missing | Rights-specific gates and valuation insufficiency | No preferred valuation can be relied upon |
| Share-count conflict | HIGH latent | No current same-date conflict | Verified/effective-date filter | No authority/tie-break rule for a future verified conflict |
| Liquidity/execution error | HIGH inherent | No spread/depth history | Participation limits, no-fill, stale gates | Slippage and capacity cannot be empirically calibrated |
| Survivorship/lookahead | HIGH inherent | Universe and vintages incomplete | Backtest refuses to run | Strategy validity remains unknown |
| Parameter/selection overfit | HIGH untestable | Zero completed backtests/OOS periods | Experiment registry and locked OOS design | Cannot be measured |
| Macro vintage error | MEDIUM-HIGH | Release/revision dates missing | First-observed append-only vintage | Historical real-time macro state incomplete |
| Event classification | MEDIUM | Current events deterministic and sourced | Evidence/method/confidence retained | Sparse coverage; no LLM error sample |
| Portfolio concentration/correlation | MEDIUM latent | No real positions | Transparent caps and conservative missing-correlation handling | Real interaction untested |
| Confidence miscalibration | HIGH untestable | Zero prospective outcomes | Separate confidence and sample-size fields | Cannot be calibrated yet |

## Model-risk interpretation

The model is not shown to be bad or good. It is unvalidated. Critical data integrity must be repaired before model performance evidence would be meaningful. After that, prospective accumulation—not parameter tuning against the current tiny sample—should be the primary validation path.
