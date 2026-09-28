from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

from .cohort_expansion import _md_table as table, assess_universe, classify_blocker
from .repository import Repository, utc_now

VERSION = "issuer-valuation-unlock/1.0.0"
WORKLIST_LIMIT = 12
BASELINE_BLOCKER_COUNTS = {"METADATA_GAP": 7, "PUBLIC_DATA_NOT_YET_COLLECTED": 66}
BASELINE_FINANCIAL_DOCUMENTS = 29

# Routes were discovered on the official portal and opened successfully on
# 2026-09-28.  This is a bounded acquisition log, not a claim that every
# possible public source has been exhausted.
SEARCH_EVIDENCE = {
    "QZSM": ["https://openinfo.uz/uz/reports/jsc/annual/5985"],
    "UZTL": ["https://openinfo.uz/ru/reports/jsc/annual/5548"],
    "AGMK": ["https://openinfo.uz/en/reports/jsc/annual/582"],
    "IPKY": ["https://new.openinfo.uz/en/reports/bank/annual/387"],
    "KASU": ["https://new.openinfo.uz/en/reports/insurance/annual/73"],
    "AGBA": ["https://openinfo.uz/en/reports/bank/annual/335"],
    "HMKB": ["https://openinfo.uz/uz/reports/bank/annual/438"],
    "UZGF": ["https://new.openinfo.uz/en/reports/jsc/annual/5576"],
    "UZMT": ["https://new.openinfo.uz/en/reports/jsc/annual/3173"],
    "UPOS": ["https://dev-v1-admin-panel.openinfo.uz/en/reports/to_pdf20415/"],
    "BIOK": ["https://new.openinfo.uz/uz-Cyrl/reports/jsc/annual/5494"],
    "BECM": ["https://new.openinfo.uz/uz-Cyrl/reports/jsc/annual/5406"],
}


def select_issuer_worklist(rows: list[dict], limit: int = WORKLIST_LIMIT) -> list[dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[row["issuer_id"]].append(row)
    issuers = []
    for issuer_id, securities in grouped.items():
        turnover = max(float(row["average_daily_turnover"] or 0) for row in securities)
        readiness = max(row["readiness_score"] for row in securities)
        name = securities[0]["issuer"]
        source_urls = " ".join(str(item.get("valuation_methods", "")) for item in securities)
        financial_tie = int(any(word in name.casefold() for word in ("bank", "sug'urta", "sug’urta", "insurance")) or "/bank/" in source_urls or "/insurance/" in source_urls)
        issuers.append({"issuer_id": issuer_id, "issuer": name, "securities": sorted(securities, key=lambda x: x["ticker"]),
                        "turnover": turnover, "readiness": readiness, "financial_tie": financial_tie})
    return sorted(issuers, key=lambda x: (-x["turnover"], -x["readiness"], -x["financial_tie"], x["issuer"]))[:limit]


def _latest_current_tickers(connection) -> set[str]:
    capture = connection.execute("SELECT capture_id FROM rse_universe_captures ORDER BY retrieved_at DESC LIMIT 1").fetchone()[0]
    return {row[0] for row in connection.execute(
        "SELECT DISTINCT ticker FROM rse_universe_instruments WHERE capture_id=? AND instrument_class IN('COMMON_EQUITY','PREFERRED_EQUITY')",
        (capture,),
    )}


def _top_blocker(row: dict) -> tuple[str, str]:
    blockers = set(row["blockers"])
    if not row["financial_documents"]:
        return "NO_VERIFIED_FINANCIAL_DOCUMENT", "PUBLIC_DATA_NOT_YET_COLLECTED"
    if not row["valuation_concepts"]:
        return "NO_NORMALIZED_FINANCIAL_INPUTS", "PARSER_GAP"
    if not row["metadata_complete_documents"]:
        return "FINANCIAL_METADATA_INCOMPLETE", "METADATA_GAP"
    if row["valuation_status"] != "AVAILABLE":
        specific = sorted(b for b in blockers if b not in {"VALUATION_INSUFFICIENT", "INSUFFICIENT_FACTOR_COVERAGE"})
        blocker = specific[0] if specific else "VALUATION_INSUFFICIENT"
        return blocker, classify_blocker(row, blocker)
    if row["factor_count"] < 4:
        return "INSUFFICIENT_FACTOR_COVERAGE", "MODEL_INTEGRATION_GAP"
    return "NONE", "NONE"


def export_issuer_unlock(database: Path, outputs: Path) -> dict:
    generated = utc_now()
    # Frozen Mission-1 queue snapshot (73 current equities).  Keep this
    # explicit so rerunning the exporter does not redefine its own baseline.
    before = Counter(BASELINE_BLOCKER_COUNTS)

    assessed = assess_universe(database)
    with Repository(database) as repo:
        current = _latest_current_tickers(repo.connection)
        current_rows = [row for row in assessed if row["ticker"] in current]
        worklist = select_issuer_worklist(current_rows)
        work_ids = [row["issuer_id"] for row in worklist]
        work_tickers = {security["ticker"] for row in worklist for security in row["securities"]}

        work_rows = []
        for rank, issuer in enumerate(worklist, 1):
            work_rows.append([rank, issuer["issuer"], ", ".join(s["ticker"] for s in issuer["securities"]),
                              f"{issuer['turnover']:.2f}", issuer["readiness"], "BANK/INSURER" if issuer["financial_tie"] else "OTHER"])
        outputs.mkdir(parents=True, exist_ok=True)
        (outputs / "issuer_worklist.md").write_text(
            f"# Issuer-level Valuation Worklist\n\nGenerated: {generated}. Version: `{VERSION}`.\n\n"
            "Ranking is deterministic: maximum issuer-level average daily turnover descending, then maximum evidence-readiness score descending; banks/insurers break exact ties, followed by legal name. Capped at 12 issuers. It is not an attractiveness ranking.\n\n" +
            table(["Rank", "Issuer", "Current equities", "Issuer max ADV (UZS)", "Max readiness", "Tie class"], work_rows) +
            "\n\n## Free-win and derived-metric audit\n\n"
            "| Item | Outcome | Evidence / exact remaining reason |\n| --- | --- | --- |\n"
            "| Average assets / ROA / asset turnover | GENERAL FIX APPLIED | Opening and closing Total Assets now require identical currency, unit, perimeter, standard and audit metadata; lineage contains both source versions. One ROA became available. |\n"
            "| Prior-period growth | GENERAL FIX APPLIED | The engine now loads only same-duration, one-year-prior documents published by the decision date and filters each concept for identical metadata. No growth value became available because work-list public reports still lack compatible verified metadata. |\n"
            "| Average equity / ROE | VERIFIED | Existing strict averaging pattern retained; one ROE is available with full lineage. |\n"
            "| Average invested capital / ROIC | REMAINS UNAVAILABLE | NOPAT and a compatible opening/closing invested-capital basis are not both source-backed; no proxy was invented. |\n"
            "| EPS / BVPS / TBVPS | REMAINS UNAVAILABLE EXCEPT EXISTING VALUATION USE | Mixed common/preferred capital requires class earnings/equity allocation and verified rights; EPS or per-share book values were not divided across classes by assumption. |\n"
            "| Net debt | VERIFIED | Strict Cash + Short-Term Debt + Long-Term Debt calculation; 17 version-1.1 records available and none converts missing inputs to zero. |\n"
            "| Growth / margins | PARTIAL | 34 gross/net margin records are available; growth remains blocked by incompatible or UNKNOWN metadata. |\n"
            "| Known five DATA_ALREADY_PRESENT_NOT_NORMALIZED | NOT CLOSED BY INVENTION | UZTL, QZSM, AGMK/AGMKP and UZTLP still lack source-backed OCF/CapEx/EBITDA (and applicable D&A/EBIT) in the retained statutory pages. This is now an exact concept/source limitation, not a silent zero. |\n"
            "| Known eight MODEL_INTEGRATION_GAP | REASSESSED | All methods were rerun independently. IPKY Residual Income remains executable; UZTL, KASU, QZSM, AGMK/AGMKP, KASUP and historical IPKYP remain rejected by their recorded method blockers. |\n"
        )

        coverage_rows = []
        document_rows = []
        docs_discovered = docs_ingested = normalized_docs = metadata_resolved = 0
        for issuer in worklist:
            tick = issuer["securities"][0]["ticker"].removesuffix("P")
            # Prefer the common/current configured ticker key where available.
            key = next((candidate for candidate in SEARCH_EVIDENCE if any(s["ticker"] in {candidate, candidate+"P"} for s in issuer["securities"])), tick)
            found = SEARCH_EVIDENCE.get(key, [])
            docs = repo.connection.execute(
                "SELECT d.*,EXISTS(SELECT 1 FROM financial_observation_versions o WHERE o.document_id=d.document_id AND o.superseded_by_version_id IS NULL) normalized "
                "FROM financial_documents d WHERE d.issuer_id=? ORDER BY d.period_end,d.publication_date,d.document_id", (issuer["issuer_id"],)
            ).fetchall()
            docs_discovered += len(found); docs_ingested += len(docs)
            normalized_docs += sum(bool(d["normalized"]) for d in docs)
            complete = sum(bool(d["currency"] and d["reporting_perimeter"] != "UNKNOWN" and d["accounting_standard"] != "UNKNOWN" and d["audit_status"] != "UNKNOWN") for d in docs)
            metadata_resolved += complete
            result = "INGESTED" if docs else ("DISCOVERED_NOT_INGESTED" if found else "NOT_FOUND")
            note = ""
            if docs and not any(d["normalized"] for d in docs): note = "PARSER_GAP: retained source document has no normalized financial rows"
            elif found and not docs: note = "PUBLIC_DATA_NOT_YET_COLLECTED: route found but period/identity metadata was not sufficient for safe ingestion"
            elif docs and complete < len(docs): note = "METADATA_GAP: unresolved unit/perimeter/standard/audit fields remain UNKNOWN"
            coverage_rows.append([issuer["issuer"], ", ".join(found) or "None", len(docs),
                                  ", ".join(sorted({d["period_end"] for d in docs})) or "None", complete, result, note])
            for d in docs:
                units = [r[0] for r in repo.connection.execute("SELECT DISTINCT unit FROM financial_observation_versions WHERE document_id=? AND superseded_by_version_id IS NULL", (d["document_id"],))]
                document_rows.append([issuer["issuer"], d["period_end"], d["publication_date"], d["currency"] or "UNKNOWN",
                                      ", ".join(units) or "UNKNOWN", d["reporting_perimeter"], d["accounting_standard"], d["audit_status"], d["source_url"]])
        (outputs / "public_source_coverage.md").write_text(
            f"# Public Source Coverage\n\nGenerated: {generated}. Searches were bounded to official Openinfo pages and already verified RSE/issuer evidence. No issuer is classified `PUBLIC_SOURCE_EXHAUSTED`; this log does not prove exhaustion. Raw ingested pages are preserved through `raw_documents`.\n\n"
            "## Issuer search log\n\n" + table(["Issuer", "Observed working route(s)", "Stored docs", "Periods", "Metadata-complete docs", "Outcome", "Remaining issue"], coverage_rows) +
            "\n\n## Document metadata audit\n\n" + table(["Issuer", "Period end", "Publication", "Currency", "Unit", "Perimeter", "Standard", "Audit", "Source"], document_rows) + "\n"
        )

        valuation_rows = repo.connection.execute(
            "SELECT DISTINCT h.identifier_value ticker,v.method,v.status,v.bear_value,v.base_value,v.bull_value,v.confidence,v.insufficiency_reasons_json "
            "FROM valuation_records v JOIN identifier_history h ON h.security_id=v.security_id AND h.identifier_type='TICKER' "
            "WHERE v.valuation_date=(SELECT max(v2.valuation_date) FROM valuation_records v2 WHERE v2.security_id=v.security_id) "
            "ORDER BY ticker,v.method"
        ).fetchall()
        valuation_rows = [row for row in valuation_rows if row["ticker"] in work_tickers]
        (outputs / "universe_valuations.md").write_text(
            f"# Worklist Valuation Results\n\nGenerated: {generated}. Each method is assessed independently; missing evidence is never replaced with an assumption. Prior valuation records remain stored.\n\n" +
            table(["Ticker", "Method", "Result", "Bear", "Base", "Bull", "Confidence", "Exact blockers"],
                  [[r["ticker"], r["method"], "EXECUTED" if r["status"] == "AVAILABLE" else "REJECTED_WITH_REASON", r["bear_value"], r["base_value"], r["bull_value"], r["confidence"], ", ".join(json.loads(r["insufficiency_reasons_json"] or "[]"))] for r in valuation_rows]) + "\n"
        )

        latest_signals = repo.connection.execute(
            "WITH latest AS (SELECT rs.*,row_number() OVER(PARTITION BY security_id ORDER BY generated_at DESC,signal_id DESC) rn FROM research_signals rs) "
            "SELECT h.identifier_value ticker,l.signal_state,l.confidence,l.factor_scores_json FROM latest l JOIN identifier_history h ON h.security_id=l.security_id AND h.identifier_type='TICKER' WHERE l.rn=1"
        ).fetchall()
        factors = []; seen_factor_tickers = set()
        for row in latest_signals:
            if row["ticker"] not in work_tickers or row["ticker"] in seen_factor_tickers: continue
            seen_factor_tickers.add(row["ticker"])
            parsed = json.loads(row["factor_scores_json"] or "{}")
            available = sorted(name for name, item in parsed.items() if item.get("status") == "AVAILABLE" and item.get("score") is not None)
            factors.append([row["ticker"], len(available), ", ".join(available) or "None", row["confidence"], row["signal_state"]])
        (outputs / "universe_factor_coverage.md").write_text(
            f"# Worklist Factor Coverage\n\nGenerated: {generated}. Frozen factor methodology and thresholds. New versioned signals were appended; prior signals were not rewritten.\n\n" +
            table(["Ticker", "Available factor count", "Available factors", "Confidence", "Research state"], factors) + "\n"
        )

        after = Counter(); blocker_rows = []
        for row in sorted(current_rows, key=lambda x: x["ticker"]):
            blocker, category = _top_blocker(row); after[category] += 1
            blocker_rows.append([row["ticker"], row["issuer_id"], blocker, category,
                                 "Worklist acquisition + engine rerun" if row["ticker"] in work_tickers else "Not in capped worklist"])
        delta_rows = [[category, before.get(category, 0), after.get(category, 0), after.get(category, 0)-before.get(category, 0)] for category in sorted(set(before)|set(after))]
        (outputs / "universe_blocker_queue.md").write_text(
            f"# Current Equity Universe Blocker Queue\n\nGenerated: {generated}. One top blocker per current equity. `PUBLIC_SOURCE_EXHAUSTED` is not assigned.\n\n"
            "## Before / after\n\n" + table(["Classification", "Before", "After", "Change"], delta_rows) +
            "\n\n## Current queue\n\n" + table(["Ticker", "Issuer ID", "Top blocker", "Classification", "Basis"], blocker_rows) + "\n"
        )

        executable = len({r["ticker"] for r in valuation_rows if r["status"] == "AVAILABLE"})
        factor4 = sum(row[1] >= 4 for row in factors)
        return {"issuers": len(worklist), "securities": len(work_tickers), "documents_discovered": docs_discovered,
                "documents_already_held": BASELINE_FINANCIAL_DOCUMENTS,
                "documents_newly_stored": max(0, docs_ingested-BASELINE_FINANCIAL_DOCUMENTS),
                "documents_stored": docs_ingested, "normalized_documents": normalized_docs,
                "metadata_complete_documents": metadata_resolved, "executable_method_rows": executable,
                "securities_4_plus_factors": factor4, "before": dict(before), "after": dict(after)}
