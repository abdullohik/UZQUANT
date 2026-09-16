# Remediation C Universe Status

## Current supported universe

| Ticker | Valuation state | Liquidity state | Research state | Explanation |
|---|---|---|---|---|
| AGMK | Not evaluated as a priority valuation target | UNASSESSABLE | LIQUIDITY_TRAP | extreme staleness/zero-volume dominance; unreliable last price |
| AGMKP | VALUATION_INSUFFICIENT | LIQUIDITY_TRAP | DATA_INSUFFICIENT | no valuation anchor/perimeter; partial preferred rights; critical liquidity |
| IPKY | VALUATION_INSUFFICIENT | INVESTABLE (LOW confidence) | DATA_INSUFFICIENT | bank data improved, but no sourceable valuation anchor/perimeter and only two supported factors |
| KASU | Not evaluated as a priority valuation target | INVESTABLE (LOW confidence) | DATA_INSUFFICIENT | insufficient supported factors/valuation evidence |
| KASUP | VALUATION_INSUFFICIENT | INVESTABLE (LOW confidence) | DATA_INSUFFICIENT | no valuation anchor/perimeter; preferred rights partial; only two supported factors |
| QZSM | VALUATION_INSUFFICIENT | LIMITED_LIQUIDITY (LOW confidence) | DATA_INSUFFICIENT | no valuation anchor/perimeter; only three supported factors |
| UZTL | VALUATION_INSUFFICIENT | INVESTABLE (LOW confidence) | HOLD | five supported components include evidence-based Governance; low confidence and no valuation remain explicit |

## Counts

- VALUED: 0
- VALUATION_INSUFFICIENT: 5 priority securities
- DATA_INSUFFICIENT: 5 universe securities
- LIQUIDITY_UNASSESSABLE: 1
- OTHER_EXPLICIT_STATE: 1 HOLD and 1 LIQUIDITY_TRAP research classification
- Current AVAILABLE factor-score rows: 21 universe-wide
- Current attractiveness scores: 1

These categories overlap by layer: valuation status, liquidity status, and final research state are deliberately separate. The absence of BUY states is not a remediation failure.

## Production-data limitations

The supported universe still has only 20 recent observations per priority security, incomplete ownership/free-float coverage, no approved peer set or discount-rate input stack, incomplete cash-flow concepts, unknown reporting perimeter, and incomplete preferred-security legal terms. Momentum and historical multiple methods remain unavailable rather than receiving artificial neutral values.
