from __future__ import annotations

import hashlib
import io
import json
import re
import uuid
import urllib.parse
from datetime import date
from decimal import Decimal
from pathlib import Path

from .config import Settings
from .financial_lineage import append_version
from .identity import RESOLVED, resolve_security_pair
from .repository import Repository, stable_id, utc_now
from .rse import fetch
from .valuation import residual_income, run_real_validation, MODEL_VERSION

PARSER_VERSION = "audited-pdf-evidence/1.1.0"
ASSUMPTION_VERSION = "ipky-residual-income/1.1.0"
SOURCE_ID = "openinfo-audited-financial-pdf"
IPKY_2023_URL = "https://openinfo.uz/media/audit_conclusion/Аудиторское_заключение_МСФО_2023_DxdUBfo.pdf"
DAMODARAN_COUNTRY_URL = "https://pages.stern.nyu.edu/adamodar/New_Home_Page/datafile/ctryprem.html"
DAMODARAN_BETA_URL = "https://pages.stern.nyu.edu/adamodar/New_Home_Page/datafile/BetasGlobal.html"
CBU_TARGET_URL = "https://cbu.uz/en/monetary-policy/concept/"

LINE_PATTERNS = {
    "Total Assets": (r"ИТОГО АКТИВЫ", 3),
    "Total Liabilities": (r"ИТОГО ОБЯЗАТЕЛЬСТВА(?! И)", 3),
    "Equity": (r"ИТОГО КАПИТАЛ", 3),
    "Net Income": (r"Чистая прибыль за период", 2),
    "Intangibles": (r"Нематериальные активы", 2),
}


def extract_ipky_2023_pdf(payload: bytes) -> dict:
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(payload))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    if "Ипак Йули" not in text:
        raise ValueError("audited PDF entity does not identify Ipak Yuli")
    if not re.search(r"Международными\s+стандартами\s+финансовой\s+отчетности", text, re.I):
        raise ValueError("IFRS assertion not found")
    perimeter_evidence = re.search(r"консолидированн\w*\s+финансов\w*\s+отчетност\w*", text, re.I)
    if not perimeter_evidence:
        raise ValueError("explicit consolidated-report wording not found")
    if not re.search(r"\(в\s+миллионах\s+узбекских\s+сумов\)", text, re.I):
        raise ValueError("million UZS unit header not found")
    values: dict[str, tuple[Decimal, Decimal, str]] = {}
    for concept, (label, digit_groups) in LINE_PATTERNS.items():
        match = re.search(rf"^\s*({label})[^\n]*$", text, re.I | re.M)
        if not match:
            raise ValueError(f"required audited line not found: {concept}")
        numeric_tokens = re.findall(r"(?<!\d)\d{1,3}(?!\d)", match.group(0))
        if len(numeric_tokens) < digit_groups * 2:
            raise ValueError(f"two-period values not found: {concept}")
        groups = numeric_tokens[-digit_groups * 2:]
        current = Decimal("".join(groups[:digit_groups])) * Decimal(1_000_000)
        prior = Decimal("".join(groups[digit_groups:])) * Decimal(1_000_000)
        values[concept] = (current, prior, match.group(0).strip())
    opening_match = re.search(r"Остаток\s+на\s+31\s+декабря\s+2021\s+года[^\n]*", text, re.I)
    if not opening_match:
        raise ValueError("2021 opening equity evidence not found")
    opening_tokens = re.findall(r"(?<!\d)\d{1,3}(?!\d)", opening_match.group(0))
    if len(opening_tokens) < 3:
        raise ValueError("2021 opening equity value not found")
    opening_equity = Decimal("".join(opening_tokens[-3:])) * Decimal(1_000_000)
    return {"text": text, "values": values, "perimeter": "CONSOLIDATED",
            "accounting_standard": "IFRS", "currency": "UZS", "unit": "MILLION_UZS",
            "opening_equity_2021": (opening_equity, opening_match.group(0).strip())}


def _ipky_identity(repo: Repository):
    resolution = resolve_security_pair(repo, "IPKY", "UZ7039920002", "2024-12-11", utc_now())
    if resolution.status != RESOLVED:
        raise ValueError(f"IPKY ticker/ISIN identity not resolved: {resolution.status}:{resolution.reason}")
    return repo.connection.execute(
        """SELECT s.security_id,s.issuer_id,i.canonical_issuer_id,i.legal_name
             FROM securities s JOIN issuers i USING(issuer_id)
            WHERE s.security_id=? AND s.issuer_id=? AND i.canonical_issuer_id=?""",
        (resolution.security_id,resolution.issuer_id,resolution.canonical_issuer_id),
    ).fetchone()


def ingest_ipky_audited_pdf(settings: Settings) -> dict:
    with Repository(settings.database_path) as repo:
        repo.initialize()
        repo.ensure_source(SOURCE_ID, "Openinfo official audited financial-statement PDFs",
                           "openinfo.uz", "PRIMARY", "VERIFIED_AUTOMATED",
                           {"document_type": "AUDITED_FINANCIAL_STATEMENTS", "format": "PDF"})
        run_id = repo.start_run(SOURCE_ID, PARSER_VERSION)
        try:
            archived = repo.connection.execute(
                "SELECT storage_path,sha256 FROM raw_documents WHERE source_url=? ORDER BY retrieved_at DESC LIMIT 1",
                (IPKY_2023_URL,),
            ).fetchone()
            payload = None
            if archived and Path(archived["storage_path"]).is_file():
                candidate = Path(archived["storage_path"]).read_bytes()
                if hashlib.sha256(candidate).hexdigest() == archived["sha256"]:
                    payload = candidate
            if payload is None:
                request_url = urllib.parse.quote(IPKY_2023_URL, safe=":/")
                payload = fetch(request_url, timeout=settings.request_timeout_seconds,
                                attempts=settings.retry_attempts, backoff=settings.retry_backoff_seconds)
            parsed = extract_ipky_2023_pdf(payload)
            identity = _ipky_identity(repo)
            if identity is None:
                raise ValueError("verified IPKY identity missing")
            digest = hashlib.sha256(payload).hexdigest()
            retrieved = utc_now()
            raw_id = stable_id("raw-audited-pdf", f"{IPKY_2023_URL}:{digest}")
            storage = settings.raw_data_dir / "openinfo" / "audited_pdf" / f"{raw_id}.pdf"
            storage.parent.mkdir(parents=True, exist_ok=True)
            if not storage.exists():
                storage.write_bytes(payload)
            repo.connection.execute("INSERT OR IGNORE INTO raw_documents VALUES(?,?,?,?,?,?,?,?,?)",
                                    (raw_id, SOURCE_ID, run_id, IPKY_2023_URL, retrieved,
                                     "2024-12-11", "application/pdf", digest, str(storage)))
            document_id = stable_id("financial-document", f"{SOURCE_ID}:IPKY:2023:{digest}")
            repo.connection.execute(
                "INSERT OR IGNORE INTO financial_documents VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (document_id, identity["issuer_id"], raw_id, identity["legal_name"], "CONSOLIDATED",
                 "2023-01-01", "2023-12-31", "2024-12-11", None,
                 "AUDITED_FINANCIAL_STATEMENTS", "PDF", "IFRS", "AUDITED", "UZS", SOURCE_ID,
                 IPKY_2023_URL, "IPKY-IFRS-2023-OPENINFO-354", retrieved, digest,
                 PARSER_VERSION, "ORIGINAL", None),
            )
            evidence = {"ticker": "IPKY", "isin": "UZ7039920002",
                        "parent_openinfo_report": "https://openinfo.uz/en/reports/bank/annual/354",
                        "perimeter_phrase": "консолидированной финансовой отчетности"}
            repo.connection.execute(
                "INSERT OR IGNORE INTO financial_document_identity_assignments VALUES(?,?,?,?,?,?,?,?,?)",
                (str(uuid.uuid4()), document_id, identity["canonical_issuer_id"], identity["security_id"],
                 "2024-12-11", "VERIFIED", "OFFICIAL_OPENINFO_LINK_AND_DOCUMENT_ENTITY",
                 json.dumps(evidence, ensure_ascii=False, sort_keys=True), retrieved),
            )
            repo.connection.execute(
                "INSERT OR IGNORE INTO financial_document_entity_checks VALUES(?,?,?,?,?,?,?)",
                (document_id, identity["issuer_id"], identity["legal_name"], json.dumps(["IPKY"]),
                 "MATCHED", "OFFICIAL_PDF_NAMES_IPAK_YULI_AND_PARENT_REPORT_IDENTITY_MATCHES", retrieved),
            )
            for evidence_type, value, location in (
                ("REPORTING_PERIMETER", "CONSOLIDATED", "auditor report: explicit consolidated financial statements wording"),
                ("SOURCE_UNIT", "MILLION_UZS", "statement headers: в миллионах узбекских сумов"),
                ("ACCOUNTING_STANDARD", "IFRS", "unmodified auditor opinion: МСФО"),
            ):
                evidence_id = stable_id("metadata-evidence", f"{document_id}:{evidence_type}:{value}")
                repo.connection.execute("INSERT OR IGNORE INTO financial_document_metadata_evidence VALUES(?,?,?,?,?,?,?,?,?,?)",
                                        (evidence_id, document_id, evidence_type, value, "HIGH", raw_id,
                                         IPKY_2023_URL, location, PARSER_VERSION, retrieved))
            inserted = 0
            for concept, (current, prior, raw_line) in parsed["values"].items():
                for period_end, value, period_label in (("2023-12-31", current, "CURRENT"),
                                                        ("2022-12-31", prior, "COMPARATIVE")):
                    location = f"pdf:audited-statement/{concept}/{period_label}"
                    raw_value = str(value / Decimal(1_000_000))
                    raw_value_id = stable_id("financial-raw", f"{document_id}:{location}")
                    repo.connection.execute("INSERT OR IGNORE INTO financial_raw_values VALUES(?,?,?,?,?,?,?,?,?)",
                                            (raw_value_id, document_id,
                                             "INCOME_STATEMENT" if concept == "Net Income" else "BALANCE_SHEET",
                                             raw_line, None, raw_value, period_label, location,
                                             "MACHINE_READABLE_PDF"))
                    observation_id = stable_id("financial-observation", f"{document_id}:{concept}:{location}")
                    repo.connection.execute("INSERT OR IGNORE INTO financial_observations VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                                            (observation_id, document_id, identity["issuer_id"],
                                             "INCOME_STATEMENT" if concept == "Net Income" else "BALANCE_SHEET",
                                             concept, period_end[:4] + "-01-01", period_end, raw_value, str(value),
                                             "UZS", "UZS", "AS_REPORTED", location, "MACHINE_READABLE_PDF",
                                             "HIGH", "REPORTED"))
                    append_version(repo, observation_id, document_id, identity["issuer_id"],
                                   "INCOME_STATEMENT" if concept == "Net Income" else "BALANCE_SHEET",
                                   concept, period_end[:4] + "-01-01", period_end, raw_value, str(value),
                                   "UZS", "UZS", location, "MACHINE_READABLE_PDF", "HIGH", "REPORTED",
                                   PARSER_VERSION, "MATCHED", "financial-taxonomy/1.0.0",
                                   "million-uzs-explicit/1.0.0")
                    inserted += 1
            opening, raw_line = parsed["opening_equity_2021"]
            location = "pdf:audited-statement/Equity/OPENING_COMPARATIVE"
            raw_value = str(opening / Decimal(1_000_000))
            raw_value_id = stable_id("financial-raw", f"{document_id}:{location}")
            repo.connection.execute("INSERT OR IGNORE INTO financial_raw_values VALUES(?,?,?,?,?,?,?,?,?)",
                                    (raw_value_id, document_id, "BALANCE_SHEET", raw_line, None,
                                     raw_value, "OPENING_COMPARATIVE", location, "MACHINE_READABLE_PDF"))
            observation_id = stable_id("financial-observation", f"{document_id}:Equity:{location}")
            repo.connection.execute("INSERT OR IGNORE INTO financial_observations VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                                    (observation_id, document_id, identity["issuer_id"], "BALANCE_SHEET",
                                     "Equity", "2021-01-01", "2021-12-31", raw_value, str(opening),
                                     "UZS", "UZS", "AS_REPORTED", location, "MACHINE_READABLE_PDF",
                                     "HIGH", "REPORTED"))
            append_version(repo, observation_id, document_id, identity["issuer_id"], "BALANCE_SHEET",
                           "Equity", "2021-01-01", "2021-12-31", raw_value, str(opening),
                           "UZS", "UZS", location, "MACHINE_READABLE_PDF", "HIGH", "REPORTED",
                           PARSER_VERSION, "MATCHED", "financial-taxonomy/1.0.0",
                           "million-uzs-explicit/1.0.0")
            inserted += 1
            repo.connection.commit()
            repo.finish_run(run_id, "SUCCEEDED", inserted, 0,
                            json.dumps({"document_id": document_id, "perimeter": "CONSOLIDATED"}))
            return {"status": "SUCCEEDED", "document_id": document_id,
                    "observations": inserted, "perimeter": "CONSOLIDATED"}
        except Exception as exc:
            repo.connection.rollback()
            repo.finish_run(run_id, "FAILED", 0, 1, str(exc))
            return {"status": "FAILED", "error": str(exc)}


def _store_assumption(repo: Repository, security_id: str, input_name: str, scenario: str,
                      value: Decimal, provenance: str, source: str, source_date: str,
                      source_url: str, methodology: str, derivation: dict, confidence: str,
                      observation_lineage=()):
    assumption_id = stable_id("valuation-assumption", f"{security_id}:RESIDUAL_INCOME:{input_name}:{scenario}:2026-09-27:{ASSUMPTION_VERSION}")
    repo.connection.execute(
        "INSERT INTO valuation_assumption_inputs VALUES(?,?,?,?,?,?,?,?,?,?,?) "
        "ON CONFLICT(security_id,method,input_name,scenario,as_of_date) DO UPDATE SET "
        "value=excluded.value,provenance_class=excluded.provenance_class,source=excluded.source,created_at=excluded.created_at",
        (assumption_id, security_id, "RESIDUAL_INCOME", input_name, scenario, str(value),
         "UZS" if input_name in {"BOOK_VALUE", "SHARES_OUTSTANDING"} else None,
         "2026-09-27", provenance, source, utc_now()),
    )
    assumption_id = repo.connection.execute(
        "SELECT assumption_id FROM valuation_assumption_inputs WHERE security_id=? AND method=? AND input_name=? AND scenario=? AND as_of_date=?",
        (security_id, "RESIDUAL_INCOME", input_name, scenario, "2026-09-27"),
    ).fetchone()[0]
    repo.connection.execute(
        "INSERT INTO valuation_assumption_details VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(assumption_id) DO UPDATE SET nominal_real_basis=excluded.nominal_real_basis,source_date=excluded.source_date,source_url=excluded.source_url,methodology=excluded.methodology,derivation_json=excluded.derivation_json,confidence=excluded.confidence,assumption_version=excluded.assumption_version,created_at=excluded.created_at",
        (assumption_id, "NOMINAL" if input_name in {"COST_OF_EQUITY", "GROWTH"} else "NOT_APPLICABLE",
         source_date, source_url, methodology, json.dumps(derivation, sort_keys=True), confidence,
         ASSUMPTION_VERSION, utc_now()),
    )
    repo.connection.execute("DELETE FROM valuation_assumption_observation_lineage WHERE assumption_id=?",(assumption_id,))
    for role,version_id,transformation in observation_lineage:
        repo.connection.execute("INSERT INTO valuation_assumption_observation_lineage VALUES(?,?,?,?,?)",
                                (assumption_id,version_id,role,transformation,utc_now()))
    return assumption_id


def _ipky_roe_evidence(repo: Repository):
    document_id = stable_id("financial-document", f"{SOURCE_ID}:IPKY:2023:{repo.connection.execute('SELECT content_hash FROM financial_documents WHERE source_url=? ORDER BY retrieved_at DESC LIMIT 1',(IPKY_2023_URL,)).fetchone()[0]}")
    rows=repo.connection.execute(
        "SELECT version_id,canonical_concept,period_end,normalized_value,currency,unit,reporting_perimeter,accounting_standard,audit_status,publication_date,knowledge_date "
        "FROM financial_observation_versions WHERE document_id=? AND superseded_by_version_id IS NULL "
        "AND canonical_concept IN ('Equity','Net Income') ORDER BY period_end,canonical_concept",(document_id,)).fetchall()
    evidence={(row[1],row[2]):row for row in rows}
    required=(("Equity","2021-12-31"),("Equity","2022-12-31"),("Equity","2023-12-31"),
              ("Net Income","2022-12-31"),("Net Income","2023-12-31"))
    if any(key not in evidence for key in required): raise ValueError("complete IPKY ROE evidence missing")
    metadata={(evidence[key][4],evidence[key][5],evidence[key][6],evidence[key][7],evidence[key][8]) for key in required}
    if metadata!={("UZS","UZS","CONSOLIDATED","IFRS","AUDITED")}:
        raise ValueError("IPKY ROE evidence metadata mismatch")
    if any(evidence[key][9]>"2026-09-27" or evidence[key][10]>"2026-09-27T23:59:59.999999+00:00" for key in required):
        raise ValueError("IPKY ROE evidence is not point-in-time eligible")
    return evidence


def store_ipky_residual_income_assumptions(database: Path) -> dict:
    with Repository(database) as repo:
        repo.initialize()
        identity = _ipky_identity(repo)
        curve = repo.connection.execute(
            """SELECT v.curve_vintage_id,v.curve_date,p.zero_rate_percent
                 FROM government_yield_curve_vintages v JOIN government_yield_curve_points p USING(curve_vintage_id)
                WHERE v.curve_date<='2026-09-27' ORDER BY v.curve_date DESC,abs(p.tenor_days-3652) LIMIT 1"""
        ).fetchone()
        if identity is None or curve is None:
            raise ValueError("IPKY identity or CBU curve unavailable")
        evidence=_ipky_roe_evidence(repo)
        value=lambda concept,period:Decimal(evidence[(concept,period)][3])
        version=lambda concept,period:evidence[(concept,period)][0]
        equity = value("Equity","2023-12-31")
        shares = Decimal("60239945264")
        average_equity_2022=(value("Equity","2021-12-31")+value("Equity","2022-12-31"))/2
        average_equity_2023=(value("Equity","2022-12-31")+equity)/2
        roe_2022 = value("Net Income","2022-12-31") / average_equity_2022
        roe_2023 = value("Net Income","2023-12-31") / average_equity_2023
        normalized_roe = (roe_2022 + roe_2023) / 2
        government_effective = (Decimal(str(curve["zero_rate_percent"])) / 100).exp() - 1
        default_spread = Decimal("0.0306")
        mature_erp = Decimal("0.0423")
        country_risk_premium = Decimal("0.0466")
        regional_bank_beta = Decimal("0.51")
        base_cost = government_effective - default_spread + regional_bank_beta * mature_erp + country_risk_premium
        ids = []
        for scenario, roe, cost, growth in (
            ("BEAR", min(roe_2022, roe_2023), base_cost + Decimal("0.02"), Decimal("0.04")),
            ("BASE", normalized_roe, base_cost, Decimal("0.05")),
            ("BULL", max(roe_2022, roe_2023), base_cost - Decimal("0.02"), Decimal("0.06")),
        ):
            if scenario=="BEAR":
                roe_lineage=(("OPENING_EQUITY",version("Equity","2021-12-31"),"AVERAGE_EQUITY=(OPENING_EQUITY+CLOSING_EQUITY)/2"),("CLOSING_EQUITY",version("Equity","2022-12-31"),"AVERAGE_EQUITY=(OPENING_EQUITY+CLOSING_EQUITY)/2"),("NET_INCOME",version("Net Income","2022-12-31"),"ROE=NET_INCOME/AVERAGE_EQUITY"))
            elif scenario=="BULL":
                roe_lineage=(("OPENING_EQUITY",version("Equity","2022-12-31"),"AVERAGE_EQUITY=(OPENING_EQUITY+CLOSING_EQUITY)/2"),("CLOSING_EQUITY",version("Equity","2023-12-31"),"AVERAGE_EQUITY=(OPENING_EQUITY+CLOSING_EQUITY)/2"),("NET_INCOME",version("Net Income","2023-12-31"),"ROE=NET_INCOME/AVERAGE_EQUITY"))
            else:
                roe_lineage=(("OPENING_EQUITY_2022",version("Equity","2021-12-31"),"NORMALIZED_ROE=MEAN(ROE_2022,ROE_2023)"),("CLOSING_EQUITY_2022_OPENING_EQUITY_2023",version("Equity","2022-12-31"),"NORMALIZED_ROE=MEAN(ROE_2022,ROE_2023)"),("CLOSING_EQUITY_2023",version("Equity","2023-12-31"),"NORMALIZED_ROE=MEAN(ROE_2022,ROE_2023)"),("NET_INCOME_2022",version("Net Income","2022-12-31"),"NORMALIZED_ROE=MEAN(ROE_2022,ROE_2023)"),("NET_INCOME_2023",version("Net Income","2023-12-31"),"NORMALIZED_ROE=MEAN(ROE_2022,ROE_2023)"))
            ids.append(_store_assumption(repo, identity["security_id"], "ROE", scenario, roe,
                         "SOURCE_DERIVED", "IPKY audited IFRS 2023 and comparatives", "2024-12-11",
                         IPKY_2023_URL, "Two-year ROE using reported net income divided by average opening/closing equity",
                         {"opening_equity_2021":str(value("Equity","2021-12-31")),"closing_equity_2022":str(value("Equity","2022-12-31")),"closing_equity_2023":str(equity),"net_income_2022":str(value("Net Income","2022-12-31")),"net_income_2023":str(value("Net Income","2023-12-31")),"average_equity_2022":str(average_equity_2022),"average_equity_2023":str(average_equity_2023),"roe_2022": str(roe_2022), "roe_2023": str(roe_2023)}, "LOW",roe_lineage))
            ids.append(_store_assumption(repo, identity["security_id"], "COST_OF_EQUITY", scenario, cost,
                         "MODEL_ESTIMATED", "CBU curve plus Damodaran 2026 country-risk and global bank-beta data", "2026-09-23",
                         DAMODARAN_COUNTRY_URL, "Effective nominal UZS reference less sovereign default spread plus beta times mature ERP plus country-risk premium; +/-2pp sensitivity",
                         {"curve_vintage_id": curve["curve_vintage_id"], "government_zero_continuous": str(curve["zero_rate_percent"]),
                          "government_effective": str(government_effective), "default_spread": str(default_spread),
                          "mature_erp": str(mature_erp), "country_risk_premium": str(country_risk_premium),
                          "regional_bank_beta": str(regional_bank_beta), "beta_source": DAMODARAN_BETA_URL}, "LOW"))
            ids.append(_store_assumption(repo, identity["security_id"], "GROWTH", scenario, growth,
                         "CONFIGURABLE_RESEARCH_ASSUMPTION", "CBU 5% medium-term inflation target", "2026-09-27",
                         CBU_TARGET_URL, "Nominal UZS terminal growth sensitivity centered on official 5% inflation target (+/-1pp)",
                         {"official_target": "0.05", "scenario": scenario}, "LOW"))
        repo.connection.commit()
        return {"assumptions": len(ids), "base_cost_of_equity": str(base_cost),
                "normalized_roe": str(normalized_roe), "curve_date": curve["curve_date"]}


def reconcile_ipky_residual_income(database: Path) -> dict:
    with Repository(database) as repo:
        row = repo.connection.execute(
            """SELECT vr.* FROM valuation_records vr JOIN identifier_history h USING(security_id)
                WHERE h.identifier_type='TICKER' AND h.identifier_value='IPKY'
                  AND vr.method='RESIDUAL_INCOME' AND vr.valuation_model_version=?
                ORDER BY vr.valuation_date DESC LIMIT 1""", (MODEL_VERSION,)
        ).fetchone()
        if row is None or row["status"] != "AVAILABLE":
            raise ValueError("available IPKY residual-income valuation missing")
        assumptions = repo.connection.execute(
            "SELECT input_name,scenario,value FROM valuation_assumption_inputs WHERE security_id=? AND method='RESIDUAL_INCOME' AND as_of_date<=?",
            (row["security_id"], row["valuation_date"]),
        ).fetchall()
        amap = {(r["input_name"], r["scenario"]): Decimal(r["value"]) for r in assumptions}
        calculated = {}
        for scenario in ("BEAR", "BASE", "BULL"):
            calculated[scenario] = residual_income(Decimal("2817695000000"), amap[("ROE", scenario)],
                                                   amap[("COST_OF_EQUITY", scenario)], amap[("GROWTH", scenario)],
                                                   Decimal("60239945264"), 5)
        stored = {"BEAR": Decimal(row["bear_value"]), "BASE": Decimal(row["base_value"]),
                  "BULL": Decimal(row["bull_value"])}
        difference = max(abs(calculated[key] - stored[key]) for key in stored)
        status = "PASSED" if difference == 0 else "FAILED"
        rid = stable_id("valuation-reconciliation", f"{row['valuation_id']}:independent-v1")
        repo.connection.execute("INSERT OR REPLACE INTO valuation_reconciliations VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                                (rid, row["valuation_id"], str(calculated["BEAR"]), str(calculated["BASE"]),
                                 str(calculated["BULL"]), str(stored["BEAR"]), str(stored["BASE"]),
                                 str(stored["BULL"]), str(difference), status,
                                 json.dumps({"formula": "five-year residual income plus continuing value", "years": 5}, sort_keys=True),
                                 "independent-reconciliation/1.0.0", utc_now()))
        repo.connection.commit()
        return {"status": status, "maximum_absolute_difference": str(difference),
                "bear": str(calculated["BEAR"]), "base": str(calculated["BASE"]),
                "bull": str(calculated["BULL"])}


def run_targeted_unlock(settings: Settings) -> dict:
    evidence = ingest_ipky_audited_pdf(settings)
    if evidence["status"] != "SUCCEEDED":
        return evidence
    assumptions = store_ipky_residual_income_assumptions(settings.database_path)
    valuations = run_real_validation(settings.database_path, date(2026, 9, 27))
    reconciliation = reconcile_ipky_residual_income(settings.database_path)
    available = [row for row in valuations if row["status"] == "AVAILABLE"]
    return {"status": "SUCCEEDED", "evidence": evidence, "assumptions": assumptions,
            "available_valuations": available, "reconciliation": reconciliation}
