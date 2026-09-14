# UZQUANT Security Master Schema

The schema is created reproducibly by ordered SQL migrations in uzquant/migrations. Internal issuer and security IDs are deterministic UUIDs and do not depend on ticker.

## Core tables

| Table | Purpose |
|---|---|
| data_sources | Authority, domain, verified access status and source configuration |
| ingestion_runs | Run ID, source, start/end, status, processed count, errors and parser version |
| raw_documents | Immutable source URL, timestamps, SHA-256 and raw storage path |
| issuers | Stable issuer identity and optional identifiers/classification |
| issuer_name_history | Provenanced legal, short, historical and display names |
| security_classes | Common, preferred, other and unknown vocabulary |
| securities | Stable issuer-linked instrument, class, type, nominal value and currency |
| listings | Exchange/board, status, listing/delisting dates and knowledge time |
| identifier_history | Effective-dated issuer/security identifiers with provenance |
| resolution_conflicts | Unresolved, resolved or rejected identity candidates |

Raw, normalized and derived directories are distinct. Raw-document metadata cannot be updated or deleted. Missing values remain NULL or UNKNOWN; they are never converted to zero.

## Commands

    python3 -m uzquant init-db
    python3 -m uzquant update-security-master
    python3 -m unittest discover -s tests -v

Typed settings support UZQUANT_DATABASE_PATH, UZQUANT_RAW_DATA_DIR, UZQUANT_REQUEST_TIMEOUT, UZQUANT_RETRY_ATTEMPTS and UZQUANT_RETRY_BACKOFF. Secrets are environment-only; the public RSE source requires none.
