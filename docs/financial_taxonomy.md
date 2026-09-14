# Financial taxonomy

UZQUANT stores source rows before attempting normalization. A normalized observation is created only when a shared phrase rule maps the reported label to a canonical concept. Unmapped rows remain in `financial_raw_values`; they are never inferred as zero or silently discarded.

The canonical namespace covers Revenue, COGS, Gross Profit, Operating Expenses, EBITDA, D&A, EBIT, Interest Expense, Pretax Income, Taxes, Net Income, Minority Interest, EPS, Cash, Receivables, Inventory, Current Assets, PP&E, Investments, Intangibles, Other Assets, Total Assets, Accounts Payable, Short-Term Debt, Long-Term Debt, Other Liabilities, Total Liabilities, Share Capital, Retained Earnings, Equity, Operating Cash Flow, CapEx, Investing Cash Flow, Financing Cash Flow, Dividends, and Free Cash Flow.

Mappings are centralized in `uzquant/financial_taxonomy.py`, not embedded per issuer. English, Russian, and Uzbek phrase variants are supported and extensible. A concept appearing in the namespace does not imply that a source reported it. EBITDA and Free Cash Flow are not derived in Phase 3 because the necessary components and definitions are not consistently available.

Values retain their exact source text, parsed decimal, source location, extraction method, confidence, and reported/derived/estimated status. Phase 3 records values as `AS_REPORTED`; it does not reverse expense signs. Source unit and currency remain unspecified when the report page does not explicitly establish them.
