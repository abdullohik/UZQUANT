# Governance event framework

Governance events retain issuer/security scope, event date, disclosure date, source evidence, confidence and classification method. Supported classifications include related-party/affiliate transactions, auditor changes, restatements, late filings, management changes, dilution, unusual borrowing, major asset transfers and minority-holder issues, plus a neutral governance-decision category.

Current validation uses deterministic official fact types and table fields—no LLM classification. Openinfo fact 25 maps to `DILUTION`, fact 8 to `MANAGEMENT_CHANGE`, and the QZSM shareholder vote remains neutral `GOVERNANCE_DECISION`. Events are evidence for review, not positive or negative investment signals.

Conflicting disclosures are preserved in `corporate_data_conflicts` with `UNRESOLVED` status. The system never silently chooses a preferred value. Publication-date filtering prevents look-ahead use.
