# Targeted Company-Evidence Valuation Unlock

Date: 2026-09-27

Scope: continuation of the First Valuation Unlock Sprint

Outcome: **one validated production valuation unlocked; broadening stopped**

## Result

IPKY now has an executable, source-traceable residual-income valuation under
`sector-valuation/3.2.0`. This is the first production valuation in the current
five-security validation set. The run produced 1 `AVAILABLE` valuation and 30
`VALUATION_INSUFFICIENT` method/security combinations. No value, signal, gate,
or readiness criterion was forced.

The stopping rule was applied after the IPKY breakthrough. UZTL, QZSM, KASUP,
and AGMKP received only the limited evidence review needed to record their next
blockers.

## IPKY evidence recovered

The official Openinfo annual-report record links the audited 2023 PDF. The PDF
identifies Ipak Yuli, states IFRS, explicitly calls the statements consolidated,
and labels statement amounts as millions of Uzbek soum. The deterministic
parser fails closed if any of those assertions is absent.

Production storage now preserves the original PDF, hash, retrieval metadata,
document identity check, reporting-perimeter evidence, source-unit evidence,
10 raw values, and immutable normalized versions. The valuation uses:

| Input | 2023 | 2022 | Unit / status |
|---|---:|---:|---|
| Total assets | 16,914,336,000,000 | 13,125,912,000,000 | UZS, reported |
| Total liabilities | 14,096,641,000,000 | 10,992,891,000,000 | UZS, reported |
| Equity | 2,817,695,000,000 | 2,133,021,000,000 | UZS, reported |
| Net income | 731,342,000,000 | 522,935,000,000 | UZS, reported |
| Intangibles | 32,929,000,000 | 24,987,000,000 | UZS, reported |
| Class shares outstanding | 60,239,945,264 | — | verified existing security evidence |

Document ID: `7c1e86df-7f87-57b0-9d62-3f92b0f7634a`.

## Valuation method

The bank engine uses a five-year residual-income model plus continuing value.
It does not use industrial EV/EBITDA as the primary method. All values are
nominal UZS; no FX conversion is used.

ROE is source-derived from reported net income divided by average opening and
closing equity. The 2022 and 2023 ROEs are 28.8540% and 29.5449%; the base
normalized ROE is their mean, 29.1995%.

The nominal UZS cost of equity is a transparent research estimate, not an
observed WACC. It begins with the effective annual equivalent of the official
CBU 10-year continuously compounded government zero rate, removes the cited
sovereign default spread to avoid double-counting it as default-free return,
then adds regional-bank beta times mature-market ERP and the Uzbekistan country
risk premium. Base cost of equity is 22.2410%, with +/-2 percentage-point bear
and bull sensitivities. Terminal growth is 4% / 5% / 6%, centered on the CBU's
5% medium-term inflation target.

| Scenario | ROE | Cost of equity | Growth | Fair value/share (UZS) |
|---|---:|---:|---:|---:|
| Bear | 28.8540% | 24.2410% | 4.0% | 57.6099 |
| Base | 29.1995% | 22.2410% | 5.0% | 66.0940 |
| Bull | 29.5449% | 20.2410% | 6.0% | 78.3093 |

Confidence is `LOW`: the financial year is stale relative to the valuation
date, and beta/ERP/CRP are external research assumptions. The independently
recomputed values match stored values exactly (`0E-26` maximum difference).

## Downstream outcome

The current research chain was rerun: fundamentals, valuation, liquidity, and
ranking. IPKY's valuation factor is now available with score 0 because the base
value of 66.094 UZS is below the latest eligible observed price of 211 UZS.
IPKY remains `DATA_INSUFFICIENT`, confidence 58.75, because only 3 factors are
available; quality, growth, momentum, dividend, governance, catalyst, and
balance-sheet-risk factors remain unavailable. This is the correct fail-closed
result and is not an investment recommendation.

The rerun also corrected a compatibility defect: current ranking previously
used a hard-coded 2026-09-15 cutoff and therefore could not see a 2026-09-27
valuation. The default now uses the actual run date. No gate or threshold
changed.

## Limited follow-up

- UZTL: the official 2025 audited PDF is machine-readable and explicitly
  consolidated IFRS in thousand UZS. It appears suitable for a later
  deterministic ingestion extension. It was not imported in this sprint after
  the stop threshold. A relative valuation still needs a credible compatible
  peer set; DCF additionally needs cash-flow mappings and supported forecast,
  debt-cost, and capital-structure assumptions.
- QZSM: the official attachment recovered in this review is a two-page auditor
  opinion under Uzbekistan national standards, not the underlying statements.
  It verifies audit scope but does not supply valuation-critical statement
  lines. Reporting perimeter and full primary statements remain unresolved.
- KASUP: official exchange records confirm the preferred class and current
  charter availability, but exact class economics have not yet been
  deterministically extracted and versioned. Reporting perimeter and a credible
  insurer peer set also remain blockers.
- AGMKP: official issuer material supports historical 25%-of-nominal preferred
  dividends, but current effective class rights and value allocation have not
  yet been fully versioned. Reporting perimeter, mining operating inputs, and
  forecast assumptions remain blockers.

## Reproducibility

Operator command:

```text
python -m uzquant targeted-valuation-unlock
```

The command reuses a hash-verified archived official PDF when available and
only refetches when no valid archive exists. Tables added are
`valuation_assumption_details` and `valuation_reconciliations`. Prior valuation
records are preserved under their original model versions.
