# Phase 1 Real Security-Master Validation

Validation date: 2026-09-14
Run ID: cb164567-0c3a-44af-8050-53f0c3ea4ad0
Parser: rse-security-master/1.0.0

## Source

- Primary: Republican Stock Exchange “Toshkent”
- Universe: <https://uzse.uz/asking_prices>
- Required-sample details: https://uzse.uz/isu_infos/{ISIN}/detail?locale=en
- Anonymous HTTPS; no bypass
- Raw responses archived locally with timestamps and SHA-256 hashes
- Run result: SUCCEEDED

## Counts

| Measure | Result |
|---|---:|
| Records processed | 74 |
| Issuers loaded | 53 |
| Securities loaded | 74 |
| Unresolved conflicts | 0 |
| Missing ISIN | 0 |
| Missing ticker | 0 |
| COMMON | 5 |
| PREFERRED | 4 |
| UNKNOWN class | 65 |

| Ticker | ISIN | Class | Result |
|---|---|---|---|
| AGMK | UZ7000550002 | COMMON | Same issuer as AGMKP; distinct security |
| AGMKP | UZ700055K015 | PREFERRED | Verified |
| KASU | UZ7028660007 | COMMON | Same issuer as KASUP; distinct security |
| KASUP | UZ702866K013 | PREFERRED | Verified |
| IPKY | UZ7039920002 | COMMON | Verified |
| UZTL | UZ7047110000 | COMMON | Verified |
| QZSM | UZ7029000005 | COMMON | Verified |

## Missing identifiers and limitations

No ingested security lacks ISIN or ticker. Issuer permanent IDs, TIN, registration/Openinfo/depository IDs and LEIs remain missing. Historical tickers/ISINs were not asserted.

The 74 records are securities discoverable on the retrieved page, not proof of all historical/delisted securities. Only required detail pages were requested, so 65 classes remain UNKNOWN rather than guessed. Listing/delisting dates, sector, industry and legal share rights remain unavailable. ACTIVE means present in this source snapshot, not actively traded. Raw responses are excluded from Git pending licensing review.
