# IPKY Full Lineage After Correction

Assessment date: 2026-09-28

## Evidence to valuation

Official Openinfo audited PDF → hash-preserved raw document `0ca469d0-ecca-5875-94a8-1c11d1f6fb77` → financial document `7c1e86df-7f87-57b0-9d62-3f92b0f7634a` → raw values → immutable normalized versions → source-derived ROE assumptions → residual-income valuation `1086109d-7a3f-5ff8-bd0f-5e85ccd27abb`.

| Input actually used | Period | Value (UZS) | Exact version | Transformation role |
|---|---:|---:|---|---|
| Equity | 2021-12-31 | 1,491,673,000,000 | `f0fa4084-dcb6-4f63-9ad8-064a20aa21d4` | Opening equity for 2022 average equity |
| Equity | 2022-12-31 | 2,133,021,000,000 | `b7da6692-c156-4d54-9839-425306c0efef` | Closing 2022/opening 2023 equity |
| Net Income | 2022-12-31 | 522,935,000,000 | `fc16f3b3-4a24-41e2-b6e2-3ba180385bf0` | 2022 ROE numerator |
| Equity | 2023-12-31 | 2,817,695,000,000 | `ede43c2c-5eba-48a8-b899-50ccc968a5ba` | Closing 2023 equity/current book value |
| Net Income | 2023-12-31 | 731,342,000,000 | `d1cff2ba-21da-4edc-9a27-2df59789dfb1` | 2023 ROE numerator |

All five IDs are present in the valuation's `source_observation_ids_json`. Each record retains raw value, normalized value, source document/location, period, UZS currency/unit, consolidated perimeter, IFRS standard, audited status, parser/taxonomy/normalization version, publication date, and knowledge timestamp.

ROE assumption lineage is stored relationally in `valuation_assumption_observation_lineage`. Bear ROE links 2021 equity, 2022 equity, and 2022 income; bull ROE links 2022 equity, 2023 equity, and 2023 income; base ROE links all five and records `NORMALIZED_ROE=MEAN(ROE_2022,ROE_2023)`.

## Valuation to signal

- Residual income (`sector-valuation/3.2.0`): AVAILABLE, LOW confidence; bear 57.6098572111716, base 66.0939781562458, bull 78.3092595811942 UZS/share.
- Quality metric: 2023 ROE 0.2954489815210567521950360312.
- Available factors: Valuation 0; Quality 29.54489815210567521950360312; Liquidity 60; Data Quality 90.
- Unavailable factors: Growth, Momentum, Dividend, Governance, Catalyst, Balance-Sheet Risk, each with its preserved explicit reason.
- Available positively weighted factors: 4; required: 4.
- Hard gates: none.
- Attractiveness: 29.88622453802641880487590078; confidence: 59.75.
- Resulting state: `REDUCE` (research classification only).

Exact signal lineage traverses only records referenced by this signal's factor records and their underlying analytical lineage. It excludes unrelated observations from the same issuer and future analytical rows.
