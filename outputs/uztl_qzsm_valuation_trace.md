# UZTL and QZSM Limited Valuation Trace

The sprint stopped broad evidence expansion after IPKY became valuation-ready.
This file records only the efficient-unlock determination.

## UZTL

An official Openinfo-linked 2025 audited report was retrieved and inspected. It
is machine-readable, explicitly titled consolidated financial statements,
states IFRS, and states that all amounts are rounded to thousand Uzbek soum.
It includes primary statements and notes. This is a strong candidate for the
next deterministic document-ingestion increment.

Source: `https://openinfo.uz/media/audit_conclusion/e15a4a62-8263-4c57-9a5e-fe54d890e9f0.pdf`

No production valuation was created in this sprint. Current blockers remain:

- the recovered 2025 PDF is not yet in normalized production storage;
- P/E and P/B require a minimum credible, compatible peer set;
- EV methods need normalized EBIT/EBITDA;
- FCF/DCF methods need mapped operating cash flow, CapEx, D&A, and debt/cash;
- DCF requires supported forecasts, cost of debt, and capital structure.

Current production status: `VALUATION_INSUFFICIENT` for every UZTL method.

## QZSM

The official 2024 attachment inspected is a two-page independent-auditor
opinion. It states that the audited financial statements comprise the balance
sheet, comprehensive income, changes in equity, cash flows, and notes and that
they follow Uzbekistan national standards. The attachment itself does not
contain those statement pages or valuation-critical line values.

Source: `https://openinfo.uz/media/audit_conclusion/c8224bae-c43b-4915-af7e-d2e24ad69887.pdf`

Current blockers remain:

- underlying full financial statements are not present in the recovered file;
- reporting perimeter is not explicit;
- P/E and P/B need a credible compatible peer set;
- EV methods need EBIT/EBITDA;
- FCF/DCF methods need cash-flow lines and supported model assumptions.

Current production status: `VALUATION_INSUFFICIENT` for every QZSM method.
