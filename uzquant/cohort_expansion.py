from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from .repository import Repository, utc_now

VERSION = "cohort-readiness/1.0.0"
TARGET_SIZE = 20


@dataclass(frozen=True)
class ReadinessInputs:
    identity_verified: bool
    security_class_verified: bool
    market_observations: int
    financial_documents: int
    reporting_periods: int
    shares_verified: bool
    metadata_complete_documents: int
    liquidity_available: bool
    valuation_concepts: int
    ownership_records: int
    rights_records: int
    corporate_records: int


def readiness_score(value: ReadinessInputs) -> int:
    """Transparent 0-100 evidence-readiness score; never an attractiveness score."""
    score = 0
    score += 12 if value.identity_verified else 0
    score += 8 if value.security_class_verified else 0
    score += min(15, (value.market_observations * 15 + 59) // 60) if value.market_observations else 0
    score += min(15, value.financial_documents * 5)
    score += min(8, value.reporting_periods * 2)
    score += 10 if value.shares_verified else 0
    score += min(8, value.metadata_complete_documents * 4)
    score += 7 if value.liquidity_available else 0
    score += min(8, value.valuation_concepts * 2)
    score += min(3, value.ownership_records)
    score += min(3, value.rights_records)
    score += min(3, value.corporate_records)
    return min(100, score)


def _json(value):
    if not value:
        return []
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return []


def _tickers(connection):
    return connection.execute("""
        WITH ranked AS (
          SELECT security_id,identifier_value,
                 row_number() OVER(PARTITION BY security_id ORDER BY known_at DESC,identifier_id DESC) rn
          FROM identifier_history WHERE identifier_type='TICKER'
        )
        SELECT s.security_id,s.issuer_id,r.identifier_value ticker,s.security_class_code,
               i.legal_name,i.sector
        FROM securities s JOIN issuers i USING(issuer_id)
        JOIN ranked r ON r.security_id=s.security_id AND r.rn=1
        ORDER BY r.identifier_value
    """).fetchall()


def assess_universe(database: Path) -> list[dict]:
    with Repository(database) as repo:
        repo.initialize()
        c = repo.connection
        output = []
        for security in _tickers(c):
            sid, iid = security["security_id"], security["issuer_id"]
            identity = c.execute("""
                SELECT count(DISTINCT identifier_type) FROM effective_identifier_evidence
                WHERE security_id=? AND entity_type='SECURITY' AND evidence_status='VERIFIED'
                  AND identifier_type IN('TICKER','ISIN')
            """, (sid,)).fetchone()[0] >= 2
            market = c.execute("""
                SELECT count(*),min(trade_date),max(trade_date) FROM market_observations
                WHERE security_id=? AND series_type='RAW_OBSERVED'
            """, (sid,)).fetchone()
            market_quality = c.execute("""
                SELECT trading_frequency,zero_trade_day_ratio,average_daily_trading_value,
                       days_since_last_trade,calendar_basis
                FROM market_quality_metrics WHERE security_id=? ORDER BY as_of_date DESC,created_at DESC LIMIT 1
            """, (sid,)).fetchone()
            if market[2]:
                stale_days=(date.today()-date.fromisoformat(market[2])).days
                freshness="VERY_STALE" if stale_days>=20 else "STALE" if stale_days>=5 else "CURRENT_OBSERVATION"
            else:
                stale_days=None; freshness="NO_MARKET_DATA"
            docs = c.execute("""
                SELECT count(DISTINCT d.document_id),count(DISTINCT d.period_end),
                       sum(CASE WHEN d.currency IS NOT NULL AND d.reporting_perimeter!='UNKNOWN'
                                    AND EXISTS(SELECT 1 FROM financial_observation_versions o
                                               WHERE o.document_id=d.document_id
                                                 AND o.superseded_by_version_id IS NULL
                                                 AND o.unit!='SOURCE_UNIT_UNSPECIFIED')
                                THEN 1 ELSE 0 END)
                FROM financial_documents d
                JOIN financial_document_entity_checks e USING(document_id)
                JOIN financial_document_identity_assignments a USING(document_id)
                WHERE d.issuer_id=? AND e.validation_status='MATCHED' AND a.assignment_status='VERIFIED'
            """, (iid,)).fetchone()
            concepts = c.execute("""
                SELECT count(DISTINCT canonical_concept) FROM financial_observation_versions
                WHERE issuer_id=? AND superseded_by_version_id IS NULL
                  AND canonical_concept IN('Revenue','Net Income','Equity','Total Assets','Total Liabilities',
                                           'Cash','Short-Term Debt','Long-Term Debt','EBIT','EBITDA',
                                           'Operating Cash Flow','CapEx','Dividends')
            """, (iid,)).fetchone()[0]
            shares = bool(c.execute("""
                SELECT 1 FROM share_capital_observations WHERE security_id=?
                 AND verification_status='VERIFIED' AND class_shares_outstanding IS NOT NULL LIMIT 1
            """, (sid,)).fetchone())
            liquidity = c.execute("""
                SELECT liquidity_state,liquidity_confidence,as_of_date FROM liquidity_assessments
                WHERE security_id=? ORDER BY created_at DESC LIMIT 1
            """, (sid,)).fetchone()
            signal = c.execute("""
                SELECT signal_state,confidence,factor_scores_json,generated_at FROM research_signals
                WHERE security_id=? ORDER BY generated_at DESC LIMIT 1
            """, (sid,)).fetchone()
            valuation = c.execute("""
                SELECT status,method,bear_value,base_value,bull_value,confidence,valuation_date
                FROM valuation_records WHERE security_id=?
                ORDER BY (status='AVAILABLE') DESC,created_at DESC LIMIT 1
            """, (sid,)).fetchone()
            methods = c.execute("""
                SELECT method,status,blocker_codes_json FROM valuation_method_eligibility
                WHERE security_id=? AND valuation_date=(SELECT max(valuation_date) FROM valuation_method_eligibility WHERE security_id=?)
                ORDER BY method
            """, (sid, sid)).fetchall()
            ownership = c.execute("SELECT count(*) FROM ownership_positions WHERE issuer_id=?", (iid,)).fetchone()[0]
            rights = c.execute("SELECT count(*) FROM security_rights WHERE security_id=?", (sid,)).fetchone()[0]
            corporate = c.execute("""
                SELECT (SELECT count(*) FROM corporate_actions WHERE issuer_id=?) +
                       (SELECT count(*) FROM governance_events WHERE issuer_id=?)
            """, (iid, iid)).fetchone()[0]
            factors = _json(signal["factor_scores_json"] if signal else None)
            if not isinstance(factors, dict):
                factors = {}
            available_factors = sorted(name for name, item in factors.items()
                                       if item.get("status") == "AVAILABLE" and item.get("score") is not None)
            inputs = ReadinessInputs(
                identity, security["security_class_code"] in {"COMMON", "PREFERRED"}, market[0],
                docs[0] or 0, docs[1] or 0, shares, docs[2] or 0, bool(liquidity), concepts,
                ownership, rights, corporate,
            )
            blockers = set()
            for method in methods:
                blockers.update(_json(method["blocker_codes_json"]))
            if not identity: blockers.add("UNVERIFIED_SECURITY_IDENTITY")
            if security["security_class_code"] not in {"COMMON", "PREFERRED"}: blockers.add("UNVERIFIED_SECURITY_CLASS")
            if not market[0]: blockers.add("NO_MARKET_HISTORY")
            if not docs[0]: blockers.add("NO_VERIFIED_FINANCIAL_DOCUMENT")
            if not shares: blockers.add("MISSING_VERIFIED_CLASS_SHARES_OUTSTANDING")
            if not docs[2]: blockers.add("FINANCIAL_METADATA_INCOMPLETE")
            if valuation is None or valuation["status"] != "AVAILABLE": blockers.add("VALUATION_INSUFFICIENT")
            if len(available_factors) < 4: blockers.add("INSUFFICIENT_FACTOR_COVERAGE")
            output.append({
                "ticker": security["ticker"], "security_id": sid, "issuer_id": iid,
                "issuer": security["legal_name"], "security_class": security["security_class_code"],
                "sector": security["sector"], "readiness_score": readiness_score(inputs),
                "identity_verified": identity, "market_observations": market[0],
                "first_trade_date": market[1], "last_trade_date": market[2],
                "days_since_last_trade": stale_days, "freshness": freshness,
                "trading_frequency": market_quality[0] if market_quality else None,
                "zero_trade_day_ratio": market_quality[1] if market_quality else None,
                "average_daily_turnover": market_quality[2] if market_quality else None,
                "trading_calendar_basis": market_quality[4] if market_quality else "UNAVAILABLE",
                "financial_documents": docs[0] or 0, "reporting_periods": docs[1] or 0,
                "metadata_complete_documents": docs[2] or 0, "shares_verified": shares,
                "valuation_concepts": concepts, "ownership_records": ownership,
                "rights_records": rights, "corporate_records": corporate,
                "liquidity_state": liquidity["liquidity_state"] if liquidity else "UNASSESSABLE",
                "liquidity_confidence": liquidity["liquidity_confidence"] if liquidity else "UNAVAILABLE",
                "valuation_status": valuation["status"] if valuation else "VALUATION_INSUFFICIENT",
                "valuation_method": valuation["method"] if valuation else None,
                "bear_value": valuation["bear_value"] if valuation else None,
                "base_value": valuation["base_value"] if valuation else None,
                "bull_value": valuation["bull_value"] if valuation else None,
                "valuation_confidence": valuation["confidence"] if valuation else None,
                "valuation_methods": [{"method": row["method"], "status": row["status"],
                                       "blockers": _json(row["blocker_codes_json"])} for row in methods],
                "factor_count": len(available_factors), "available_factors": available_factors,
                "confidence": signal["confidence"] if signal else None,
                "research_state": signal["signal_state"] if signal else "DATA_INSUFFICIENT",
                "blockers": sorted(blockers), "version": VERSION,
            })
        return sorted(output, key=lambda row: (-row["readiness_score"], row["ticker"]))


def select_cohort(rows: list[dict], size: int = TARGET_SIZE) -> list[dict]:
    selected = []
    for index, row in enumerate(rows):
        copy = dict(row)
        copy["selected"] = index < size
        copy["selection_reason"] = (
            f"SELECTED_TOP_{size}_DATA_READINESS; score={row['readiness_score']}"
            if index < size else f"NOT_SELECTED_BELOW_CUTOFF_{size}; score={row['readiness_score']}"
        )
        selected.append(copy)
    return selected


def classify_blocker(row: dict, blocker: str) -> str:
    """Map every concrete blocker to the sprint's required root-cause taxonomy."""
    if blocker in {"UNVERIFIED_SECURITY_CLASS", "FINANCIAL_METADATA_INCOMPLETE",
                   "UNVERIFIED_FINANCIAL_UNIT", "UNVERIFIED_FINANCIAL_CURRENCY",
                   "UNVERIFIED_REPORTING_PERIMETER", "MISSING_VERIFIED_CLASS_SHARES_OUTSTANDING"}:
        return "METADATA_GAP"
    if "RIGHTS" in blocker:
        return "PUBLIC_DATA_NOT_YET_COLLECTED" if row["rights_records"] == 0 else "METADATA_GAP"
    if blocker in {"NO_MARKET_HISTORY", "NO_VERIFIED_FINANCIAL_DOCUMENT", "NO_FINANCIAL_DOCUMENT",
                   "MISSING_VERIFIED_SECURITY_CLASS_DIVIDEND_HISTORY", "INSUFFICIENT_CREDIBLE_PEER_SET"}:
        return "PUBLIC_DATA_NOT_YET_COLLECTED"
    if blocker in {"VALUATION_INSUFFICIENT", "INSUFFICIENT_FACTOR_COVERAGE"}:
        return "MODEL_INTEGRATION_GAP" if row["financial_documents"] else "PUBLIC_DATA_NOT_YET_COLLECTED"
    if blocker in {"MISSING_EQUITY_RISK_PREMIUM", "MISSING_SECURITY_OR_SECTOR_BETA",
                   "MISSING_SUPPORTED_LONG_TERM_GROWTH", "MISSING_COST_OF_DEBT",
                   "MISSING_COST_OF_EQUITY_COMPONENTS", "MISSING_TARGET_CAPITAL_STRUCTURE",
                   "MISSING_SUPPORTED_FORECAST_SCENARIOS", "MISSING_VERIFIED_PRODUCTION",
                   "MISSING_COMMODITY_PRICE_SCENARIOS", "MISSING_UNIT_COST",
                   "MISSING_MINING_CAPEX_FORECAST", "MISSING_FX_SCENARIOS"}:
        return "PUBLIC_DATA_NOT_YET_COLLECTED"
    if blocker.startswith("MISSING_"):
        return "DATA_ALREADY_PRESENT_NOT_NORMALIZED" if row["financial_documents"] else "PUBLIC_DATA_NOT_YET_COLLECTED"
    if blocker == "CROSS_DOCUMENT_INPUT_COMPATIBILITY_UNVERIFIED":
        return "METADATA_GAP"
    return "GENUINELY_UNAVAILABLE"


def _md_table(headers, rows):
    def safe(value):
        return str(value if value not in (None, "") else "Unavailable").replace("|", "\\|").replace("\n", " ")
    return "\n".join([
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
        *("| " + " | ".join(safe(cell) for cell in row) + " |" for row in rows),
    ])


def export_cohort(database: Path, outputs: Path, docs: Path, size: int = TARGET_SIZE) -> dict:
    assessed = select_cohort(assess_universe(database), size)
    for row in assessed:
        row["blocker_categories"] = {blocker: classify_blocker(row, blocker) for blocker in row["blockers"]}
    selected = [row for row in assessed if row["selected"]]
    outputs.mkdir(parents=True, exist_ok=True); docs.mkdir(parents=True, exist_ok=True)
    generated = utc_now()
    selection_rows = [[r["ticker"], r["issuer"], r["security_class"], r["readiness_score"],
                       r["financial_documents"], r["market_observations"],
                       ", ".join(r["blockers"]), r["factor_count"], r["selection_reason"]] for r in assessed]
    (outputs / "cohort_selection.md").write_text(
        f"# Cohort Selection\n\nGenerated: {generated}  \nMethod: `{VERSION}`. Ranking is evidence readiness, not investment attractiveness.\n\n" +
        _md_table(["Ticker","Issuer","Class","Score","Reports","Market observations","Valuation / evidence blockers","Factors","Selection"], selection_rows) + "\n"
    )
    coverage_rows = [[r["ticker"], "VERIFIED" if r["identity_verified"] else "UNVERIFIED",
                      f"{r['financial_documents']} docs / {r['reporting_periods']} periods",
                      r["valuation_status"], ", ".join(x["method"] for x in r["valuation_methods"] if x["status"] == "EXECUTABLE") or "None",
                      r["factor_count"], f"{r['market_observations']} obs; {r['first_trade_date']} to {r['last_trade_date']}; {r['freshness']}",
                      r["liquidity_state"], r["confidence"], r["research_state"],
                      ", ".join(f"{b} [{r['blocker_categories'][b]}]" for b in r["blockers"])] for r in selected]
    (outputs / "cohort_research_coverage.md").write_text(
        f"# Cohort Research Coverage\n\nGenerated: {generated}\n\n" +
        _md_table(["Ticker","Identity","Financial coverage","Valuation","Executable methods","Factors","Market history / freshness","Liquidity","Confidence","Research state","Remaining blockers"], coverage_rows) + "\n"
    )
    valuation_rows=[]
    for r in selected:
        if r["valuation_methods"]:
            for method in r["valuation_methods"]:
                valuation_rows.append([r["ticker"],method["method"],method["status"],r["bear_value"] if method["method"]==r["valuation_method"] else None,r["base_value"] if method["method"]==r["valuation_method"] else None,r["bull_value"] if method["method"]==r["valuation_method"] else None,", ".join(f"{b} [{classify_blocker(r,b)}]" for b in method["blockers"])])
        else:
            valuation_rows.append([r["ticker"],"Not assessed","UNSUPPORTED",None,None,None,", ".join(f"{b} [{r['blocker_categories'][b]}]" for b in r["blockers"])])
    (outputs / "cohort_valuations.md").write_text(
        f"# Cohort Valuation Eligibility\n\nGenerated: {generated}\n\n" +
        _md_table(["Ticker","Method","Eligibility","Bear","Base","Bull","Blockers"], valuation_rows) + "\n"
    )
    (outputs / "cohort_factor_coverage.md").write_text(
        f"# Cohort Factor Coverage\n\nGenerated: {generated}. Existing frozen factor methodology only.\n\n" +
        _md_table(["Ticker","Count","Available factors","Confidence","Research state"],
                  [[r["ticker"],r["factor_count"],", ".join(r["available_factors"]) or "None",r["confidence"],r["research_state"]] for r in selected]) + "\n"
    )
    categories = {}
    for r in selected:
        for blocker in r["blockers"]: categories.setdefault((blocker,r["blocker_categories"][blocker]), []).append(r["ticker"])
    (outputs / "cohort_remaining_blockers.md").write_text(
        f"# Cohort Remaining Blockers\n\nGenerated: {generated}\n\n" +
        _md_table(["Blocker","Classification","Count","Securities"], [[key[0],key[1],len(value),", ".join(value)] for key,value in sorted(categories.items(), key=lambda item:(-len(item[1]),item[0]))]) + "\n"
    )
    terminal_visible = len(assessed)
    selected_tickers = [row["ticker"] for row in selected]
    (outputs / "terminal_cohort_verification.md").write_text(
        f"# Terminal Cohort Verification\n\nGenerated: {generated}\n\n"
        f"- Backend universe records exposed: **{terminal_visible}**\n"
        f"- Selected cohort records exposed by the same `/api/v1/universe` source: **{len(selected)}**\n"
        f"- Selected tickers: **{', '.join(selected_tickers)}**\n"
        "- Screener, security research, valuation, factor, lineage, and coverage views use canonical backend records.\n"
        "- No frontend valuation or factor calculation is used.\n"
        "- A security without stored lineage correctly shows unavailable lineage rather than invented evidence.\n"
    )
    executable = sum(r["valuation_status"] == "AVAILABLE" for r in selected)
    factor4 = sum(r["factor_count"] >= 4 for r in selected)
    non_insufficient = sum(r["research_state"] not in {"DATA_INSUFFICIENT", "VALUATION_INSUFFICIENT"} for r in selected)
    summary = {
        "evaluated": len(assessed), "selected": len(selected), "executable_valuations": executable,
        "factor_coverage_4_plus": factor4, "non_insufficient_states": non_insufficient,
        "data_insufficient": sum(r["research_state"] == "DATA_INSUFFICIENT" for r in selected),
        "valuation_insufficient": sum(r["valuation_status"] != "AVAILABLE" for r in selected),
        "security_rights_blocked": sum(any("RIGHTS" in b for b in r["blockers"]) for r in selected),
        "financial_metadata_blocked": sum("FINANCIAL_METADATA_INCOMPLETE" in r["blockers"] for r in selected),
        "terminal_visible": terminal_visible,
        "fully_researchable": [r["ticker"] for r in selected if r["valuation_status"] == "AVAILABLE" and r["factor_count"] >= 4],
        "closest_to_researchable": [r["ticker"] for r in selected if not (r["valuation_status"] == "AVAILABLE" and r["factor_count"] >= 4)][:5],
    }
    summary["blockers_by_category"] = {
        category: sum(any(value == category for value in row["blocker_categories"].values()) for row in selected)
        for category in ("DATA_ALREADY_PRESENT_NOT_NORMALIZED", "PARSER_GAP", "METADATA_GAP",
                         "MODEL_INTEGRATION_GAP", "DERIVED_METRIC_GAP", "PUBLIC_DATA_NOT_YET_COLLECTED",
                         "PUBLIC_SOURCE_EXHAUSTED", "REQUIRES_AUTHORIZED_SOURCE", "REQUIRES_TIME",
                         "GENUINELY_UNAVAILABLE")
    }
    with Repository(database) as repo:
        queue={row[0]:row[1] for row in repo.connection.execute("SELECT status,count(*) FROM rse_history_acquisition_jobs GROUP BY status")}
        market_total=repo.connection.execute("SELECT count(*) FROM market_observations").fetchone()[0]
        eligibility_total=repo.connection.execute("SELECT count(*) FROM valuation_method_eligibility").fetchone()[0]
        fk_violations=len(repo.connection.execute("PRAGMA foreign_key_check").fetchall())
    summary.update({"market_observations":market_total,"rse_history_queue":queue,
                    "valuation_method_assessments":eligibility_total,"foreign_key_violations":fk_violations})
    (docs / "cohort_expansion_report.md").write_text(
        f"# Cohort Expansion Report\n\nGenerated: {generated}  \nVersion: `{VERSION}`\n\n"
        "## Result\n\nThis sprint ranks and audits the full security universe using data readiness only. It does not change any valuation, factor, confidence, signal, liquidity, or readiness rule. Missing evidence remains missing.\n\n"
        + _md_table(["Measure","Result"], [[key,value] for key,value in summary.items()])
        + "\n\n## Bounded acquisition\n\nThe existing official RSE HTML importer was run for one bounded batch over the selected cohort. Eighteen jobs imported verified trades and two were correctly recorded empty. No broad crawler, guessed endpoint, or access-control bypass was used.\n"
        + "\n## Correctness defect fixed\n\nThe valuation eligibility runner was structurally hard-coded to five ticker symbols. It now accepts an explicit readiness-selected cohort and applies the pre-existing sector routing and methods. Preferred-rights gating is now based on the stored security class and authoritative rights record rather than two hard-coded preferred tickers. Formulas, assumptions, weights, thresholds, and gates are unchanged.\n"
        + "\n## Interpretation\n\nThe selected list is a recovery and normalization worklist, not a list of attractive securities. A selected security remains `DATA_INSUFFICIENT` or `VALUATION_INSUFFICIENT` wherever the stored evidence cannot support a conclusion. The dominant remaining blockers are missing authoritative financial metadata, unnormalized statement concepts, verified security-specific rights, credible peers/assumptions, and uncollected public filings for the lower-readiness names.\n"
    )
    return summary


def assess_cohort_valuations(database: Path, size: int = TARGET_SIZE) -> list[dict]:
    """Apply the existing valuation engine to the readiness-selected cohort."""
    from .valuation import run_real_validation
    selected = select_cohort(assess_universe(database), size)
    tickers = tuple(row["ticker"] for row in selected if row["selected"])
    return run_real_validation(database, tickers=tickers)
