from __future__ import annotations

import json
from dataclasses import replace
from dataclasses import asdict, dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path

from .repository import Repository, stable_id, utc_now

MODEL_VERSION = "sector-valuation/3.0.0"
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
        allowed={"OBSERVED","SOURCE_DERIVED","MODEL_ESTIMATED","CONFIGURABLE_RESEARCH_ASSUMPTION","UNAVAILABLE"}
        if self.provenance_class not in allowed: raise ValueError("invalid assumption provenance")
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
    else:
        if any(not r[1] for r in docs): reasons.append("UNVERIFIED_FINANCIAL_CURRENCY")
        if any(not r[2] or r[2] == "UNKNOWN" for r in docs): reasons.append("UNVERIFIED_REPORTING_PERIMETER")
        if len(docs) < 2: reasons.append("INSUFFICIENT_FINANCIAL_HISTORY")
        unit_unknown = repo.connection.execute("SELECT 1 FROM financial_observations WHERE document_id IN (%s) AND unit='SOURCE_UNIT_UNSPECIFIED' LIMIT 1" % ",".join("?" * len(docs)), document_ids).fetchone()
        if unit_unknown: reasons.append("UNVERIFIED_FINANCIAL_UNIT")
    share = repo.connection.execute("SELECT observation_id,class_shares_outstanding,currency FROM share_capital_observations WHERE security_id=? AND disclosure_date<=? AND effective_date<=? AND verification_status='VERIFIED' AND class_shares_outstanding IS NOT NULL ORDER BY effective_date DESC,disclosure_date DESC LIMIT 1",(security_id,as_of.isoformat(),as_of.isoformat())).fetchone()
    if not share: reasons.append("MISSING_VERIFIED_CLASS_SHARES_OUTSTANDING")
    if sector in {"GENERAL", "MINING"}:
        concepts = {r[0] for r in repo.connection.execute("SELECT DISTINCT canonical_concept FROM financial_observations WHERE issuer_id=(SELECT issuer_id FROM securities WHERE security_id=?)", (security_id,))}
        for concept in ("Operating Cash Flow", "CapEx", "D&A"):
            if concept not in concepts: reasons.append("MISSING_" + concept.upper().replace(" ", "_&" if concept == "D&A" else "_"))
    rights = repo.connection.execute("SELECT rights_confidence,voting_rights,dividend_rights FROM security_rights WHERE security_id=? ORDER BY disclosure_date DESC LIMIT 1", (security_id,)).fetchone()
    klass = repo.connection.execute("SELECT security_class_code FROM securities WHERE security_id=?", (security_id,)).fetchone()
    if klass and klass[0] == "PREFERRED" and (not rights or rights[0] != "HIGH" or not rights[2]):
        reasons.append("PREFERRED_SECURITY_RIGHTS_UNVERIFIED")
    observations = [r[0] for r in repo.connection.execute("SELECT observation_id FROM financial_observations WHERE document_id IN (%s)" % (",".join("?" * len(docs)) if docs else "NULL"), document_ids)] if docs else []
    latest = {}
    for concept,value,currency,unit,oid,document_id in repo.connection.execute("SELECT o.canonical_concept,o.normalized_value,o.currency,o.unit,o.observation_id,o.document_id FROM financial_observations o JOIN financial_documents d USING(document_id) JOIN financial_document_entity_checks c USING(document_id) JOIN financial_document_identity_assignments a USING(document_id) WHERE o.issuer_id=(SELECT issuer_id FROM securities WHERE security_id=?) AND d.publication_date<=? AND c.validation_status='MATCHED' AND a.assignment_status='VERIFIED' ORDER BY o.period_end DESC,d.publication_date DESC",(security_id,as_of.isoformat())):
        latest.setdefault(concept,{"value":value,"currency":currency,"unit":unit,"observation_id":oid,"document_id":document_id})
    assembled={"latest_concepts":latest,"share_capital_observation_id":share[0] if share else None,"class_shares_outstanding":share[1] if share else None}
    if docs and not latest:
        reasons.extend(("NO_NORMALIZED_FINANCIAL_INPUTS","UNVERIFIED_FINANCIAL_UNIT"))
    return sorted(set(reasons)), document_ids, observations, assembled


def run_real_validation(database: Path, valuation_date: date = date(2026, 9, 15)):
    from .remediation_b import record_model_attempt
    tickers = ("AGMKP", "KASUP", "IPKY", "UZTL", "QZSM")
    with Repository(database) as repo:
        repo.initialize()
        rows = repo.connection.execute("SELECT h.identifier_value,s.security_id,s.issuer_id,i.sector,coalesce((SELECT source_url FROM financial_documents WHERE issuer_id=i.issuer_id ORDER BY publication_date DESC LIMIT 1),'') source_url FROM identifier_history h JOIN securities s ON s.security_id=h.security_id JOIN issuers i ON i.issuer_id=s.issuer_id WHERE h.identifier_type='TICKER' AND h.identifier_value IN (?,?,?,?,?) GROUP BY h.identifier_value,s.security_id", tickers).fetchall()
        results = []
        for row in rows:
            source_sector = {"IPKY":"BANK","KASUP":"INSURANCE","AGMKP":"MINING"}.get(row[0],row[3] or "GENERAL")
            engine, methods = route_valuation(source_sector)
            method = methods[0]
            reasons, docs, observations, assembled = _real_reasons(repo, row[1], engine, valuation_date)
            for candidate in methods:
                method_missing=list(reasons)
                if candidate not in {"INDUSTRIAL_DCF","MINING_SCENARIO_DCF"}:
                    method_missing=[r for r in method_missing if r not in {"MISSING_CAPEX","MISSING_D&A","MISSING_OPERATING_CASH_FLOW"}]
                if candidate in {"P/B","P/TBV","ROE_ADJUSTED_P/B"}:
                    if "Equity" not in assembled["latest_concepts"]: method_missing.append("MISSING_EQUITY")
                    method_missing.append("MISSING_VERIFIED_PEER_MULTIPLE")
                elif candidate=="P/E":
                    if "Net Income" not in assembled["latest_concepts"]: method_missing.append("MISSING_NET_INCOME")
                    method_missing.append("MISSING_VERIFIED_PEER_MULTIPLE")
                elif candidate in {"RESIDUAL_INCOME","DDM"}: method_missing.append("MISSING_SOURCEABLE_COST_OF_EQUITY_ASSUMPTIONS")
                elif candidate in {"INDUSTRIAL_DCF","MINING_SCENARIO_DCF"}: method_missing.append("MISSING_SOURCEABLE_DISCOUNT_RATE_ASSUMPTIONS")
                else: method_missing.append("MISSING_VERIFIED_RELATIVE_VALUATION_ASSUMPTIONS")
                assumptions_rows=repo.connection.execute("SELECT scenario,value,provenance_class,source,assumption_id FROM valuation_assumption_inputs WHERE security_id=? AND method=? AND as_of_date<=? ORDER BY as_of_date DESC",(row[1],candidate,valuation_date.isoformat())).fetchall()
                scenario_inputs={r[0].casefold():AssumptionInput(D(r[1]) if r[1] is not None else None,r[2],r[3]) for r in assumptions_rows if r[0] in {"BEAR","BASE","BULL"}}
                result=ValuationResult(INSUFFICIENT,candidate,None,reasons=tuple(sorted(set(method_missing))))
                if candidate in {"P/E","P/B"} and len(scenario_inputs)==3:
                    method_missing=[r for r in method_missing if r!="MISSING_VERIFIED_PEER_MULTIPLE"]
                    concept="Net Income" if candidate=="P/E" else "Equity"
                    metric=assembled["latest_concepts"].get(concept)
                    result=execute_multiple_method(candidate,D(metric["value"]) if metric else None,D(assembled["class_shares_outstanding"]) if assembled["class_shares_outstanding"] else None,scenario_inputs,metric["currency"] if metric else "UZS",row[0] not in {"AGMKP","KASUP"}) if not method_missing else ValuationResult(INSUFFICIENT,candidate,None,reasons=tuple(sorted(set(method_missing))))
                final_missing=list(result.reasons) if result.status!= "AVAILABLE" else []
                record_model_attempt(repo,row[1],valuation_date,candidate,final_missing,[],docs+observations+[r[4] for r in assumptions_rows])
                vid = stable_id("valuation", f"{row[1]}:{valuation_date}:{candidate}:{MODEL_VERSION}")
                assumption_json={"inputs":[dict(r) for r in assumptions_rows],"no_assumptions_invented":True}
                values=(vid,row[1],row[2],valuation_date.isoformat(),valuation_date.isoformat(),json.dumps({"document_ids":docs,"assembled":assembled},sort_keys=True),candidate,engine,result.currency,json.dumps(assumption_json,sort_keys=True),str(result.bear_value) if result.bear_value is not None else None,str(result.base_value) if result.base_value is not None else None,str(result.bull_value) if result.bull_value is not None else None,result.confidence,MODEL_VERSION,result.status,json.dumps(final_missing),json.dumps(docs),json.dumps(observations),utc_now())
                repo.connection.execute("INSERT INTO valuation_records VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(security_id,valuation_date,method,valuation_model_version) DO UPDATE SET financial_period_inputs_json=excluded.financial_period_inputs_json,assumptions_json=excluded.assumptions_json,bear_value=excluded.bear_value,base_value=excluded.base_value,bull_value=excluded.bull_value,confidence=excluded.confidence,status=excluded.status,insufficiency_reasons_json=excluded.insufficiency_reasons_json,source_document_ids_json=excluded.source_document_ids_json,source_observation_ids_json=excluded.source_observation_ids_json,created_at=excluded.created_at",values)
                results.append({"ticker":row[0],"security_id":row[1],"engine":engine,"method":candidate,"status":result.status,"reasons":final_missing,"available_inputs":sorted(assembled["latest_concepts"]),"required_share_input":"VERIFIED_CLASS_SHARES_OUTSTANDING","source_document_ids":docs})
        repo.connection.commit()
        return sorted(results,key=lambda r:r["ticker"])
