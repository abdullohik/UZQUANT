# Fundamental metrics dictionary

Formula version: `fundamental-metrics/1.0.0`. All ratios use unrounded `Decimal` inputs. A zero denominator returns `UNAVAILABLE / ZERO_DENOMINATOR`; a missing or ambiguous concept returns `UNAVAILABLE`, never zero. Every stored result links to its source observation IDs, document IDs, and source period.

## General non-financial engine

| Metric | Deterministic formula |
|---|---|
| Revenue / EBITDA / EBIT / Net Income Growth | current / compatible prior − 1 |
| Gross / EBITDA / EBIT / Net Margin | relevant profit / revenue |
| ROA / ROE | net income / average assets or equity |
| ROIC | NOPAT / average invested capital |
| Asset Turnover | revenue / average assets |
| Current Ratio | current assets / current liabilities |
| Quick Ratio | (current assets − inventory) / current liabilities |
| Debt/Equity | (short-term debt + long-term debt) / equity |
| Net Debt | short-term debt + long-term debt − cash |
| Net Debt/EBITDA | net debt / EBITDA |
| Interest Coverage | EBIT / interest expense |
| Operating Cash Flow Margin | operating cash flow / revenue |
| Free Cash Flow | operating cash flow − CapEx |
| FCF Margin | free cash flow / revenue |
| CapEx/Sales | CapEx / revenue |
| Dividend Payout Ratio | dividends / net income |

Average-balance ratios require actual beginning and ending compatible balances. Ending balances are not substituted. NOPAT is not inferred without a valid tax basis.

## Accounting quality

| Metric or flag | Definition |
|---|---|
| CFO / Net Income; Cash Conversion | operating cash flow / net income |
| FCF / Net Income | free cash flow / net income |
| Accrual Measure | (net income − CFO) / average assets |
| Receivables or Inventory Growth vs Revenue Growth | relevant growth minus revenue growth |
| Working-Capital Intensity | (receivables + inventory − accounts payable) / revenue |
| CapEx Intensity | CapEx / revenue |
| D&A vs CapEx | D&A / CapEx |
| Debt Growth | current total debt / prior total debt − 1 |
| `RECEIVABLES_GROWING_FASTER_THAN_REVENUE` | difference > 10 percentage points |
| `POOR_CASH_CONVERSION` | CFO / net income < 0.70 |
| `RAPID_DEBT_GROWTH` | debt growth > 30% |
| `INVENTORY_ANOMALY` | inventory growth exceeds revenue growth by > 15 points |

Threshold flags are deterministic investigation prompts, not investment signals.

## Sector engines

- Bank: Assets, Loans, Deposits, Equity, Net Interest Income, NIM, ROA, ROE, Loan/Deposit Growth, NPL, Provisioning, Capital Adequacy, and Cost/Income. Average earning assets are required for NIM.
- Insurance: Premium Growth, Claims, Loss/Expense/Combined Ratios, Investment Income, Reserves, ROE, and Solvency.
- Mining: Production, Unit Costs, Capital Intensity, Commodity Exposure, and Operating Leverage.
- General: the non-financial formulas above.

Routing uses explicit Openinfo report categories for banks and insurers. Mining routing requires an explicit issuer sector; ticker or company-name guesses are prohibited. Unsupported concepts remain unavailable.

## Historical and TTM rules

YoY, 3Y, and 5Y comparisons require matching period length plus identical known currency, unit, perimeter, and accounting standard. Unknown metadata blocks comparison. TTM requires exactly four adjacent, non-overlapping quarterly periods with identical known metadata. Annual or cumulative filings are never split into invented quarters.

Run `python3 -m uzquant calculate-fundamentals`, then query an issuer with `python3 -m uzquant query-fundamentals --ticker AGMKP`.
