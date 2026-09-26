# RSE Historical Trade Acquisition

UZQUANT maintains a persistent queue of exact-ISIN, calendar-month RSE export requests. The production two-year plan covers 2024-09-27 through 2026-09-27 for active STK securities in the verified security master.

## Safety and evidence rules

- Acquisition uses the official RSE trade-results export only.
- Each job records the exact ISIN, requested dates, market, attempts, status, file hash, and resulting capture.
- A workbook is rejected if its ISIN, market, or trade dates differ from the job.
- Raw workbooks are archived immutably and parsed transactions retain row-level provenance.
- Empty exports remain explicit `EMPTY` results.
- Failed or inaccessible sources remain `SOURCE_BLOCKED` or `FAILED`; the system does not fabricate substitute data.
- Current-day captures remain partial and are not promoted to complete daily OHLC.

## Operator commands

```text
python3 -m uzquant plan-rse-history --begin 2024-09-27 --end 2026-09-27 --market STK
python3 -m uzquant next-rse-export
python3 -m uzquant import-rse-inbox --inbox data/import/rse
python3 -m uzquant rse-history-status
```

`next-rse-export` returns the official export URL and the exact required inbox filename. After the official XLSX is downloaded, save it under that filename in `data/import/rse/` and run the inbox importer. Repeated planning and importing are idempotent.
