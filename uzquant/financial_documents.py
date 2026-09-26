from __future__ import annotations
import hashlib,json,re,uuid
from dataclasses import dataclass
from datetime import date,datetime,timezone
from decimal import Decimal,InvalidOperation
from html.parser import HTMLParser
from pathlib import Path
from .financial_taxonomy import map_source_concept
from .financial_lineage import append_version
from .repository import Repository,stable_id,utc_now
from .identity import RESOLVED,record_conflict,resolve_security_pair
from .operations import enforce_source_schema
from .rse import fetch

PARSER_VERSION="openinfo-financial-html/1.1.0"
SOURCE_ID="openinfo-disclosure"
REPORT_ISINS={"AGMK":"UZ7000550002","KASUP":"UZ702866K013","IPKY":"UZ7039920002","UZTL":"UZ7047110000","QZSM":"UZ7029000005"}
REPORTS=(
 # ticker, portal path, period, publication, perimeter, standard, audit, currency, unit
 ("AGMK","jsc/annual/5218","2023-01-01","2023-12-31","2024-09-25","UNKNOWN","LOCAL_STATUTORY","AUDITED","UZS","SOURCE_UNIT_UNSPECIFIED"),
 ("AGMK","jsc/quarter/18364","2026-01-01","2026-03-31","2026-05-01","UNKNOWN","LOCAL_STATUTORY","UNAUDITED","UZS","SOURCE_UNIT_UNSPECIFIED"),
 ("KASUP","insurance/annual/39","2017-01-01","2017-12-31","2018-07-13","UNKNOWN","LOCAL_STATUTORY","AUDITED","UZS","SOURCE_UNIT_UNSPECIFIED"),
 ("KASUP","insurance/annual/73","2021-01-01","2021-12-31","2022-06-13","UNKNOWN","LOCAL_STATUTORY","AUDITED","UZS","SOURCE_UNIT_UNSPECIFIED"),
 ("KASUP","insurance/annual/208","2023-01-01","2023-12-31","2024-07-08","UNKNOWN","LOCAL_STATUTORY","AUDITED","UZS","SOURCE_UNIT_UNSPECIFIED"),
 ("KASUP","insurance/quarter/650","2025-01-01","2025-06-30","2025-07-31","UNKNOWN","LOCAL_STATUTORY","UNAUDITED","UZS","SOURCE_UNIT_UNSPECIFIED"),
 ("IPKY","bank/annual/289","2022-01-01","2022-12-31","2023-06-27","UNKNOWN","LOCAL_STATUTORY","AUDITED","UZS","SOURCE_UNIT_UNSPECIFIED"),
 ("IPKY","bank/annual/354","2023-01-01","2023-12-31","2024-12-11","UNKNOWN","LOCAL_STATUTORY","AUDITED","UZS","SOURCE_UNIT_UNSPECIFIED"),
 ("IPKY","bank/annual/387","2024-01-01","2024-12-31","2025-07-11","UNKNOWN","LOCAL_STATUTORY","AUDITED","UZS","SOURCE_UNIT_UNSPECIFIED"),
 ("UZTL","jsc/annual/5548","2024-01-01","2024-12-31","2025-07-09","UNKNOWN","LOCAL_STATUTORY","AUDITED","UZS","SOURCE_UNIT_UNSPECIFIED"),
 ("UZTL","jsc/annual/6116","2025-01-01","2025-12-31","2026-07-10","UNKNOWN","LOCAL_STATUTORY","AUDITED","UZS","SOURCE_UNIT_UNSPECIFIED"),
 ("QZSM","jsc/annual/5176","2023-01-01","2023-12-31","2024-07-24","UNKNOWN","LOCAL_STATUTORY","AUDITED","UZS","SOURCE_UNIT_UNSPECIFIED"),
 ("QZSM","jsc/annual/5408","2024-01-01","2024-12-31","2025-06-26","UNKNOWN","LOCAL_STATUTORY","AUDITED","UZS","SOURCE_UNIT_UNSPECIFIED"),
 ("QZSM","jsc/quarter/18437","2026-01-01","2026-03-31","2026-05-13","UNKNOWN","LOCAL_STATUTORY","UNAUDITED","UZS","SOURCE_UNIT_UNSPECIFIED"),
)
@dataclass(frozen=True)
class ParsedRow:
    statement_type:str; label:str; row_code:str|None; raw_value:str; location:str
class TableParser(HTMLParser):
    def __init__(self): super().__init__(); self.rows=[]; self.row=None; self.cell=None
    def handle_starttag(self,tag,attrs):
        if tag=="tr": self.row=[]
        elif tag in ("td","th") and self.row is not None: self.cell=[]
    def handle_data(self,data):
        if self.cell is not None: self.cell.append(data)
    def handle_endtag(self,tag):
        if tag in ("td","th") and self.cell is not None:
            self.row.append(" ".join("".join(self.cell).split())); self.cell=None
        elif tag=="tr" and self.row is not None:
            if any(self.row): self.rows.append(self.row)
            self.row=None
def parse_decimal(raw:str)->Decimal|None:
    value=raw.strip().replace("\u00a0","").replace(" ","")
    if value in ("","-"): return None
    if value.startswith("(") and value.endswith(")"): value="-"+value[1:-1]
    if "," in value and "." in value: value=value.replace(".","").replace(",",".")
    elif "," in value: value=value.replace(",",".")
    value=value.replace("%","")
    try: return Decimal(value)
    except InvalidOperation: return None
def parse_statement_rows(content:bytes)->list[ParsedRow]:
    parser=TableParser(); parser.feed(content.decode("utf-8",errors="replace")); out=[]; statement="UNKNOWN"
    for index,cells in enumerate(parser.rows):
        joined=" ".join(cells).casefold()
        if "at the beginning of the reporting period" in joined: statement="BALANCE_SHEET"; continue
        if "current reporting period" in joined or ("income" in joined and "expense" in joined): statement="INCOME_STATEMENT"; continue
        if len(cells)<3: continue
        code=cells[1] if re.fullmatch(r"\d{3}",cells[1]) else None
        start=2 if code else 1
        numeric=[(i,v,parse_decimal(v)) for i,v in enumerate(cells[start:],start) if parse_decimal(v) is not None]
        if not numeric: continue
        # Balance sheets report beginning/end. Income tables report prior/current
        # income/expense pairs; choose the current pair's non-zero reported cell.
        if statement=="INCOME_STATEMENT" and len(numeric)>=2:
            candidates=numeric[-2:]; chosen=next((x for x in candidates if x[2]!=0),candidates[-1])
        else: chosen=numeric[-1]
        out.append(ParsedRow(statement,cells[0],code,chosen[1],f"html:row[{index}]/cell[{chosen[0]}]"))
    if not out: raise ValueError("no structured financial rows found")
    return out
def _save(repo,run_id,ticker,path_bits,period_start,period_end,published,perimeter,standard,audit,currency,unit,content,raw_dir,url):
    digest=hashlib.sha256(content).hexdigest(); source_identifier=path_bits.rsplit('/',1)[-1]
    raw_id=stable_id("raw-financial",f"{url}:{digest}"); document_id=stable_id("financial-document",f"{SOURCE_ID}:{source_identifier}:{digest}")
    raw_dir.mkdir(parents=True,exist_ok=True); storage=raw_dir/f"{raw_id}.html"
    if not storage.exists(): storage.write_bytes(content)
    repo.connection.execute("INSERT OR IGNORE INTO raw_documents VALUES(?,?,?,?,?,?,?,?,?)",(raw_id,SOURCE_ID,run_id,url,utc_now(),published,"text/html",digest,str(storage)))
    try: rows=parse_statement_rows(content); observed={"html_table","financial_rows","numeric_value"}
    except ValueError: rows=[]; observed={"html_table"} if b"<tr" in content.lower() else set()
    enforce_source_schema(repo,"financial_documents",SOURCE_ID,PARSER_VERSION,raw_id,{"html_table","financial_rows","numeric_value"},observed)
    resolution=resolve_security_pair(repo,ticker,REPORT_ISINS[ticker],published,utc_now())
    if resolution.status!=RESOLVED:
        conflict=record_conflict(repo,"FINANCIAL_DOCUMENT_IDENTITY_FAILURE","TICKER_ISIN",f"{ticker}|{REPORT_ISINS[ticker]}",published,[],{"status":resolution.status,"reason":resolution.reason,"source_identifier":source_identifier})
        raise ValueError(f"financial document quarantined: {resolution.status} ({conflict})")
    issuer=repo.connection.execute("SELECT issuer_id,legal_name FROM issuers WHERE issuer_id=?",(resolution.issuer_id,)).fetchone()
    prior=repo.connection.execute("SELECT document_id FROM financial_documents WHERE source_id=? AND source_identifier=? AND content_hash<>? ORDER BY retrieved_at DESC LIMIT 1",(SOURCE_ID,source_identifier,digest)).fetchone()
    revision_status,revises=("REVISED",prior[0]) if prior else ("ORIGINAL",None)
    repo.connection.execute("INSERT INTO financial_documents VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(source_id,source_identifier,content_hash) DO UPDATE SET reporting_perimeter=excluded.reporting_perimeter,period_start=excluded.period_start,period_end=excluded.period_end,publication_date=excluded.publication_date,accounting_standard=excluded.accounting_standard,audit_status=excluded.audit_status,currency=excluded.currency,parser_version=excluded.parser_version",(document_id,issuer[0],raw_id,issuer[1],perimeter,period_start,period_end,published,None,"ANNUAL" if "/annual/" in path_bits else "QUARTERLY","HTML",standard,audit,currency,SOURCE_ID,url,source_identifier,utc_now(),digest,PARSER_VERSION,revision_status,revises))
    evidence=json.dumps({"ticker":ticker,"isin":REPORT_ISINS[ticker],"evidence_ids":resolution.evidence_ids,"source_identifier":source_identifier},sort_keys=True)
    repo.connection.execute("INSERT INTO financial_document_identity_assignments VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(document_id) DO UPDATE SET canonical_issuer_id=excluded.canonical_issuer_id,security_id=excluded.security_id,publication_date=excluded.publication_date,assignment_status=excluded.assignment_status,assignment_method=excluded.assignment_method,evidence_json=excluded.evidence_json,assigned_at=excluded.assigned_at",(str(uuid.uuid4()),document_id,resolution.canonical_issuer_id,resolution.security_id,published,"VERIFIED","EFFECTIVE_DATED_TICKER_AND_ISIN",evidence,utc_now()))
    matched=True
    entity_status="MATCHED"
    entity_reason="EFFECTIVE_DATED_TICKER_AND_ISIN_AGREE"
    repo.connection.execute("INSERT INTO financial_document_entity_checks VALUES(?,?,?,?,?,?,?) ON CONFLICT(document_id) DO UPDATE SET validation_status=excluded.validation_status,reason=excluded.reason,checked_at=excluded.checked_at",(document_id,issuer[0],issuer[1],json.dumps([ticker]),entity_status,entity_reason,utc_now()))
    if not matched:
        return 0,0
    normalized=0
    for row in rows:
        rid=stable_id("financial-raw",f"{document_id}:{row.location}")
        repo.connection.execute("INSERT OR IGNORE INTO financial_raw_values VALUES(?,?,?,?,?,?,?,?,?)",(rid,document_id,row.statement_type,row.label,row.row_code,row.raw_value,"CURRENT_OR_PERIOD_END",row.location,"STRUCTURED_HTML"))
        concept=map_source_concept(row.label,row.row_code,row.statement_type); number=parse_decimal(row.raw_value)
        if concept and number is not None:
            oid=stable_id("financial-observation",f"{document_id}:{concept}:{row.location}")
            repo.connection.execute("INSERT OR IGNORE INTO financial_observations VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(oid,document_id,issuer[0],row.statement_type,concept,period_start,period_end,row.raw_value,str(number),currency,unit,"AS_REPORTED",row.location,"STRUCTURED_HTML","HIGH","REPORTED"))
            append_version(repo,oid,document_id,issuer[0],row.statement_type,concept,period_start,period_end,row.raw_value,str(number),currency,unit,row.location,"STRUCTURED_HTML","HIGH","REPORTED",PARSER_VERSION); normalized+=1
    _validate(repo,document_id)
    return len(rows),normalized
def _validate(repo,document_id):
    doc=repo.connection.execute("SELECT * FROM financial_documents WHERE document_id=?",(document_id,)).fetchone()
    def issue(kind,severity,details):
        repo.connection.execute("INSERT OR IGNORE INTO financial_validation_issues VALUES(?,?,?,?,?,?)",(stable_id("validation",f"{document_id}:{kind}"),document_id,kind,severity,json.dumps(details,sort_keys=True),utc_now()))
    if doc["period_start"] and doc["period_start"]>doc["period_end"]: issue("PERIOD_MISMATCH","ERROR",{"start":doc["period_start"],"end":doc["period_end"]})
    if doc["reporting_perimeter"]=="UNKNOWN": issue("REPORTING_PERIMETER_UNKNOWN","WARNING",{})
    if doc["currency"] is None: issue("CURRENCY_UNSPECIFIED","WARNING",{})
    if repo.connection.execute("SELECT count(*) FROM financial_documents WHERE source_id=? AND source_identifier=?",(doc["source_id"],doc["source_identifier"])).fetchone()[0]>1: issue("DUPLICATE_OR_REVISED_REPORT","WARNING",{})
    overlaps=repo.connection.execute("SELECT count(*) FROM financial_documents WHERE issuer_id=? AND document_type=? AND document_id<>? AND period_start<=? AND period_end>=?",(doc["issuer_id"],doc["document_type"],document_id,doc["period_end"],doc["period_start"] or doc["period_end"])).fetchone()[0]
    if overlaps: issue("OVERLAPPING_PERIOD","WARNING",{"other_documents":overlaps})
    values={r[0]:Decimal(r[1]) for r in repo.connection.execute("SELECT canonical_concept,normalized_value FROM financial_observations WHERE document_id=?",(document_id,))}
    for concept in ("Total Assets","Total Liabilities","Equity"):
        if concept in values and values[concept]<0: issue("SIGN_ERROR","ERROR",{"concept":concept,"value":str(values[concept])})
    if all(k in values for k in ("Total Assets","Total Liabilities","Equity")):
        delta=abs(values["Total Assets"]-values["Total Liabilities"]-values["Equity"]); tolerance=max(Decimal(1),abs(values["Total Assets"])*Decimal("0.001"))
        if delta>tolerance:
            issue("BALANCE_IDENTITY","ERROR",{"delta":str(delta),"tolerance":str(tolerance)})
def point_in_time(repo,issuer_id,concept,as_of):
    return repo.connection.execute("SELECT o.* FROM financial_observation_versions o JOIN financial_document_identity_assignments a USING(document_id) WHERE o.issuer_id=? AND o.canonical_concept=? AND o.publication_date<=? AND o.knowledge_date<=? AND a.assignment_status='VERIFIED' ORDER BY o.period_end DESC,o.publication_date DESC,o.knowledge_date DESC LIMIT 1",(issuer_id,concept,as_of,as_of)).fetchone()
def ingest_financial_documents(settings):
    with Repository(settings.database_path) as repo:
        repo.initialize(); repo.ensure_source(SOURCE_ID,"Openinfo Corporate Disclosure Portal","openinfo.uz","PRIMARY","VERIFIED_AUTOMATED",{"format":"structured HTML","attribution_required":True}); run=repo.start_run(SOURCE_ID,PARSER_VERSION); docs=raw=normalized=errors=0; failures=[]
        for ticker,bits,start,end,published,perimeter,standard,audit,currency,unit in REPORTS:
            url=f"https://openinfo.uz/en/reports/{bits}"
            try:
                content=fetch(url,timeout=settings.request_timeout_seconds,attempts=settings.retry_attempts,backoff=settings.retry_backoff_seconds)
                r,n=_save(repo,run,ticker,bits,start,end,published,perimeter,standard,audit,currency,unit,content,settings.raw_data_dir/"openinfo"/ticker,url); raw+=r; normalized+=n; docs+=1; repo.connection.commit()
            except Exception as exc: errors+=1; failures.append(f"{ticker}: {exc}")
        status="SUCCEEDED" if not errors else ("PARTIAL" if docs else "FAILED"); repo.finish_run(run,status,docs,errors,"; ".join(failures) or None)
        return {"status":status,"documents":docs,"raw_values":raw,"normalized_observations":normalized,"errors":failures}
