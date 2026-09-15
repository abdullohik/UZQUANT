# UZQUANT event taxonomy and ingestion

Event model: `event-classification/1.0.0`

## Point-in-time record

Each event stores a stable event ID, issuer, explicitly affected securities, publication date/time, separate effective date, type, summary, materiality, direction, horizon, confidence, classification method and optional LLM model/prompt versions. Evidence is stored in immutable source links with the raw-document ID, upstream record ID, URL, publication date and source text.

Events are visible to a historical query only on or after publication. An effective date before publication does not make the information historically available sooner.

Duplicate copies from the same source are idempotent. Independently sourced records join an event only through a deterministic canonical key containing authoritative issuer, type and effective/event date; fuzzy text does not silently merge events. Each corroborating source remains a separate source link.

## Types

| Type | Definition |
|---|---|
| `DIVIDEND` | Class-specific dividend declaration or distribution evidence |
| `PRIVATIZATION` | Formal privatization action or program inclusion |
| `STATE_STAKE_SALE` | Announced/completed disposal of a state holding |
| `STRATEGIC_INVESTOR` | Identified strategic-investor entry or process |
| `ACQUISITION` / `MERGER` | Acquisitions or legal combinations |
| `CAPITAL_INCREASE` | Verified new issuance or registered capital increase |
| `BUYBACK` | Issuer repurchase program or transaction |
| `LARGE_CONTRACT` | Contract whose materiality is evidenced |
| `BORROWING` / `REFINANCING` | Material debt raising or refinancing |
| `MANAGEMENT_CHANGE` / `AUDITOR_CHANGE` | Disclosed officer/director or auditor changes |
| `RELATED_PARTY` | Related/affiliate transaction |
| `LEGAL` / `REGULATORY` | Material legal or regulatory development |
| `PRODUCTION_EXPANSION` | Verified capacity/production expansion |
| `ASSET_SALE` / `RESTRUCTURING` | Material disposal or restructuring |
| `BANKRUPTCY` | Formal insolvency/bankruptcy development |
| `OTHER` | Evidence exists but does not safely fit another type |

Direction is one of `STRONG_NEGATIVE`, `NEGATIVE`, `NEUTRAL`, `POSITIVE`, or `STRONG_POSITIVE`. `NEUTRAL` means no defensible directional implication was established; it is not a claim of no economic impact. Materiality (`LOW/MEDIUM/HIGH/UNKNOWN`) and horizon are separate.

## Classification methods

Deterministic mappings are preferred. An LLM classifier must retain evidence, source, confidence, model version and prompt version. Below 75% classification confidence, the supplied helper conservatively returns `OTHER`, `NEUTRAL`, and LOW confidence. It never creates numerical financial effects.

## Real validation

The engine normalized five existing official Openinfo occurrences: AGMK class-specific dividends, UZTL class-specific dividends, UZTL capital increase, UZTL management change and a QZSM shareholder-meeting decision. Manual inspection reconciled every date, affected security, type and source URL to the Phase 5 stored record. The UZTL dilution and new-issuance upstream records were recognized as one event rather than double counted.

Operator command: `python3 -m uzquant update-events`.
