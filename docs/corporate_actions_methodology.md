# Corporate actions and dividends methodology

Phase 5 uses official Openinfo structured HTML disclosures and archives every response with URL, retrieval time and SHA-256. Action identity is tied to the issuer and, when the disclosure identifies the class, the canonical security. Announcement means the public disclosure date; decision, record, effective and payment dates remain separate.

Supported persistent action types include splits, reverse splits, bonus shares, rights issues, capital increases/reductions, new issuance, conversions, mergers, spin-offs, buybacks, tender offers and delistings. Only `NEW_ISSUANCE` was actually encountered in the validation sources. The UZTL issuance is linked to the explicitly disclosed ordinary share, not inferred from ticker syntax.

No adjustment factor is generated unless an authoritative disclosure establishes it. Phase 5 therefore creates no adjusted prices. Dividends are stored by security ID and class, with announcement, ex/record/payment dates only where published, amount per share, currency, type and source.

Parser version: `openinfo-corporate/1.0.0`. Operator command: `python3 -m uzquant update-corporate-intelligence`.
