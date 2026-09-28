from __future__ import annotations
import json,uuid
from dataclasses import dataclass
from datetime import date,timedelta
from decimal import Decimal
from .repository import Repository,stable_id,utc_now

FORMULA_VERSION="fundamental-metrics/1.1.0"
GENERAL_METRICS=("Revenue Growth","Gross Margin","EBITDA Growth","EBITDA Margin","EBIT Growth","EBIT Margin","Net Income Growth","Net Margin","ROA","ROE","ROIC","Asset Turnover","Current Ratio","Quick Ratio","Debt/Equity","Net Debt","Net Debt/EBITDA","Interest Coverage","Operating Cash Flow Margin","Free Cash Flow","FCF Margin","CapEx/Sales","Dividend Payout Ratio")
BANK_METRICS=("Assets","Loans","Deposits","Equity","Net Interest Income","NIM","ROA","ROE","Loan Growth","Deposit Growth","NPL","Provisioning","Capital Adequacy","Cost/Income")
INSURANCE_METRICS=("Premium Growth","Claims","Loss Ratio","Expense Ratio","Combined Ratio","Investment Income","Reserves","ROE","Solvency")
MINING_METRICS=("Production","Unit Costs","Capital Intensity","Commodity Exposure","Operating Leverage")
QUALITY_METRICS=("CFO / Net Income","FCF / Net Income","Accrual Measure","Receivables Growth vs Revenue Growth","Inventory Growth vs Revenue Growth","Working-Capital Intensity","Cash Conversion","CapEx Intensity","D&A vs CapEx","Debt Growth")

@dataclass(frozen=True)
class Result:
    value:Decimal|None; reason:str|None=None; inputs:tuple[str,...]=()
    @property
    def status(self): return "AVAILABLE" if self.value is not None else "UNAVAILABLE"
@dataclass(frozen=True)
class PeriodValue:
    start:date; end:date; value:Decimal; currency:str|None; unit:str; perimeter:str; standard:str

def safe_div(numerator:Decimal|None,denominator:Decimal|None,*inputs):
    if numerator is None or denominator is None: return Result(None,"MISSING_INPUT",inputs)
    if denominator==0: return Result(None,"ZERO_DENOMINATOR",inputs)
    return Result(numerator/denominator,None,inputs)
def growth(current:Decimal|None,prior:Decimal|None,*inputs):
    if current is None or prior is None: return Result(None,"NO_COMPATIBLE_PRIOR_PERIOD",inputs)
    if prior==0: return Result(None,"ZERO_PRIOR_PERIOD",inputs)
    return Result(current/prior-Decimal(1),None,inputs)
def construct_ttm(periods:list[PeriodValue])->Result:
    if len(periods)!=4: return Result(None,"TTM_REQUIRES_FOUR_QUARTERS")
    ordered=sorted(periods,key=lambda p:p.start)
    metadata={(p.currency,p.unit,p.perimeter,p.standard) for p in ordered}
    if len(metadata)!=1 or None in {p.currency for p in ordered}: return Result(None,"INCOMPATIBLE_PERIOD_METADATA")
    if any(ordered[i].end+timedelta(days=1)!=ordered[i+1].start for i in range(3)): return Result(None,"OVERLAPPING_OR_GAPPED_PERIODS")
    if any((p.end-p.start).days not in range(88,93) for p in ordered): return Result(None,"PERIOD_IS_NOT_QUARTERLY")
    return Result(sum((p.value for p in ordered),Decimal(0)))
def historical_growth(current:PeriodValue,prior:PeriodValue,years:int)->Result:
    if years not in (1,3,5): return Result(None,"UNSUPPORTED_HORIZON")
    if current.start.year-prior.start.year!=years or current.end.year-prior.end.year!=years: return Result(None,"PERIOD_MISMATCH")
    if abs((current.end-current.start).days-(prior.end-prior.start).days)>1: return Result(None,"PERIOD_MISMATCH")
    metadata=(current.currency,current.unit,current.perimeter,current.standard)
    if None in metadata or "UNKNOWN" in metadata or metadata!=(prior.currency,prior.unit,prior.perimeter,prior.standard): return Result(None,"INCOMPATIBLE_PERIOD_METADATA")
    return growth(current.value,prior.value)
def route_sector(source_url:str,sector:str|None=None)->str:
    if "/bank/" in source_url: return "BANK"
    if "/insurance/" in source_url: return "INSURANCE"
    if sector and sector.casefold() in {"mining","metals & mining","commodity"}: return "MINING"
    return "GENERAL"
def _sum_strict(values:dict[str,Decimal|None],*names):
    parts=[values.get(n) for n in names]
    return None if any(v is None for v in parts) else sum(parts,Decimal(0))
def compute_general(v:dict[str,Decimal|None],prior:dict[str,Decimal|None]|None=None)->dict[str,Result]:
    prior=prior or {}; debt=_sum_strict(v,"Short-Term Debt","Long-Term Debt"); pdebt=_sum_strict(prior,"Short-Term Debt","Long-Term Debt")
    fcf=None if v.get("Operating Cash Flow") is None or v.get("CapEx") is None else v["Operating Cash Flow"]-v["CapEx"]
    results={
      "Revenue Growth":growth(v.get("Revenue"),prior.get("Revenue"),"Revenue"),
      "Gross Margin":safe_div(v.get("Gross Profit"),v.get("Revenue"),"Gross Profit","Revenue"),
      "EBITDA Growth":growth(v.get("EBITDA"),prior.get("EBITDA"),"EBITDA"),
      "EBITDA Margin":safe_div(v.get("EBITDA"),v.get("Revenue"),"EBITDA","Revenue"),
      "EBIT Growth":growth(v.get("EBIT"),prior.get("EBIT"),"EBIT"),
      "EBIT Margin":safe_div(v.get("EBIT"),v.get("Revenue"),"EBIT","Revenue"),
      "Net Income Growth":growth(v.get("Net Income"),prior.get("Net Income"),"Net Income"),
      "Net Margin":safe_div(v.get("Net Income"),v.get("Revenue"),"Net Income","Revenue"),
      "ROA":safe_div(v.get("Net Income"),v.get("Average Assets"),"Net Income","Average Assets"),
      "ROE":safe_div(v.get("Net Income"),v.get("Average Equity"),"Net Income","Average Equity"),
      "ROIC":safe_div(v.get("NOPAT"),v.get("Average Invested Capital"),"NOPAT","Average Invested Capital"),
      "Asset Turnover":safe_div(v.get("Revenue"),v.get("Average Assets"),"Revenue","Average Assets"),
      "Current Ratio":safe_div(v.get("Current Assets"),v.get("Current Liabilities"),"Current Assets","Current Liabilities"),
      "Quick Ratio":safe_div(None if v.get("Current Assets") is None or v.get("Inventory") is None else v["Current Assets"]-v["Inventory"],v.get("Current Liabilities"),"Current Assets","Inventory","Current Liabilities"),
      "Debt/Equity":safe_div(debt,v.get("Equity"),"Short-Term Debt","Long-Term Debt","Equity"),
      "Net Debt":Result(None,"MISSING_INPUT",("Short-Term Debt","Long-Term Debt","Cash")) if debt is None or v.get("Cash") is None else Result(debt-v["Cash"],None,("Short-Term Debt","Long-Term Debt","Cash")),
      "Net Debt/EBITDA":safe_div(None if debt is None or v.get("Cash") is None else debt-v["Cash"],v.get("EBITDA"),"Debt","Cash","EBITDA"),
      "Interest Coverage":safe_div(v.get("EBIT"),v.get("Interest Expense"),"EBIT","Interest Expense"),
      "Operating Cash Flow Margin":safe_div(v.get("Operating Cash Flow"),v.get("Revenue"),"Operating Cash Flow","Revenue"),
      "Free Cash Flow":Result(fcf,None,("Operating Cash Flow","CapEx")) if fcf is not None else Result(None,"MISSING_INPUT",("Operating Cash Flow","CapEx")),
      "FCF Margin":safe_div(fcf,v.get("Revenue"),"Free Cash Flow","Revenue"),
      "CapEx/Sales":safe_div(v.get("CapEx"),v.get("Revenue"),"CapEx","Revenue"),
      "Dividend Payout Ratio":safe_div(v.get("Dividends"),v.get("Net Income"),"Dividends","Net Income"),
    }
    return results
def compute_quality(v:dict[str,Decimal|None],prior:dict[str,Decimal|None]|None=None):
    prior=prior or {}; fcf=None if v.get("Operating Cash Flow") is None or v.get("CapEx") is None else v["Operating Cash Flow"]-v["CapEx"]
    rg=growth(v.get("Receivables"),prior.get("Receivables"),"Receivables"); revg=growth(v.get("Revenue"),prior.get("Revenue"),"Revenue"); ig=growth(v.get("Inventory"),prior.get("Inventory"),"Inventory")
    debt=_sum_strict(v,"Short-Term Debt","Long-Term Debt"); pdebt=_sum_strict(prior,"Short-Term Debt","Long-Term Debt")
    wc=None if any(v.get(k) is None for k in ("Receivables","Inventory","Accounts Payable")) else v["Receivables"]+v["Inventory"]-v["Accounts Payable"]
    metrics={
      "CFO / Net Income":safe_div(v.get("Operating Cash Flow"),v.get("Net Income"),"Operating Cash Flow","Net Income"),
      "FCF / Net Income":safe_div(fcf,v.get("Net Income"),"Free Cash Flow","Net Income"),
      "Accrual Measure":safe_div(None if v.get("Net Income") is None or v.get("Operating Cash Flow") is None else v["Net Income"]-v["Operating Cash Flow"],v.get("Average Assets"),"Net Income","Operating Cash Flow","Average Assets"),
      "Receivables Growth vs Revenue Growth":Result(rg.value-revg.value,None,("Receivables","Revenue")) if rg.value is not None and revg.value is not None else Result(None,"NO_COMPATIBLE_PRIOR_PERIOD",("Receivables","Revenue")),
      "Inventory Growth vs Revenue Growth":Result(ig.value-revg.value,None,("Inventory","Revenue")) if ig.value is not None and revg.value is not None else Result(None,"NO_COMPATIBLE_PRIOR_PERIOD",("Inventory","Revenue")),
      "Working-Capital Intensity":safe_div(wc,v.get("Revenue"),"Receivables","Inventory","Accounts Payable","Revenue"),
      "Cash Conversion":safe_div(v.get("Operating Cash Flow"),v.get("Net Income"),"Operating Cash Flow","Net Income"),
      "CapEx Intensity":safe_div(v.get("CapEx"),v.get("Revenue"),"CapEx","Revenue"),
      "D&A vs CapEx":safe_div(v.get("D&A"),v.get("CapEx"),"D&A","CapEx"),
      "Debt Growth":growth(debt,pdebt,"Short-Term Debt","Long-Term Debt"),
    }
    flags={
      "RECEIVABLES_GROWING_FASTER_THAN_REVENUE":_flag(metrics["Receivables Growth vs Revenue Growth"],Decimal("0.10"),"gt"),
      "POOR_CASH_CONVERSION":_flag(metrics["Cash Conversion"],Decimal("0.70"),"lt"),
      "RAPID_DEBT_GROWTH":_flag(metrics["Debt Growth"],Decimal("0.30"),"gt"),
      "INVENTORY_ANOMALY":_flag(metrics["Inventory Growth vs Revenue Growth"],Decimal("0.15"),"gt"),
    }
    return metrics,flags
def compute_bank(v:dict[str,Decimal|None],prior:dict[str,Decimal|None]|None=None):
    prior=prior or {}; income=None if v.get("Net Interest Income") is None or v.get("Non-Interest Income") is None else v["Net Interest Income"]+v["Non-Interest Income"]
    return {"Assets":Result(v.get("Total Assets"),"MISSING_INPUT" if v.get("Total Assets") is None else None,("Total Assets",)),"Loans":Result(v.get("Loans"),"MISSING_INPUT" if v.get("Loans") is None else None,("Loans",)),"Deposits":Result(v.get("Deposits"),"MISSING_INPUT" if v.get("Deposits") is None else None,("Deposits",)),"Equity":Result(v.get("Equity"),"MISSING_INPUT" if v.get("Equity") is None else None,("Equity",)),"Net Interest Income":Result(v.get("Net Interest Income"),"MISSING_INPUT" if v.get("Net Interest Income") is None else None,("Net Interest Income",)),"NIM":safe_div(v.get("Net Interest Income"),v.get("Average Earning Assets"),"Net Interest Income","Average Earning Assets"),"ROA":safe_div(v.get("Net Income"),v.get("Average Assets"),"Net Income","Average Assets"),"ROE":safe_div(v.get("Net Income"),v.get("Average Equity"),"Net Income","Average Equity"),"Loan Growth":growth(v.get("Loans"),prior.get("Loans"),"Loans"),"Deposit Growth":growth(v.get("Deposits"),prior.get("Deposits"),"Deposits"),"NPL":safe_div(v.get("Nonperforming Loans"),v.get("Loans"),"Nonperforming Loans","Loans"),"Provisioning":safe_div(v.get("Loan Loss Provisions"),v.get("Loans"),"Loan Loss Provisions","Loans"),"Capital Adequacy":safe_div(v.get("Regulatory Capital"),v.get("Risk Weighted Assets"),"Regulatory Capital","Risk Weighted Assets"),"Cost/Income":safe_div(v.get("Operating Expenses"),income,"Operating Expenses","Net Interest Income","Non-Interest Income")}
def compute_insurance(v:dict[str,Decimal|None],prior:dict[str,Decimal|None]|None=None):
    prior=prior or {}; loss=safe_div(v.get("Claims"),v.get("Premiums"),"Claims","Premiums"); expense=safe_div(v.get("Underwriting Expenses"),v.get("Premiums"),"Underwriting Expenses","Premiums")
    combined=Result(loss.value+expense.value,None,("Claims","Underwriting Expenses","Premiums")) if loss.value is not None and expense.value is not None else Result(None,"MISSING_INPUT",("Claims","Underwriting Expenses","Premiums"))
    return {"Premium Growth":growth(v.get("Premiums"),prior.get("Premiums"),"Premiums"),"Claims":Result(v.get("Claims"),"MISSING_INPUT" if v.get("Claims") is None else None,("Claims",)),"Loss Ratio":loss,"Expense Ratio":expense,"Combined Ratio":combined,"Investment Income":Result(v.get("Investment Income"),"MISSING_INPUT" if v.get("Investment Income") is None else None,("Investment Income",)),"Reserves":Result(v.get("Insurance Reserves"),"MISSING_INPUT" if v.get("Insurance Reserves") is None else None,("Insurance Reserves",)),"ROE":safe_div(v.get("Net Income"),v.get("Average Equity"),"Net Income","Average Equity"),"Solvency":safe_div(v.get("Available Solvency Capital"),v.get("Required Solvency Capital"),"Available Solvency Capital","Required Solvency Capital")}
def compute_mining(v:dict[str,Decimal|None],prior:dict[str,Decimal|None]|None=None):
    prior=prior or {}; rg=growth(v.get("Revenue"),prior.get("Revenue")); eg=growth(v.get("EBIT"),prior.get("EBIT"))
    return {"Production":Result(v.get("Production"),"MISSING_INPUT" if v.get("Production") is None else None,("Production",)),"Unit Costs":safe_div(v.get("Production Costs"),v.get("Production"),"Production Costs","Production"),"Capital Intensity":safe_div(v.get("CapEx"),v.get("Revenue"),"CapEx","Revenue"),"Commodity Exposure":Result(v.get("Commodity Revenue Share"),"MISSING_INPUT" if v.get("Commodity Revenue Share") is None else None,("Commodity Revenue Share",)),"Operating Leverage":safe_div(eg.value,rg.value,"EBIT Growth","Revenue Growth")}
def _flag(result:Result,threshold:Decimal,direction:str):
    if result.value is None: return ("UNAVAILABLE",{"reason":result.reason,"threshold":str(threshold)})
    triggered=result.value>threshold if direction=="gt" else result.value<threshold
    return ("TRIGGERED" if triggered else "NOT_TRIGGERED",{"value":str(result.value),"threshold":str(threshold),"test":direction})
def _compatible_average(opening,closing):
    """Average compatible point-in-time observations without filling gaps."""
    if opening is None or closing is None: return None
    metadata=lambda row:(row[3],row[4],row[5],row[6],row[7])
    if metadata(opening)!=metadata(closing): return None
    if None in metadata(opening) or "UNKNOWN" in metadata(opening): return None
    opening_end=date.fromisoformat(opening[2]); closing_end=date.fromisoformat(closing[2])
    if closing_end.year-opening_end.year!=1 or (closing_end.month,closing_end.day)!=(opening_end.month,opening_end.day): return None
    return (Decimal(opening[1])+Decimal(closing[1]))/Decimal(2)


def _inputs(repo,document_id):
    rows=repo.connection.execute(
        "SELECT canonical_concept,normalized_value,period_end,currency,unit,reporting_perimeter,accounting_standard,audit_status,version_id "
        "FROM financial_observation_versions WHERE document_id=? AND superseded_by_version_id IS NULL "
        "ORDER BY period_end,version_id",(document_id,)).fetchall()
    grouped={}
    for r in rows: grouped.setdefault(r[0],[]).append(r)
    document_end=repo.connection.execute("SELECT period_end FROM financial_documents WHERE document_id=?",(document_id,)).fetchone()[0]
    current={}
    for concept,items in grouped.items():
        candidates=[row for row in items if row[2]==document_end]
        current[concept]=candidates[0] if len(candidates)==1 else None
    values={concept:(Decimal(row[1]) if row is not None else None) for concept,row in current.items()}
    ids={concept:(row[8],) for concept,row in current.items() if row is not None}
    # Period averages must be based on two explicitly reported, metadata-
    # compatible balance-sheet observations.  Do not substitute the closing
    # balance when the opening observation is absent.
    for concept,derived_name in (("Equity","Average Equity"),("Total Assets","Average Assets")):
        closing=current.get(concept)
        prior_rows=[row for row in grouped.get(concept,()) if closing is not None and row[2]<closing[2]]
        latest_prior=max((row[2] for row in prior_rows),default=None)
        prior_candidates=[row for row in prior_rows if row[2]==latest_prior]
        opening=prior_candidates[0] if len(prior_candidates)==1 else None
        average=_compatible_average(opening,closing)
        if average is not None:
            values[derived_name]=average
            ids[derived_name]=(opening[8],closing[8])
    return values,ids

def _compatible_prior_inputs(repo,doc,current_ids):
    """Return the latest genuinely comparable earlier document inputs.

    Growth is deliberately unavailable when any reporting dimension is
    unknown or differs.  Publication order is also enforced so a later-filed
    historical report cannot leak into an earlier decision point.
    """
    dimensions=(doc["currency"],doc["reporting_perimeter"],doc["accounting_standard"],doc["audit_status"])
    if None in dimensions or "UNKNOWN" in dimensions:
        return {},{}
    candidates=repo.connection.execute(
        "SELECT d.* FROM financial_documents d "
        "JOIN financial_document_identity_assignments a USING(document_id) "
        "JOIN financial_document_entity_checks c USING(document_id) "
        "WHERE d.issuer_id=? AND d.period_end<? AND d.publication_date<=? "
        "AND d.currency=? AND d.reporting_perimeter=? "
        "AND d.accounting_standard=? AND d.audit_status=? "
        "AND a.assignment_status='VERIFIED' AND c.validation_status='MATCHED' "
        "ORDER BY d.period_end DESC,d.publication_date DESC,d.document_id",
        (doc["issuer_id"],doc["period_end"],doc["publication_date"],*dimensions),
    ).fetchall()
    for prior_doc in candidates:
        current_start=date.fromisoformat(doc["period_start"])
        current_end=date.fromisoformat(doc["period_end"])
        prior_start=date.fromisoformat(prior_doc["period_start"])
        prior_end=date.fromisoformat(prior_doc["period_end"])
        if current_start.year-prior_start.year!=1 or current_end.year-prior_end.year!=1:
            continue
        if (current_start.month,current_start.day,current_end.month,current_end.day)!=(prior_start.month,prior_start.day,prior_end.month,prior_end.day):
            continue
        prior_values,prior_ids=_inputs(repo,prior_doc["document_id"])
        compatible_values={}; compatible_ids={}
        for concept,value in prior_values.items():
            if concept not in current_ids or concept not in prior_ids:
                continue
            def metadata(version_id):
                return tuple(repo.connection.execute(
                    "SELECT currency,unit,reporting_perimeter,accounting_standard,audit_status "
                    "FROM financial_observation_versions WHERE version_id=?",(version_id,)
                ).fetchone())
            current_metadata={metadata(version_id) for version_id in current_ids[concept]}
            prior_metadata={metadata(version_id) for version_id in prior_ids[concept]}
            if len(current_metadata)==1 and current_metadata==prior_metadata and None not in next(iter(current_metadata)) and "UNKNOWN" not in next(iter(current_metadata)):
                compatible_values[concept]=value; compatible_ids[concept]=prior_ids[concept]
        return compatible_values,compatible_ids
    return {},{}
def _generic_unavailable(names,reason): return {n:Result(None,reason) for n in names}
def calculate_document(repo:Repository,document_id:str):
    doc=repo.connection.execute("SELECT d.*,i.sector FROM financial_documents d JOIN issuers i USING(issuer_id) JOIN financial_document_identity_assignments a USING(document_id) WHERE document_id=? AND a.assignment_status='VERIFIED'",(document_id,)).fetchone()
    if not doc: raise ValueError("unknown document")
    engine=route_sector(doc["source_url"],doc["sector"]); values,ids=_inputs(repo,document_id)
    prior,prior_ids=_compatible_prior_inputs(repo,doc,ids)
    if engine=="GENERAL": results=compute_general(values,prior)
    elif engine=="BANK": results=compute_bank(values,prior)
    elif engine=="INSURANCE": results=compute_insurance(values,prior)
    else: results=compute_mining(values,prior)
    quality,flags=compute_quality(values,prior)
    # Growth inputs refer to both periods; retain both sides of the lineage.
    combined_ids={key:tuple(dict.fromkeys((*ids.get(key,()),*prior_ids.get(key,())))) for key in set(ids)|set(prior_ids)}
    for name,result in {**results,**quality}.items():
        obs=[oid for concept in result.inputs for oid in combined_ids.get(concept,())]
        mid=stable_id("metric",f"{document_id}:{name}:CURRENT:{FORMULA_VERSION}")
        ratio=name not in {"Net Debt","Free Cash Flow","Assets","Loans","Deposits","Equity","Net Interest Income","Claims","Investment Income","Reserves","Production","Unit Costs"}
        repo.connection.execute("INSERT INTO fundamental_metrics VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(document_id,metric_name,comparison_horizon,formula_version) DO UPDATE SET metric_value=excluded.metric_value,metric_currency=excluded.metric_currency,metric_unit=excluded.metric_unit,status=excluded.status,unavailable_reason=excluded.unavailable_reason,source_observation_ids_json=excluded.source_observation_ids_json,created_at=excluded.created_at",(mid,doc["issuer_id"],document_id,name,engine,doc["period_start"],doc["period_end"],"CURRENT",str(result.value) if result.value is not None else None,None if ratio else doc["currency"],"RATIO" if ratio else "SOURCE_UNIT_UNSPECIFIED",result.status,result.reason,FORMULA_VERSION,json.dumps(obs),json.dumps([document_id]),utc_now()))
        for version_id in obs:
            repo.connection.execute("INSERT OR IGNORE INTO analytical_observation_lineage VALUES(?,?,?,?,?)",(str(uuid.uuid4()),"fundamental_metrics",mid,version_id,utc_now()))
    for name,(status,evidence) in flags.items():
        fid=stable_id("quality-flag",f"{document_id}:{name}:{FORMULA_VERSION}")
        repo.connection.execute("INSERT INTO accounting_quality_flags VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(document_id,flag_name,formula_version) DO UPDATE SET status=excluded.status,evidence_json=excluded.evidence_json,created_at=excluded.created_at",(fid,doc["issuer_id"],document_id,name,status,json.dumps(evidence,sort_keys=True),FORMULA_VERSION,utc_now()))
    repo.connection.commit(); return engine,results,quality,flags
def calculate_all(database):
    with Repository(database) as repo:
        repo.initialize()
        bad=[r[0] for r in repo.connection.execute("SELECT document_id FROM financial_document_entity_checks WHERE validation_status='MISMATCH'")]
        if bad:
            marks=','.join('?' for _ in bad)
            repo.connection.execute(f"DELETE FROM fundamental_metrics WHERE document_id IN ({marks})",bad)
            repo.connection.execute(f"DELETE FROM accounting_quality_flags WHERE document_id IN ({marks})",bad)
            repo.connection.commit()
        documents=[r[0] for r in repo.connection.execute("SELECT d.document_id FROM financial_documents d JOIN financial_document_entity_checks c USING(document_id) JOIN financial_document_identity_assignments a USING(document_id) WHERE c.validation_status='MATCHED' AND a.assignment_status='VERIFIED'")]
        counts={"documents":len(documents),"available":0,"unavailable":0,"triggered_flags":0}
        for document_id in documents:
            _,results,quality,flags=calculate_document(repo,document_id)
            for r in list(results.values())+list(quality.values()): counts[r.status.lower()]+=1
            counts["triggered_flags"]+=sum(s=="TRIGGERED" for s,_ in flags.values())
        return counts
def query_metrics(repo:Repository,ticker:str):
    return repo.connection.execute("SELECT DISTINCT m.* FROM fundamental_metrics m JOIN securities s ON s.issuer_id=m.issuer_id JOIN identifier_history h ON h.security_id=s.security_id WHERE h.identifier_type='TICKER' AND h.identifier_value=? ORDER BY m.period_end DESC,m.metric_name",(ticker,)).fetchall()
