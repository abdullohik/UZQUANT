from __future__ import annotations

import json
from dataclasses import replace
from dataclasses import asdict, dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path

from .evidence import PROVENANCE_CLASSES
from .repository import Repository, stable_id, utc_now

MODEL_VERSION = "sector-valuation/3.2.0"
INSUFFICIENT = "VALUATION_INSUFFICIENT"
D = Decimal


@dataclass(frozen=True)
class FXInput:
    from_currency: str
    to_currency: str
    rate: Decimal
    rate_date: date
    source: str


@dataclass(frozen=True)
class DCFScenario:
    revenue_growth: Decimal
    ebit_margin: Decimal
    tax_rate: Decimal
    da_pct_revenue: Decimal
    capex_pct_revenue: Decimal
    working_capital_pct_revenue: Decimal
    wacc: Decimal
    terminal_growth: Decimal


@dataclass(frozen=True)
class ValuationResult:
    status: str
    method: str
    currency: str | None
    bear_value: Decimal | None = None
    base_value: Decimal | None = None
    bull_value: Decimal | None = None
    confidence: str = "UNAVAILABLE"
    reasons: tuple[str, ...] = ()

@dataclass(frozen=True)
class AssumptionInput:
    value: Decimal | None
    provenance_class: str
    source: str | None = None

    def validate(self):
        if self.provenance_class not in PROVENANCE_CLASSES: raise ValueError("invalid assumption provenance")
        if self.value is not None and self.provenance_class!="UNAVAILABLE" and not self.source:
            raise ValueError("available assumption requires provenance source")

def method_requirements(method:str)->tuple[str,...]:
    return {
      "P/E":("Net Income","Shares Outstanding","Bear Multiple","Base Multiple","Bull Multiple"),
      "P/B":("Equity","Shares Outstanding","Bear Multiple","Base Multiple","Bull Multiple"),
      "P/TBV":("Tangible Book Value","Shares Outstanding","Bear Multiple","Base Multiple","Bull Multiple"),
      "EV/EBITDA":("EBITDA","Net Debt","Shares Outstanding","Bear Multiple","Base Multiple","Bull Multiple"),
      "EV/EBIT":("EBIT","Net Debt","Shares Outstanding","Bear Multiple","Base Multiple","Bull Multiple"),
      "FCF_YIELD":("Free Cash Flow","Shares Outstanding","Bear Yield","Base Yield","Bull Yield"),
      "DDM":("Dividend Per Share","Bear Cost of Equity","Base Cost of Equity","Bull Cost of Equity","Growth"),
      "RESIDUAL_INCOME":("Equity","ROE","Shares Outstanding","Cost of Equity","Growth"),
      "INDUSTRIAL_DCF":("Revenue","Net Debt","Shares Outstanding","DCF Scenarios","Country Risk Premium"),
      "MINING_SCENARIO_DCF":("Production","Commodity Price","Unit Cost","CapEx","FX","Shares Outstanding","Discount Rate"),
    }.get(method,())

def execute_multiple_method(method:str,metric_total:Decimal|None,shares:Decimal|None,
                            scenario_multiples:dict[str,AssumptionInput],currency:str,
                            preferred_rights_sufficient:bool=True)->ValuationResult:
    if method not in {"P/E","P/B"}: return ValuationResult(INSUFFICIENT,method,currency,reasons=("METHOD_NOT_IMPLEMENTED",))
    if metric_total is None or shares is None or shares<=0: return ValuationResult(INSUFFICIENT,method,currency,reasons=("MISSING_VERIFIED_INPUT",))
    if not preferred_rights_sufficient: return ValuationResult(INSUFFICIENT,method,currency,reasons=("PREFERRED_VALUE_ALLOCATION_UNSUPPORTED",))
    if set(scenario_multiples)!={"bear","base","bull"}: return ValuationResult(INSUFFICIENT,method,currency,reasons=("MISSING_SCENARIO_MULTIPLES",))
    try:
        for item in scenario_multiples.values(): item.validate()
    except ValueError as exc: return ValuationResult(INSUFFICIENT,method,currency,reasons=(str(exc).upper().replace(" ","_"),))
    if any(x.value is None or x.value<0 or x.provenance_class=="UNAVAILABLE" for x in scenario_multiples.values()):
        return ValuationResult(INSUFFICIENT,method,currency,reasons=("UNAVAILABLE_SCENARIO_MULTIPLE",))
    per_share=metric_total/shares
    vals={k:per_share*v.value for k,v in scenario_multiples.items()}
    if not vals["bear"]<=vals["base"]<=vals["bull"]: return ValuationResult(INSUFFICIENT,method,currency,reasons=("NON_MONOTONIC_SCENARIOS",))
    return ValuationResult("AVAILABLE",method,currency,vals["bear"],vals["base"],vals["bull"],"METHOD_INPUT_DEPENDENT")

def combine_valuations(results:list[tuple[ValuationResult,Decimal]])->ValuationResult:
    valid=[(r,w) for r,w in results if r.status=="AVAILABLE" and w>0]
    if not valid: return ValuationResult(INSUFFICIENT,"CONSENSUS",None,reasons=("NO_VALID_METHOD",))
    currencies={r.currency for r,_ in valid}
    if len(currencies)!=1: return ValuationResult(INSUFFICIENT,"CONSENSUS",None,reasons=("MIXED_CURRENCIES",))
    total=sum((w for _,w in valid),D(0))
    avg=lambda field:sum((getattr(r,field)*w for r,w in valid),D(0))/total
    return ValuationResult("AVAILABLE","CONSENSUS",next(iter(currencies)),avg("bear_value"),avg("base_value"),avg("bull_value"),"WEIGHTED_BY_METHOD_CONFIDENCE")


def validate_consistency(cashflow_currency: str, discount_currency: str,
                         cashflow_basis: str, discount_basis: str,
                         fx: FXInput | None = None) -> None:
    if cashflow_basis not in {"NOMINAL", "REAL"} or discount_basis not in {"NOMINAL", "REAL"}:
        raise ValueError("basis must be NOMINAL or REAL")
    if cashflow_basis != discount_basis:
        raise ValueError("cash-flow and discount-rate bases differ")
    if cashflow_currency != discount_currency:
        if not fx or (fx.from_currency, fx.to_currency) != (cashflow_currency, discount_currency):
            raise ValueError("currency conversion requires a matching sourced FX input")
        if fx.rate <= 0 or not fx.source:
            raise ValueError("FX rate and source must be valid")


def convert_fx(amount: Decimal, fx: FXInput) -> Decimal:
    if amount is None or fx.rate <= 0 or not fx.source:
        raise ValueError("invalid FX conversion")
    return amount * fx.rate


def dcf_value(revenue: Decimal | None, scenario: DCFScenario,
              years: int, net_debt: Decimal | None,
              shares_outstanding: Decimal | None) -> dict[str, Decimal]:
    if revenue is None or net_debt is None or shares_outstanding is None:
        raise ValueError("missing DCF input")
    if revenue < 0 or years < 1 or shares_outstanding <= 0:
        raise ValueError("invalid DCF input")
    if not D("0") <= scenario.tax_rate <= D("1"):
        raise ValueError("invalid tax rate")
    if scenario.wacc <= scenario.terminal_growth or scenario.wacc <= 0:
        raise ValueError("WACC must exceed terminal growth")
    enterprise = D("0")
    prior_revenue = revenue
    last_fcf = D("0")
    for year in range(1, years + 1):
        projected = prior_revenue * (D("1") + scenario.revenue_growth)
        ebit = projected * scenario.ebit_margin
        da = projected * scenario.da_pct_revenue
        capex = projected * scenario.capex_pct_revenue
        delta_wc = (projected - prior_revenue) * scenario.working_capital_pct_revenue
        last_fcf = ebit * (D("1") - scenario.tax_rate) + da - capex - delta_wc
        enterprise += last_fcf / ((D("1") + scenario.wacc) ** year)
        prior_revenue = projected
    terminal = last_fcf * (D("1") + scenario.terminal_growth) / (scenario.wacc - scenario.terminal_growth)
    enterprise += terminal / ((D("1") + scenario.wacc) ** years)
    equity = enterprise - net_debt
    return {"enterprise_value": enterprise, "equity_value": equity,
            "fair_value_per_share": equity / shares_outstanding,
            "terminal_value": terminal, "last_fcf": last_fcf}


def industrial_dcf(revenue: Decimal | None, scenarios: dict[str, DCFScenario], years: int,
                   net_debt: Decimal | None, shares_outstanding: Decimal | None,
                   currency: str, cashflow_basis: str, discount_basis: str,
                   discount_currency: str, country_risk_premium: Decimal | None,
                   fx: FXInput | None = None) -> ValuationResult:
    missing = []
    for name, value in (("REVENUE", revenue), ("NET_DEBT", net_debt),
                        ("SHARES_OUTSTANDING", shares_outstanding),
                        ("COUNTRY_RISK_PREMIUM", country_risk_premium)):
        if value is None:
            missing.append(f"MISSING_{name}")
    if set(scenarios) != {"bear", "base", "bull"}:
        missing.append("MISSING_SCENARIOS")
    if missing:
        return ValuationResult(INSUFFICIENT, "INDUSTRIAL_DCF", currency, reasons=tuple(missing))
    try:
        validate_consistency(currency, discount_currency, cashflow_basis, discount_basis, fx)
        values = {name: dcf_value(revenue, scenario, years, net_debt, shares_outstanding)
                  for name, scenario in scenarios.items()}
    except ValueError as exc:
        return ValuationResult(INSUFFICIENT, "INDUSTRIAL_DCF", currency,
                               reasons=(str(exc).upper().replace(" ", "_"),))
    return ValuationResult("AVAILABLE", "INDUSTRIAL_DCF", discount_currency,
                           values["bear"]["fair_value_per_share"],
                           values["base"]["fair_value_per_share"],
                           values["bull"]["fair_value_per_share"], "MODEL_BASED")


def dcf_sensitivity_grid(revenue: Decimal, base: DCFScenario, years: int,
                         net_debt: Decimal, shares: Decimal,
                         wacc_values: tuple[Decimal, ...], terminal_growth_values: tuple[Decimal, ...],
                         revenue_growth_values: tuple[Decimal, ...] = (),
                         margin_values: tuple[Decimal, ...] = ()):
    rows = []
    dimensions = (("WACC", "wacc", wacc_values),
                  ("TERMINAL_GROWTH", "terminal_growth", terminal_growth_values),
                  ("REVENUE_GROWTH", "revenue_growth", revenue_growth_values),
                  ("EBIT_MARGIN", "ebit_margin", margin_values))
    for label, field, values in dimensions:
        for value in values:
            try:
                result = dcf_value(revenue, replace(base, **{field: value}), years, net_debt, shares)
                rows.append({"dimension": label, "assumption_value": value, **result})
            except ValueError:
                rows.append({"dimension": label, "assumption_value": value,
                             "enterprise_value": None, "equity_value": None,
                             "fair_value_per_share": None})
    return rows


def relative_metrics(price=None, eps=None, book_per_share=None, enterprise_value=None,
                     ebitda=None, ebit=None, sales=None, fcf=None, dividends_per_share=None):
    def ratio(n, d, positive=False):
        if n is None or d is None or d == 0 or (positive and d <= 0):
            return None
        return n / d
    return {"P/E": ratio(price, eps, True), "P/B": ratio(price, book_per_share),
            "EV/EBITDA": ratio(enterprise_value, ebitda, True),
            "EV/EBIT": ratio(enterprise_value, ebit, True),
            "EV/Sales": ratio(enterprise_value, sales, True),
            "FCF Yield": ratio(fcf, price), "Dividend Yield": ratio(dividends_per_share, price)}


def residual_income(book_value: Decimal | None, roe: Decimal | None,
                    cost_of_equity: Decimal | None, growth: Decimal | None,
                    shares: Decimal | None, years: int = 5) -> Decimal | None:
    if None in (book_value, roe, cost_of_equity, growth, shares) or shares <= 0:
        return None
    if cost_of_equity <= growth:
        return None
    book, value = book_value, book_value
    for year in range(1, years + 1):
        residual = book * (roe - cost_of_equity)
        value += residual / ((D("1") + cost_of_equity) ** year)
        book *= D("1") + growth
    continuing = book * (roe - cost_of_equity) * (D("1") + growth) / (cost_of_equity - growth)
    value += continuing / ((D("1") + cost_of_equity) ** years)
    return value / shares


def dividend_discount(dividend_per_share: Decimal | None, cost_of_equity: Decimal | None,
                      growth: Decimal | None) -> Decimal | None:
    if None in (dividend_per_share, cost_of_equity, growth) or dividend_per_share < 0:
        return None
    if cost_of_equity <= growth:
        return None
    return dividend_per_share * (D("1") + growth) / (cost_of_equity - growth)


def implied_equity_multiple(metric_per_share: Decimal | None, peer_multiple: Decimal | None,
                            require_positive_metric: bool = False) -> Decimal | None:
    if metric_per_share is None or peer_multiple is None or peer_multiple < 0:
        return None
    if require_positive_metric and metric_per_share <= 0:
        return None
    return metric_per_share * peer_multiple


def route_valuation(sector: str) -> tuple[str, tuple[str, ...]]:
    sector = sector.upper()
    if sector == "BANK": return "BANK", ("P/B", "P/TBV", "P/E", "RESIDUAL_INCOME", "DDM")
    if sector == "INSURANCE": return "INSURANCE", ("P/B", "P/E", "ROE_ADJUSTED_P/B", "RESIDUAL_INCOME", "DDM")
    if sector in {"MINING", "COMMODITY"}: return "MINING", ("MINING_SCENARIO_DCF","EV/EBITDA","EV/EBIT","P/E","P/B","FCF_YIELD","DDM")
    return "GENERAL", ("INDUSTRIAL_DCF","EV/EBITDA","EV/EBIT","P/E","P/B","FCF_YIELD","DDM")


def _residual_income_source_lineage(repo, assembled, detailed_rows):
    """Return only the versioned observations actually used by residual income."""
    exact_rows = [assembled["latest_concepts"].get(name) for name in ("Equity", "Net Income")]
    exact_rows = [item for item in exact_rows if item]
    documents = sorted({item["document_id"] for item in exact_rows})
    assumption_ids = [row[5] for row in detailed_rows]
    assumption_versions = []
    if assumption_ids:
        marks = ",".join("?" for _ in assumption_ids)
        assumption_versions = [row[0] for row in repo.connection.execute(
            f"SELECT DISTINCT observation_version_id FROM valuation_assumption_observation_lineage WHERE assumption_id IN ({marks})",
            assumption_ids,
        )]
    observations = sorted({item["observation_id"] for item in exact_rows} | set(assumption_versions))
    return documents, observations


def mining_scenario(production, commodity_price, fx_rate, unit_cost, capex):
    if any(v is None for v in (production, commodity_price, fx_rate, unit_cost, capex)):
        return None
    if production < 0 or commodity_price < 0 or fx_rate <= 0:
        return None
    return production * commodity_price * fx_rate - production * unit_cost - capex


def _real_reasons(repo: Repository, security_id: str, sector: str, as_of: date) -> tuple[list[str], list[str], list[str], dict]:
    docs = repo.connection.execute("SELECT d.document_id,d.currency,d.reporting_perimeter FROM financial_documents d JOIN financial_document_entity_checks c USING(document_id) JOIN financial_document_identity_assignments a USING(document_id) WHERE d.issuer_id=(SELECT issuer_id FROM securities WHERE security_id=?) AND d.publication_date<=? AND c.validation_status='MATCHED' AND a.assignment_status='VERIFIED' ORDER BY d.period_end DESC,d.publication_date DESC", (security_id,as_of.isoformat())).fetchall()
    reasons, document_ids = [], [r[0] for r in docs]
    if not docs: reasons.append("NO_FINANCIAL_DOCUMENT")
    elif len(docs) < 2:
        reasons.append("INSUFFICIENT_FINANCIAL_HISTORY")
    share = repo.connection.execute("SELECT observation_id,class_shares_outstanding,currency FROM share_capital_observations WHERE security_id=? AND disclosure_date<=? AND effective_date<=? AND verification_status='VERIFIED' AND class_shares_outstanding IS NOT NULL ORDER BY effective_date DESC,disclosure_date DESC LIMIT 1",(security_id,as_of.isoformat(),as_of.isoformat())).fetchone()
    if not share: reasons.append("MISSING_VERIFIED_CLASS_SHARES_OUTSTANDING")
    rights = repo.connection.execute("SELECT rights_confidence,voting_rights,dividend_rights FROM security_rights WHERE security_id=? ORDER BY disclosure_date DESC LIMIT 1", (security_id,)).fetchone()
    klass = repo.connection.execute("SELECT security_class_code FROM securities WHERE security_id=?", (security_id,)).fetchone()
    if klass and klass[0] == "PREFERRED" and (not rights or rights[0] != "HIGH" or not rights[2]):
        reasons.append("PREFERRED_SECURITY_RIGHTS_UNVERIFIED")
    observations = [r[0] for r in repo.connection.execute("SELECT version_id FROM financial_observation_versions WHERE superseded_by_version_id IS NULL AND document_id IN (%s)" % (",".join("?" * len(docs)) if docs else "NULL"), document_ids)] if docs else []
    latest = {}
    for concept,value,currency,unit,oid,document_id,perimeter,period_end,standard,audit in repo.connection.execute("SELECT o.canonical_concept,o.normalized_value,o.currency,o.unit,o.version_id,o.document_id,d.reporting_perimeter,o.period_end,d.accounting_standard,d.audit_status FROM financial_observation_versions o JOIN financial_documents d USING(document_id) JOIN financial_document_entity_checks c USING(document_id) JOIN financial_document_identity_assignments a USING(document_id) WHERE o.superseded_by_version_id IS NULL AND o.issuer_id=(SELECT issuer_id FROM securities WHERE security_id=?) AND d.publication_date<=? AND c.validation_status='MATCHED' AND a.assignment_status='VERIFIED' ORDER BY (d.reporting_perimeter!='UNKNOWN') DESC,o.period_end DESC,d.publication_date DESC",(security_id,as_of.isoformat())):
        latest.setdefault(concept,{"value":value,"currency":currency,"unit":unit,"observation_id":oid,"document_id":document_id,"reporting_perimeter":perimeter,"period_end":period_end,"accounting_standard":standard,"audit_status":audit})
    assembled={"latest_concepts":latest,"share_capital_observation_id":share[0] if share else None,"class_shares_outstanding":share[1] if share else None}
    if docs and not latest:
        reasons.extend(("NO_NORMALIZED_FINANCIAL_INPUTS","UNVERIFIED_FINANCIAL_UNIT"))
    return sorted(set(reasons)), document_ids, observations, assembled


def _curve_reference(repo: Repository, as_of: date):
    return repo.connection.execute(
        """SELECT v.curve_vintage_id,v.curve_date,p.tenor_days,p.zero_rate_percent,
                  v.currency,v.rate_basis,v.compounding,v.source_url,v.retrieved_at
           FROM government_yield_curve_vintages v
           JOIN government_yield_curve_points p USING(curve_vintage_id)
           WHERE v.curve_date<=? AND v.retrieved_at<=?
           ORDER BY v.curve_date DESC,abs(p.tenor_days-3652),p.tenor_days DESC LIMIT 1""",
        (as_of.isoformat(), as_of.isoformat() + "T23:59:59.999999+00:00"),
    ).fetchone()


def _concept_blockers(assembled: dict, concepts: tuple[str, ...]) -> list[str]:
    blockers: list[str] = []
    rows = []
    for concept in concepts:
        row = assembled["latest_concepts"].get(concept)
        if row is None:
            blockers.append("MISSING_" + concept.upper().replace("D&A", "D_AND_A").replace(" ", "_"))
        else:
            rows.append(row)
            if not row.get("currency"):
                blockers.append("UNVERIFIED_FINANCIAL_CURRENCY")
            if row.get("unit") == "SOURCE_UNIT_UNSPECIFIED":
                blockers.append("UNVERIFIED_FINANCIAL_UNIT")
            if not row.get("reporting_perimeter") or row.get("reporting_perimeter") == "UNKNOWN":
                blockers.append("UNVERIFIED_REPORTING_PERIMETER")
    if len({row.get("document_id") for row in rows}) > 1:
        blockers.append("CROSS_DOCUMENT_INPUT_COMPATIBILITY_UNVERIFIED")
    return blockers


def _method_blockers(repo: Repository, ticker: str, method: str, base_reasons: list[str],
                     assembled: dict, curve, as_of: date) -> list[str]:
    blockers = list(base_reasons)
    requirements = {
        "P/B": ("Equity",), "P/TBV": ("Equity", "Intangibles"),
        "ROE_ADJUSTED_P/B": ("Equity", "Net Income"), "P/E": ("Net Income",),
        "RESIDUAL_INCOME": ("Equity", "Net Income"),
        "EV/EBITDA": ("EBITDA", "Short-Term Debt", "Long-Term Debt", "Cash"),
        "EV/EBIT": ("EBIT", "Short-Term Debt", "Long-Term Debt", "Cash"),
        "FCF_YIELD": ("Operating Cash Flow", "CapEx"),
        "INDUSTRIAL_DCF": ("Revenue", "Operating Cash Flow", "CapEx", "D&A", "Short-Term Debt", "Long-Term Debt", "Cash"),
        "MINING_SCENARIO_DCF": ("Short-Term Debt", "Long-Term Debt", "Cash"),
    }
    blockers.extend(_concept_blockers(assembled, requirements.get(method, ())))
    if method in {"P/B", "P/TBV", "P/E", "ROE_ADJUSTED_P/B", "EV/EBITDA", "EV/EBIT"}:
        blockers.append("INSUFFICIENT_CREDIBLE_PEER_SET")
    if method in {"RESIDUAL_INCOME", "DDM", "INDUSTRIAL_DCF", "MINING_SCENARIO_DCF"}:
        if curve is None:
            blockers.append("MISSING_AUTHORITATIVE_UZS_RISK_FREE_CURVE")
        if method in {"RESIDUAL_INCOME", "DDM"}:
            blockers.extend(("MISSING_EQUITY_RISK_PREMIUM", "MISSING_SECURITY_OR_SECTOR_BETA", "MISSING_SUPPORTED_LONG_TERM_GROWTH"))
        else:
            blockers.extend(("MISSING_COST_OF_EQUITY_COMPONENTS", "MISSING_COST_OF_DEBT", "MISSING_TARGET_CAPITAL_STRUCTURE", "MISSING_SUPPORTED_FORECAST_SCENARIOS"))
    if method == "DDM":
        dividend = repo.connection.execute(
            "SELECT 1 FROM dividends WHERE security_id=? AND announcement_date<=? AND dividend_per_share IS NOT NULL LIMIT 1",
            (assembled.get("security_id"), as_of.isoformat()),
        ).fetchone() if repo.connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='dividends'").fetchone() else None
        if not dividend:
            blockers.append("MISSING_VERIFIED_SECURITY_CLASS_DIVIDEND_HISTORY")
    if method == "MINING_SCENARIO_DCF":
        blockers.extend(("MISSING_VERIFIED_PRODUCTION", "MISSING_COMMODITY_PRICE_SCENARIOS", "MISSING_UNIT_COST", "MISSING_MINING_CAPEX_FORECAST", "MISSING_FX_SCENARIOS"))
    security = repo.connection.execute(
        "SELECT security_class_code FROM securities WHERE security_id=?",
        (assembled.get("security_id"),),
    ).fetchone()
    if security and security[0] == "PREFERRED":
        rights = repo.connection.execute(
            "SELECT rights_confidence,dividend_rights FROM security_rights "
            "WHERE security_id=? AND disclosure_date<=? ORDER BY disclosure_date DESC LIMIT 1",
            (assembled.get("security_id"), as_of.isoformat()),
        ).fetchone()
        if not rights or rights[0] != "HIGH" or not rights[1]:
            blockers.append("PREFERRED_SECURITY_RIGHTS_UNVERIFIED")
    return sorted(set(blockers))


def run_real_validation(database: Path, valuation_date: date | None = None,
                        tickers: tuple[str, ...] | None = None):
    from .remediation_b import record_model_attempt
    valuation_date = valuation_date or date.today()
    tickers = tickers or ("AGMKP", "KASUP", "IPKY", "UZTL", "QZSM")
    with Repository(database) as repo:
        repo.initialize()
        marks = ",".join("?" for _ in tickers)
        rows = repo.connection.execute(f"SELECT h.identifier_value,s.security_id,s.issuer_id,i.sector,coalesce((SELECT source_url FROM financial_documents WHERE issuer_id=i.issuer_id ORDER BY publication_date DESC LIMIT 1),'') source_url FROM identifier_history h JOIN securities s ON s.security_id=h.security_id JOIN issuers i ON i.issuer_id=s.issuer_id WHERE h.identifier_type='TICKER' AND h.identifier_value IN ({marks}) GROUP BY h.identifier_value,s.security_id", tickers).fetchall()
        results = []
        for row in rows:
            source_sector = ("BANK" if "/bank/" in row[4] else
                             "INSURANCE" if "/insurance/" in row[4] else
                             "MINING" if row[0] in {"AGMK", "AGMKP"} else
                             row[3] or "GENERAL")
            engine, methods = route_valuation(source_sector)
            method = methods[0]
            reasons, docs, observations, assembled = _real_reasons(repo, row[1], engine, valuation_date)
            assembled["security_id"] = row[1]
            curve = _curve_reference(repo, valuation_date)
            for candidate in methods:
                method_missing=_method_blockers(repo,row[0],candidate,reasons,assembled,curve,valuation_date)
                assumptions_rows=repo.connection.execute("SELECT scenario,value,provenance_class,source,assumption_id FROM valuation_assumption_inputs WHERE security_id=? AND method=? AND as_of_date<=? ORDER BY as_of_date DESC",(row[1],candidate,valuation_date.isoformat())).fetchall()
                detailed_rows=repo.connection.execute("SELECT input_name,scenario,value,provenance_class,source,assumption_id FROM valuation_assumption_inputs WHERE security_id=? AND method=? AND as_of_date<=? ORDER BY as_of_date DESC",(row[1],candidate,valuation_date.isoformat())).fetchall()
                assumption_map={(r[0],r[1]):D(r[2]) for r in detailed_rows if r[2] is not None}
                scenario_inputs={r[0].casefold():AssumptionInput(D(r[1]) if r[1] is not None else None,r[2],r[3]) for r in assumptions_rows if r[0] in {"BEAR","BASE","BULL"}}
                result=ValuationResult(INSUFFICIENT,candidate,None,reasons=tuple(sorted(set(method_missing))))
                if candidate in {"P/E","P/B"} and len(scenario_inputs)==3:
                    method_missing=[r for r in method_missing if r!="MISSING_VERIFIED_PEER_MULTIPLE"]
                    concept="Net Income" if candidate=="P/E" else "Equity"
                    metric=assembled["latest_concepts"].get(concept)
                    result=execute_multiple_method(candidate,D(metric["value"]) if metric else None,D(assembled["class_shares_outstanding"]) if assembled["class_shares_outstanding"] else None,scenario_inputs,metric["currency"] if metric else "UZS","PREFERRED_SECURITY_RIGHTS_UNVERIFIED" not in method_missing) if not method_missing else ValuationResult(INSUFFICIENT,candidate,None,reasons=tuple(sorted(set(method_missing))))
                elif candidate=="RESIDUAL_INCOME":
                    required={(name,scenario) for name in ("ROE","COST_OF_EQUITY","GROWTH") for scenario in ("BEAR","BASE","BULL")}
                    if required<=set(assumption_map):
                        method_missing=[reason for reason in method_missing if reason not in {"MISSING_EQUITY_RISK_PREMIUM","MISSING_SECURITY_OR_SECTOR_BETA","MISSING_SUPPORTED_LONG_TERM_GROWTH"}]
                        equity=assembled["latest_concepts"].get("Equity")
                        shares=D(assembled["class_shares_outstanding"]) if assembled["class_shares_outstanding"] else None
                        if not method_missing and equity and shares:
                            vals={scenario:residual_income(D(equity["value"]),assumption_map[("ROE",scenario)],assumption_map[("COST_OF_EQUITY",scenario)],assumption_map[("GROWTH",scenario)],shares,5) for scenario in ("BEAR","BASE","BULL")}
                            if all(value is not None for value in vals.values()) and vals["BEAR"]<=vals["BASE"]<=vals["BULL"]:
                                result=ValuationResult("AVAILABLE",candidate,equity["currency"],vals["BEAR"],vals["BASE"],vals["BULL"],"LOW",())
                            else:
                                result=ValuationResult(INSUFFICIENT,candidate,equity["currency"],reasons=("INVALID_RESIDUAL_INCOME_SCENARIOS",))
                        else:
                            result=ValuationResult(INSUFFICIENT,candidate,None,reasons=tuple(sorted(set(method_missing))))
                final_missing=list(result.reasons) if result.status!= "AVAILABLE" else []
                available_inputs=sorted(assembled["latest_concepts"])
                if curve is not None:
                    available_inputs.append("AUTHORITATIVE_UZS_NOMINAL_GOVERNMENT_ZERO_CURVE")
                status="EXECUTABLE" if not final_missing else ("PARTIALLY_SUPPORTED" if available_inputs else "UNSUPPORTED")
                eligibility_id=stable_id("valuation-eligibility",f"{row[1]}:{valuation_date}:{candidate}:{MODEL_VERSION}")
                repo.connection.execute("INSERT INTO valuation_method_eligibility VALUES(?,?,?,?,?,?,?,?,?,?) ON CONFLICT(security_id,valuation_date,method,model_version) DO UPDATE SET status=excluded.status,blocker_codes_json=excluded.blocker_codes_json,available_inputs_json=excluded.available_inputs_json,reference_curve_vintage_id=excluded.reference_curve_vintage_id,assessed_at=excluded.assessed_at",(eligibility_id,row[1],valuation_date.isoformat(),candidate,status,json.dumps(final_missing),json.dumps(available_inputs),curve[0] if curve else None,MODEL_VERSION,utc_now()))
                valuation_docs = docs
                valuation_observations = observations
                if result.status == "AVAILABLE" and candidate == "RESIDUAL_INCOME":
                    valuation_docs, valuation_observations = _residual_income_source_lineage(
                        repo, assembled, detailed_rows
                    )
                record_model_attempt(repo,row[1],valuation_date,candidate,final_missing,[],valuation_docs+valuation_observations+[r[4] for r in assumptions_rows])
                vid = stable_id("valuation", f"{row[1]}:{valuation_date}:{candidate}:{MODEL_VERSION}")
                assumption_json={"inputs":[dict(r) for r in detailed_rows],"no_assumptions_invented":True,
                                 "assumption_details_table":"valuation_assumption_details"}
                values=(vid,row[1],row[2],valuation_date.isoformat(),valuation_date.isoformat(),json.dumps({"document_ids":valuation_docs,"assembled":assembled},sort_keys=True),candidate,engine,result.currency,json.dumps(assumption_json,sort_keys=True),str(result.bear_value) if result.bear_value is not None else None,str(result.base_value) if result.base_value is not None else None,str(result.bull_value) if result.bull_value is not None else None,result.confidence,MODEL_VERSION,result.status,json.dumps(final_missing),json.dumps(valuation_docs),json.dumps(valuation_observations),utc_now())
                repo.connection.execute("INSERT INTO valuation_records VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(security_id,valuation_date,method,valuation_model_version) DO UPDATE SET financial_period_inputs_json=excluded.financial_period_inputs_json,assumptions_json=excluded.assumptions_json,bear_value=excluded.bear_value,base_value=excluded.base_value,bull_value=excluded.bull_value,confidence=excluded.confidence,status=excluded.status,insufficiency_reasons_json=excluded.insufficiency_reasons_json,source_document_ids_json=excluded.source_document_ids_json,source_observation_ids_json=excluded.source_observation_ids_json,created_at=excluded.created_at",values)
                if candidate in {"P/B","P/TBV","P/E","ROE_ADJUSTED_P/B","EV/EBITDA","EV/EBIT"}:
                    peer_id=stable_id("valuation-peer-set",f"{vid}:credible-local-peers:{MODEL_VERSION}")
                    selection=(f"Version {MODEL_VERSION}: distinct issuers; same economic sector/business; "
                               "compatible period, perimeter, currency and units; verified shares and observed price; minimum 3 peers")
                    peer_evidence={"status":"INSUFFICIENT_CREDIBLE_PEER_SET","minimum_peer_count":3,
                                   "accepted_peer_count":0,"no_cross_sector_substitution":True,
                                   "no_duplicate_share_classes_as_independent_issuers":True}
                    repo.connection.execute("INSERT OR IGNORE INTO valuation_peer_sets VALUES(?,?,?,?,?,?)",(peer_id,vid,valuation_date.isoformat(),selection,json.dumps([]),json.dumps(peer_evidence,sort_keys=True)))
                results.append({"ticker":row[0],"security_id":row[1],"engine":engine,"method":candidate,"status":result.status,"eligibility":status,"reasons":final_missing,"available_inputs":available_inputs,"risk_free_curve_date":curve[1] if curve else None,"risk_free_reference_tenor_days":curve[2] if curve else None,"risk_free_reference_zero_rate_percent":curve[3] if curve else None,"required_share_input":"VERIFIED_CLASS_SHARES_OUTSTANDING","source_document_ids":valuation_docs})
        repo.connection.commit()
        return sorted(results,key=lambda r:r["ticker"])
