# IPKY Valuation Trace

Status: **AVAILABLE / EXECUTABLE**

Valuation date and data cutoff: 2026-09-27

Model: `sector-valuation/3.2.0`

Method: `RESIDUAL_INCOME`

Currency/basis: nominal UZS

Confidence: LOW

## Evidence chain

1. Official Openinfo audited 2023 IFRS PDF.
2. Explicit entity match: Ipak Yuli / IPKY.
3. Explicit reporting perimeter: consolidated.
4. Explicit unit: millions of Uzbek soum; normalized to UZS.
5. Immutable normalized Equity and Net Income observations.
6. Verified class shares outstanding: 60,239,945,264.
7. Versioned scenario assumptions with provenance.
8. Deterministic five-year residual-income calculation.
9. Independent reconciliation: PASSED, maximum difference `0E-26`.

Exact valuation source document:
`7c1e86df-7f87-57b0-9d62-3f92b0f7634a`.

Exact normalized observation versions used by the valuation:

- `22c9ce88-f80d-4183-aa0d-478b295030b1`
- `5c47a3a2-06e7-4125-afac-141cfa29cfa7`

## Inputs and scenarios

| Input | Bear | Base | Bull | Provenance |
|---|---:|---:|---:|---|
| Book equity | 2,817,695,000,000 | same | same | reported, audited consolidated IFRS |
| Shares | 60,239,945,264 | same | same | verified class shares |
| ROE | 28.8540% | 29.1995% | 29.5449% | source-derived from two reported years |
| Cost of equity | 24.2410% | 22.2410% | 20.2410% | model-estimated, fully sourced components |
| Growth | 4.0% | 5.0% | 6.0% | configurable sensitivity around official target |

## Result

| Bear | Base | Bull |
|---:|---:|---:|
| 57.609857 UZS | 66.093978 UZS | 78.309260 UZS |

Latest eligible observed market price in the ranking rerun: 211 UZS. Base
valuation upside is -68.6758%; therefore the transparent valuation-factor score
is 0. IPKY still remains `DATA_INSUFFICIENT` because the aggregate framework
has only three available factors. No order or recommendation was generated.
