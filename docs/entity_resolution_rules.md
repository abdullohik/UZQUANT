# UZQUANT Entity Resolution Rules

## Evidence order

1. Verified permanent source identifier
2. ISIN
3. Registration or tax identifier
4. Exchange identifier
5. Source-specific issuer identifier
6. Ticker plus corroborating issuer evidence
7. Exact legal/source display name

Fuzzy similarity may only create a review candidate. It cannot merge entities.

Security IDs are derived from verified ISINs. Ticker is versioned metadata, never an internal key. The current RSE issuer ID uses an exact normalized source display name and records this weaker method explicitly. Duplicate ticker-to-ISIN mappings create unresolved conflicts.

Common/preferred classes are accepted only from explicit RSE detail-page labels. Suffixes are never used to infer class or economic rights.

| Issuer | Common | Preferred | Resolution |
|---|---|---|---|
| Olmaliq KMK | AGMK / UZ7000550002 | AGMKP / UZ700055K015 | Same issuer ID; distinct securities; explicit labels |
| Kapital Sug’urta | KASU / UZ7028660007 | KASUP / UZ702866K013 | Same issuer ID; distinct securities; explicit labels |

These labels establish class, not voting, dividend, liquidation, conversion or redemption rights. Historical identifier changes must append rows and never overwrite prior evidence.
