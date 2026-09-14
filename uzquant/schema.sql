PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sources (
    source_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    domain TEXT NOT NULL,
    authority_level TEXT NOT NULL CHECK (authority_level IN ('PRIMARY', 'SECONDARY')),
    access_status TEXT NOT NULL CHECK (access_status IN (
        'VERIFIED_AUTOMATED', 'VERIFIED_MANUAL', 'PARTIAL',
        'RESTRICTED', 'UNKNOWN', 'UNAVAILABLE'
    )),
    terms_notes TEXT,
    UNIQUE(name, domain)
);

CREATE TABLE IF NOT EXISTS source_snapshots (
    snapshot_id INTEGER PRIMARY KEY,
    source_id INTEGER NOT NULL REFERENCES sources(source_id),
    source_url TEXT NOT NULL,
    retrieved_at TEXT NOT NULL,
    publication_at TEXT,
    media_type TEXT NOT NULL,
    sha256 TEXT NOT NULL CHECK (length(sha256) = 64),
    raw_content BLOB NOT NULL,
    UNIQUE(source_url, retrieved_at)
);

CREATE INDEX IF NOT EXISTS idx_source_snapshots_sha256
ON source_snapshots(sha256);

CREATE TRIGGER IF NOT EXISTS prevent_source_snapshot_update
BEFORE UPDATE ON source_snapshots
BEGIN
    SELECT RAISE(ABORT, 'source snapshots are immutable');
END;

CREATE TRIGGER IF NOT EXISTS prevent_source_snapshot_delete
BEFORE DELETE ON source_snapshots
BEGIN
    SELECT RAISE(ABORT, 'source snapshots are immutable');
END;

CREATE TABLE IF NOT EXISTS issuers (
    issuer_id INTEGER PRIMARY KEY,
    canonical_name TEXT NOT NULL,
    country_code TEXT NOT NULL DEFAULT 'UZ',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS issuer_identifiers (
    issuer_identifier_id INTEGER PRIMARY KEY,
    issuer_id INTEGER NOT NULL REFERENCES issuers(issuer_id),
    identifier_type TEXT NOT NULL,
    identifier_value TEXT NOT NULL,
    valid_from TEXT,
    valid_to TEXT,
    known_at TEXT NOT NULL,
    snapshot_id INTEGER NOT NULL REFERENCES source_snapshots(snapshot_id),
    CHECK (valid_to IS NULL OR valid_from IS NULL OR valid_to >= valid_from),
    UNIQUE(identifier_type, identifier_value, valid_from, known_at)
);

CREATE TABLE IF NOT EXISTS securities (
    security_id INTEGER PRIMARY KEY,
    issuer_id INTEGER NOT NULL REFERENCES issuers(issuer_id),
    security_class TEXT NOT NULL CHECK (security_class IN ('COMMON', 'PREFERRED', 'OTHER', 'UNKNOWN')),
    currency TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS security_identifiers (
    security_identifier_id INTEGER PRIMARY KEY,
    security_id INTEGER NOT NULL REFERENCES securities(security_id),
    identifier_type TEXT NOT NULL CHECK (identifier_type IN ('TICKER', 'ISIN', 'REGISTRATION_NUMBER', 'OTHER')),
    identifier_value TEXT NOT NULL,
    valid_from TEXT,
    valid_to TEXT,
    known_at TEXT NOT NULL,
    snapshot_id INTEGER NOT NULL REFERENCES source_snapshots(snapshot_id),
    CHECK (valid_to IS NULL OR valid_from IS NULL OR valid_to >= valid_from),
    UNIQUE(identifier_type, identifier_value, valid_from, known_at)
);

CREATE TABLE IF NOT EXISTS documents (
    document_id INTEGER PRIMARY KEY,
    snapshot_id INTEGER NOT NULL UNIQUE REFERENCES source_snapshots(snapshot_id),
    issuer_id INTEGER REFERENCES issuers(issuer_id),
    security_id INTEGER REFERENCES securities(security_id),
    document_type TEXT NOT NULL,
    reporting_period_start TEXT,
    reporting_period_end TEXT,
    publication_at TEXT,
    audited INTEGER CHECK (audited IN (0, 1) OR audited IS NULL),
    accounting_standard TEXT CHECK (accounting_standard IN ('IFRS', 'LOCAL', 'OTHER', 'UNKNOWN') OR accounting_standard IS NULL),
    reporting_perimeter TEXT CHECK (reporting_perimeter IN ('CONSOLIDATED', 'STANDALONE', 'UNKNOWN') OR reporting_perimeter IS NULL),
    supersedes_document_id INTEGER REFERENCES documents(document_id),
    CHECK (reporting_period_end IS NULL OR reporting_period_start IS NULL OR reporting_period_end >= reporting_period_start)
);

CREATE TABLE IF NOT EXISTS reported_facts (
    fact_id INTEGER PRIMARY KEY,
    issuer_id INTEGER REFERENCES issuers(issuer_id),
    security_id INTEGER REFERENCES securities(security_id),
    snapshot_id INTEGER NOT NULL REFERENCES source_snapshots(snapshot_id),
    fact_name TEXT NOT NULL,
    value_numeric TEXT,
    value_text TEXT,
    unit TEXT,
    currency TEXT,
    period_start TEXT,
    period_end TEXT,
    valid_at TEXT,
    known_at TEXT NOT NULL,
    value_kind TEXT NOT NULL CHECK (value_kind IN ('REPORTED', 'DERIVED', 'ESTIMATED')),
    confidence TEXT NOT NULL CHECK (confidence IN ('HIGH', 'MEDIUM', 'LOW', 'UNKNOWN')),
    CHECK (issuer_id IS NOT NULL OR security_id IS NOT NULL),
    CHECK (value_numeric IS NOT NULL OR value_text IS NOT NULL),
    CHECK (period_end IS NULL OR period_start IS NULL OR period_end >= period_start)
);

CREATE INDEX IF NOT EXISTS idx_facts_point_in_time
ON reported_facts(fact_name, security_id, issuer_id, known_at, valid_at);

CREATE TABLE IF NOT EXISTS validation_issues (
    issue_id INTEGER PRIMARY KEY,
    issue_type TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('INFO', 'WARNING', 'ERROR', 'CRITICAL')),
    entity_type TEXT NOT NULL,
    entity_id INTEGER,
    detected_at TEXT NOT NULL,
    details TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'OPEN' CHECK (status IN ('OPEN', 'RESOLVED', 'ACCEPTED'))
);
