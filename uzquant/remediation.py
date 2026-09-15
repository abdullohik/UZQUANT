from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path

from .repository import Repository, stable_id, utc_now

PARSER_VERSION = "remediation-a/1.0.0"
TARGETS = ("AGMKP", "KASUP", "IPKY", "UZTL", "QZSM")


@dataclass(frozen=True)
class ShareCapitalEvidence:
    ticker: str
    effective_date: str
    disclosure_date: str
    total_issuer_shares: str | None = None
    class_shares_outstanding: str | None = None
    nominal_value: str | None = None
    currency: str | None = None
    status: str = "UNAVAILABLE"
    reason: str | None = None
    source_url: str | None = None
    provision: str | None = None


# Only source-explicit observations are entered here. KASUP's historical annual
# disclosure reports an issuer-level security count, not a preferred-class count.
SHARE_CAPITAL_EVIDENCE = (
    ShareCapitalEvidence("AGMKP", "2023-12-31", "2024-09-25", status="UNAVAILABLE",
        reason="ANNUAL_DISCLOSURE_DOES_NOT_STATE_VERIFIED_PREFERRED_CLASS_SHARES",
        source_url="https://openinfo.uz/en/reports/jsc/annual/5218"),
    ShareCapitalEvidence("KASUP", "2018-12-31", "2019-07-09", total_issuer_shares="658616940",
        status="PARTIAL", reason="ISSUER_TOTAL_ONLY_NOT_PREFERRED_CLASS_OUTSTANDING",
        source_url="https://openinfo.uz/en/reports/insurance/annual/45",
        provision="Basic information on additionally issued securities: number of securities"),
    ShareCapitalEvidence("IPKY", "2022-12-31", "2023-07-10", status="UNAVAILABLE",
        reason="ANNUAL_DISCLOSURE_DOES_NOT_STATE_VERIFIED_CLASS_SHARES",
        source_url="https://openinfo.uz/en/reports/bank/annual/296"),
    ShareCapitalEvidence("UZTL", "2024-12-31", "2025-07-09", status="UNAVAILABLE",
        reason="ANNUAL_DISCLOSURE_DOES_NOT_STATE_VERIFIED_CLASS_SHARES",
        source_url="https://openinfo.uz/en/reports/jsc/annual/5548"),
    ShareCapitalEvidence("QZSM", "2023-12-31", "2024-07-24", status="UNAVAILABLE",
        reason="ANNUAL_DISCLOSURE_DOES_NOT_STATE_VERIFIED_CLASS_SHARES",
        source_url="https://openinfo.uz/en/reports/jsc/annual/5176"),
)


def _security(repo: Repository, ticker: str):
    return repo.connection.execute(
        "SELECT s.security_id,s.issuer_id FROM securities s JOIN identifier_history h "
        "ON h.security_id=s.security_id WHERE h.identifier_type='TICKER' "
        "AND h.identifier_value=? ORDER BY h.known_at DESC LIMIT 1", (ticker,)).fetchone()


def record_share_capital_evidence(database: Path):
    with Repository(database) as repo:
        repo.initialize()
        loaded = 0
        for item in SHARE_CAPITAL_EVIDENCE:
            security = _security(repo, item.ticker)
            if not security:
                continue
            raw = repo.connection.execute(
                "SELECT raw_document_id FROM financial_documents WHERE source_url=? "
                "ORDER BY retrieved_at DESC LIMIT 1", (item.source_url,)).fetchone()
            observation_id = stable_id("share-capital", f"{security[0]}:{item.effective_date}:{item.source_url}")
            repo.connection.execute(
                "INSERT INTO share_capital_observations VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) "
                "ON CONFLICT(issuer_id,security_id,effective_date,source_url) DO UPDATE SET "
                "total_issuer_shares=excluded.total_issuer_shares,class_shares_outstanding=excluded.class_shares_outstanding,"
                "nominal_value=excluded.nominal_value,currency=excluded.currency,verification_status=excluded.verification_status,"
                "unavailable_reason=excluded.unavailable_reason,source_document_id=excluded.source_document_id,"
                "source_provision=excluded.source_provision,created_at=excluded.created_at",
                (observation_id, security[1], security[0], item.effective_date, item.disclosure_date,
                 item.total_issuer_shares, item.class_shares_outstanding, item.nominal_value, item.currency,
                 item.status, item.reason, raw[0] if raw else None, item.source_url, item.provision,
                 PARSER_VERSION, utc_now()))
            loaded += 1
        repo.connection.commit()
        return {"targets": len(SHARE_CAPITAL_EVIDENCE), "recorded": loaded,
                "verified_class_counts": sum(bool(i.class_shares_outstanding and i.status == "VERIFIED") for i in SHARE_CAPITAL_EVIDENCE)}


def verified_shares_as_of(repo: Repository, security_id: str, as_of: date):
    return repo.connection.execute(
        "SELECT * FROM share_capital_observations WHERE security_id=? AND disclosure_date<=? "
        "AND effective_date<=? AND verification_status='VERIFIED' AND class_shares_outstanding IS NOT NULL "
        "ORDER BY effective_date DESC,disclosure_date DESC LIMIT 1",
        (security_id, as_of.isoformat(), as_of.isoformat())).fetchone()


def record_market_coverage_blocker(database: Path):
    with Repository(database) as repo:
        repo.initialize()
        attempted = utc_now()
        evidence_url = "https://uzse.uz/trade_results?date=02.02.2018"
        audit_id = stable_id("coverage-audit", f"uzse-historical:{attempted[:10]}")
        repo.connection.execute(
            "INSERT OR REPLACE INTO source_coverage_audits VALUES(?,?,?,?,?,?,?,?,?,?)",
            (audit_id, "uzse-public-web", "DATED_TRADE_RESULTS", attempted,
             "Historical dated pages and trading calendar for target securities",
             "Current security-detail rolling window only", "BLOCKED",
             "Official dated endpoint returned HTTP 403 to compliant automated request; no bypass attempted",
             evidence_url, PARSER_VERSION))
        repo.connection.commit()
        return {"status": "BLOCKED", "evidence_url": evidence_url}


def record_preferred_rights_assessments(database: Path):
    evidence = {
        "AGMKP": ("RIGHTS_PARTIAL", "Annual disclosure reports a preferred dividend paid, but no authoritative formula, cumulative, voting, liquidation, redemption, or conversion provisions were retrieved", "https://openinfo.uz/en/reports/jsc/annual/5218", "On Preferred Shares (per share in sum)"),
        "KASUP": ("RIGHTS_PARTIAL", "Annual disclosure reports a preferred dividend paid, but does not establish the complete legal rights of the class", "https://openinfo.uz/en/reports/insurance/annual/45", "On preferred shares (per share in sums)"),
    }
    with Repository(database) as repo:
        repo.initialize(); recorded=0
        for ticker,(classification,reason,url,provision) in evidence.items():
            security=_security(repo,ticker)
            if not security: continue
            raw=repo.connection.execute("SELECT raw_document_id FROM financial_documents WHERE source_url=? ORDER BY retrieved_at DESC LIMIT 1",(url,)).fetchone()
            assessment_id=stable_id("rights-assessment",f"{security[0]}:2026-09-15")
            repo.connection.execute("INSERT INTO security_rights_assessments VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(security_id,as_of_date) DO UPDATE SET classification=excluded.classification,reason=excluded.reason,source_url=excluded.source_url,source_document_id=excluded.source_document_id,source_provision=excluded.source_provision,created_at=excluded.created_at",(assessment_id,security[0],"2026-09-15",classification,reason,url,raw[0] if raw else None,provision,utc_now())); recorded+=1
        repo.connection.commit(); return {"recorded":recorded,"rights_verified":0,"rights_partial":recorded}
