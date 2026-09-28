# Issuer-level Valuation Worklist

Generated: 2026-09-28T12:11:54.897998+00:00. Version: `issuer-valuation-unlock/1.0.0`.

Ranking is deterministic: maximum issuer-level average daily turnover descending, then maximum evidence-readiness score descending; banks/insurers break exact ties, followed by legal name. Capped at 12 issuers. It is not an attractiveness ranking.

| Rank | Issuer | Current equities | Issuer max ADV (UZS) | Max readiness | Tie class |
| --- | --- | --- | --- | --- | --- |
| 1 | <Qizilqumsement> AJ | QZSM | 4495574.95 | 85 | OTHER |
| 2 | <O'zbektelekom> AK | UZTL, UZTLP | 4480004.60 | 85 | OTHER |
| 3 | <Olmaliq KMK> AJ | AGMK, AGMKP | 3041272.56 | 81 | OTHER |
| 4 | AITB <Ipak Yo'li> | IPKY | 3022540.38 | 85 | OTHER |
| 5 | <Kapital sug'urta> AJ | KASU, KASUP | 33743.59 | 83 | BANK/INSURER |
| 6 | <O'zbekgeofizika> AJ | UZGF, UZGFP | 0.00 | 46 | OTHER |
| 7 | <UzAuto Motors> AJ | UZMT | 0.00 | 46 | OTHER |
| 8 | <Biokimyo> AJ | BIOK | 0.00 | 41 | OTHER |
| 9 | <Agrobank> ATB | AGBA, AGBAP | 0.00 | 39 | BANK/INSURER |
| 10 | <Hamkorbank> ATB | HMKB, HMKBP | 0.00 | 39 | BANK/INSURER |
| 11 | <O'zbekiston pochtasi> AJ | UPOS, UPOSP | 0.00 | 29 | OTHER |
| 12 | <Bekobodsement> AJ | BECM | 0.00 | 25 | OTHER |

## Free-win and derived-metric audit

| Item | Outcome | Evidence / exact remaining reason |
| --- | --- | --- |
| Average assets / ROA / asset turnover | GENERAL FIX APPLIED | Opening and closing Total Assets now require identical currency, unit, perimeter, standard and audit metadata; lineage contains both source versions. One ROA became available. |
| Prior-period growth | GENERAL FIX APPLIED | The engine now loads only same-duration, one-year-prior documents published by the decision date and filters each concept for identical metadata. No growth value became available because work-list public reports still lack compatible verified metadata. |
| Average equity / ROE | VERIFIED | Existing strict averaging pattern retained; one ROE is available with full lineage. |
| Average invested capital / ROIC | REMAINS UNAVAILABLE | NOPAT and a compatible opening/closing invested-capital basis are not both source-backed; no proxy was invented. |
| EPS / BVPS / TBVPS | REMAINS UNAVAILABLE EXCEPT EXISTING VALUATION USE | Mixed common/preferred capital requires class earnings/equity allocation and verified rights; EPS or per-share book values were not divided across classes by assumption. |
| Net debt | VERIFIED | Strict Cash + Short-Term Debt + Long-Term Debt calculation; 17 version-1.1 records available and none converts missing inputs to zero. |
| Growth / margins | PARTIAL | 34 gross/net margin records are available; growth remains blocked by incompatible or UNKNOWN metadata. |
| Known five DATA_ALREADY_PRESENT_NOT_NORMALIZED | NOT CLOSED BY INVENTION | UZTL, QZSM, AGMK/AGMKP and UZTLP still lack source-backed OCF/CapEx/EBITDA (and applicable D&A/EBIT) in the retained statutory pages. This is now an exact concept/source limitation, not a silent zero. |
| Known eight MODEL_INTEGRATION_GAP | REASSESSED | All methods were rerun independently. IPKY Residual Income remains executable; UZTL, KASU, QZSM, AGMK/AGMKP, KASUP and historical IPKYP remain rejected by their recorded method blockers. |
