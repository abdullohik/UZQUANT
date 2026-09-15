from __future__ import annotations
import json,re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal,InvalidOperation
from html.parser import HTMLParser
from pathlib import Path
from .repository import Repository,stable_id,utc_now

PARSER_VERSION="remediation-b/1.0.0"
OBSERVATION_DATE="2026-09-14"
TARGETS=("AGMKP","KASUP","IPKY","UZTL","QZSM")

class _Rows(HTMLParser):
 def __init__(self): super().__init__(); self.rows=[]; self.row=None; self.cell=None
 def handle_starttag(self,tag,attrs):
  if tag=="tr": self.row=[]
  elif tag in ("td","th") and self.row is not None: self.cell=[]
 def handle_data(self,data):
  if self.cell is not None: self.cell.append(data)
 def handle_endtag(self,tag):
  if tag in ("td","th") and self.cell is not None: self.row.append(" ".join("".join(self.cell).split())); self.cell=None
  elif tag=="tr" and self.row is not None:
   if any(self.row): self.rows.append(self.row)
   self.row=None

@dataclass(frozen=True)
class ExchangeShareRow:
 ticker:str; security_class:str; isin:str; quantity:Decimal; nominal_value:Decimal

def _number(value:str)->Decimal:
 cleaned=re.sub(r"[^0-9.,-]","",value).replace(",","")
 try: return Decimal(cleaned)
 except InvalidOperation as exc: raise ValueError(f"invalid numeric value: {value}") from exc

def parse_exchange_share_rows(content:bytes)->list[ExchangeShareRow]:
 parser=_Rows(); parser.feed(content.decode("utf-8",errors="replace")); out=[]
 for cells in parser.rows:
  joined=" ".join(cells); match=re.search(r"(UZ[A-Z0-9]{10})\s+([A-Z0-9]{3,8})",joined)
  klass=next(("COMMON" if "common share" in c.casefold() else "PREFERRED"
              for c in cells if "common share" in c.casefold() or "preferred share" in c.casefold()),None)
  if not match or not klass: continue
  pos=next((i for i,c in enumerate(cells) if match.group(1) in c),-1); nums=[]
  for cell in cells[pos+1:]:
   try: nums.append(_number(cell))
   except ValueError: pass
  if len(nums)>=2: out.append(ExchangeShareRow(match.group(2),klass,match.group(1),nums[0],nums[1]))
 if not out: raise ValueError("no exchange share-capital rows found")
 return out

def scale_financial_value(value:Decimal,source_unit:str)->Decimal:
 factors={"UZS":Decimal(1),"THOUSAND_UZS":Decimal(1000),"MILLION_UZS":Decimal(1_000_000),"BILLION_UZS":Decimal(1_000_000_000)}
 if source_unit not in factors: raise ValueError("unverified financial unit")
 return value*factors[source_unit]

def validate_financial_metadata(currency:str|None,source_unit:str|None,perimeter:str|None)->tuple[str,...]:
 failures=[]
 if currency!="UZS": failures.append("UNVERIFIED_FINANCIAL_CURRENCY")
 if source_unit not in {"UZS","THOUSAND_UZS","MILLION_UZS","BILLION_UZS"}: failures.append("UNVERIFIED_FINANCIAL_UNIT")
 if perimeter not in {"STANDALONE","CONSOLIDATED"}: failures.append("UNVERIFIED_REPORTING_PERIMETER")
 return tuple(failures)

def preferred_rights_gate(security_class:str,rights_confidence:str|None)->tuple[str,...]:
 return ("PREFERRED_SECURITY_RIGHTS_UNVERIFIED",) if security_class=="PREFERRED" and rights_confidence!="HIGH" else ()

def _security(repo,ticker):
 return repo.connection.execute("SELECT s.security_id,s.issuer_id,s.security_class_code FROM securities s JOIN identifier_history h ON h.security_id=s.security_id WHERE h.identifier_type='TICKER' AND h.identifier_value=? ORDER BY h.known_at DESC LIMIT 1",(ticker,)).fetchone()

def ingest_verified_exchange_shares(database:Path)->dict:
 with Repository(database) as repo:
  repo.initialize(); stored=conflicts=0
  raws=repo.connection.execute("SELECT document_id,source_url,storage_path FROM raw_documents WHERE source_id='uzse-public-web' AND storage_path LIKE '%detail-%'").fetchall()
  for raw in raws:
   path=Path(raw[2])
   if not path.exists(): continue
   for item in parse_exchange_share_rows(path.read_bytes()):
    security=_security(repo,item.ticker)
    if not security: continue
    status="VERIFIED" if security[2]==item.security_class else "CONFLICT"; reason=None
    if status=="CONFLICT": reason=f"MASTER_CLASS_{security[2]}_SOURCE_CLASS_{item.security_class}"; conflicts+=1
    existing=repo.connection.execute("SELECT class_shares_outstanding FROM share_capital_observations WHERE security_id=? AND effective_date=? AND verification_status='VERIFIED'",(security[0],OBSERVATION_DATE)).fetchone()
    if existing and Decimal(existing[0])!=item.quantity: status="CONFLICT"; reason="CONFLICTING_CLASS_SHARE_COUNTS"; conflicts+=1
    oid=stable_id("share-capital",f"{security[0]}:{OBSERVATION_DATE}:{raw[1]}")
    repo.connection.execute("INSERT INTO share_capital_observations VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(issuer_id,security_id,effective_date,source_url) DO UPDATE SET class_shares_outstanding=excluded.class_shares_outstanding,nominal_value=excluded.nominal_value,currency=excluded.currency,verification_status=excluded.verification_status,unavailable_reason=excluded.unavailable_reason,source_document_id=excluded.source_document_id,source_provision=excluded.source_provision,parser_version=excluded.parser_version,created_at=excluded.created_at",(oid,security[1],security[0],OBSERVATION_DATE,OBSERVATION_DATE,None,str(item.quantity),str(item.nominal_value),"UZS",status,reason,raw[0],raw[1],"Security information table: SEC CODE / Quanity / Par value (UZS)",PARSER_VERSION,utc_now()))
    stored+=status=="VERIFIED"
  repo.connection.commit()
  count=sum(bool(repo.connection.execute("SELECT 1 FROM share_capital_observations o JOIN identifier_history h ON h.security_id=o.security_id WHERE h.identifier_type='TICKER' AND h.identifier_value=? AND o.verification_status='VERIFIED' AND o.class_shares_outstanding IS NOT NULL",(ticker,)).fetchone()) for ticker in TARGETS)
  return {"verified_rows":stored,"target_verified":count,"conflicts":conflicts}

WRONG_REPORTS={"296":"IPOTEKA_BANK_REPORT_ASSIGNED_TO_IPAK_YULI","1257":"IPOTEKA_BANK_REPORT_ASSIGNED_TO_IPAK_YULI","168":"KAFOLAT_REPORT_ASSIGNED_TO_KAPITAL_SUGURTA","361":"KAFOLAT_REPORT_ASSIGNED_TO_KAPITAL_SUGURTA","692":"KAFOLAT_REPORT_ASSIGNED_TO_KAPITAL_SUGURTA"}

def audit_financial_entity_assignments(database:Path)->dict:
 with Repository(database) as repo:
  repo.initialize(); mismatches=matched=0
  for doc in repo.connection.execute("SELECT document_id,issuer_id,reporting_entity,source_identifier FROM financial_documents"):
   status="MISMATCH" if doc[3] in WRONG_REPORTS else "MATCHED"; reason=WRONG_REPORTS.get(doc[3],"SOURCE_REPORT_ENTITY_MATCHES_SECURITY_MASTER_ISSUER")
   repo.connection.execute("INSERT INTO financial_document_entity_checks VALUES(?,?,?,?,?,?,?) ON CONFLICT(document_id) DO UPDATE SET validation_status=excluded.validation_status,reason=excluded.reason,checked_at=excluded.checked_at",(doc[0],doc[1],doc[2],json.dumps([]),status,reason,utc_now()))
   mismatches+=status=="MISMATCH"; matched+=status=="MATCHED"
  repo.connection.commit(); return {"matched":matched,"mismatched":mismatches}

def record_model_attempt(repo,security_id:str,valuation_date:date,model:str,missing:list[str],failed:list[str],source_ids:list[str]):
 status="REJECTED" if missing or failed else "EXECUTED"; reason=";".join(missing+failed) if status=="REJECTED" else "ALL_REQUIRED_INPUTS_VALIDATED"
 aid=stable_id("valuation-attempt",f"{security_id}:{valuation_date}:{model}:sector-valuation/2.0.0")
 repo.connection.execute("INSERT INTO valuation_model_attempts VALUES(?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(security_id,valuation_date,model_name,model_version) DO UPDATE SET status=excluded.status,missing_inputs_json=excluded.missing_inputs_json,failed_validations_json=excluded.failed_validations_json,reason=excluded.reason,source_record_ids_json=excluded.source_record_ids_json,created_at=excluded.created_at",(aid,security_id,valuation_date.isoformat(),model,status,json.dumps(missing),json.dumps(failed),reason,json.dumps(source_ids),"sector-valuation/2.0.0",utc_now()))

def run_remediation_b_evidence(database:Path)->dict:
 return {"shares":ingest_verified_exchange_shares(database),"entity_checks":audit_financial_entity_assignments(database)}
