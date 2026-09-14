from __future__ import annotations
import hashlib,json,re,uuid
from dataclasses import dataclass
from datetime import date,datetime,timezone
from decimal import Decimal,InvalidOperation
from html.parser import HTMLParser
from pathlib import Path
from .financial_taxonomy import map_concept
from .repository import Repository,stable_id,utc_now
from .rse import fetch

PARSER_VERSION="openinfo-financial-html/1.0.0"
SOURCE_ID="openinfo-disclosure"
REPORTS=(
 ("AGMK","jsc/quarter/18364","2026-01-01","2026-03-31","2026-05-01"),
 ("KASUP","insurance/quarter/361","2023-04-01","2023-06-30","2023-07-26"),
 ("IPKY","bank/quarter/1257","2026-01-01","2026-03-31","2026-04-27"),
 ("UZTL","jsc/annual/6116","2025-01-01","2025-12-31","2026-07-10"),
 ("QZSM","jsc/quarter/18437","2026-01-01","2026-03-31","2026-05-13"),
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
def _issuer_for_ticker(repo,ticker):
    row=repo.connection.execute("SELECT s.issuer_id,i.legal_name FROM identifier_history h JOIN securities s ON s.security_id=h.security_id JOIN issuers i ON i.issuer_id=s.issuer_id WHERE h.identifier_type='TICKER' AND h.identifier_value=? ORDER BY h.known_at DESC LIMIT 1",(ticker,)).fetchone()
    if not row: raise ValueError(f"ticker absent from approved security master: {ticker}")
    return row
def _save(repo,run_id,ticker,path_bits,period_start,period_end,published,content,raw_dir,url):
    issuer=_issuer_for_ticker(repo,ticker); digest=hashlib.sha256(content).hexdigest(); source_identifier=path_bits.rsplit('/',1)[-1]
    raw_id=stable_id("raw-financial",f"{url}:{digest}"); document_id=stable_id("financial-document",f"{SOURCE_ID}:{source_identifier}:{digest}")
    raw_dir.mkdir(parents=True,exist_ok=True); storage=raw_dir/f"{raw_id}.html"
    if not storage.exists(): storage.write_bytes(content)
    repo.connection.execute("INSERT OR IGNORE INTO raw_documents VALUES(?,?,?,?,?,?,?,?,?)",(raw_id,SOURCE_ID,run_id,url,utc_now(),published,"text/html",digest,str(storage)))
    prior=repo.connection.execute("SELECT document_id FROM financial_documents WHERE source_id=? AND source_identifier=? AND content_hash<>? ORDER BY retrieved_at DESC LIMIT 1",(SOURCE_ID,source_identifier,digest)).fetchone()
    revision_status,revises=("REVISED",prior[0]) if prior else ("ORIGINAL",None)
    repo.connection.execute("INSERT OR IGNORE INTO financial_documents VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(document_id,issuer[0],raw_id,issuer[1],"UNKNOWN",period_start,period_end,published,None,"ANNUAL" if "/annual/" in path_bits else "QUARTERLY","HTML","UNKNOWN","UNKNOWN",None,SOURCE_ID,url,source_identifier,utc_now(),digest,PARSER_VERSION,revision_status,revises))
    rows=parse_statement_rows(content); normalized=0
    for row in rows:
        rid=stable_id("financial-raw",f"{document_id}:{row.location}")
        repo.connection.execute("INSERT OR IGNORE INTO financial_raw_values VALUES(?,?,?,?,?,?,?,?,?)",(rid,document_id,row.statement_type,row.label,row.row_code,row.raw_value,"CURRENT_OR_PERIOD_END",row.location,"STRUCTURED_HTML"))
        concept=map_concept(row.label); number=parse_decimal(row.raw_value)
        if concept and number is not None:
            oid=stable_id("financial-observation",f"{document_id}:{concept}:{row.location}")
            repo.connection.execute("INSERT OR IGNORE INTO financial_observations VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(oid,document_id,issuer[0],row.statement_type,concept,period_start,period_end,row.raw_value,str(number),None,"SOURCE_UNIT_UNSPECIFIED","AS_REPORTED",row.location,"STRUCTURED_HTML","HIGH","REPORTED")); normalized+=1
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
    return repo.connection.execute("SELECT o.*,d.publication_date FROM financial_observations o JOIN financial_documents d USING(document_id) WHERE o.issuer_id=? AND o.canonical_concept=? AND d.publication_date<=? ORDER BY o.period_end DESC,d.publication_date DESC LIMIT 1",(issuer_id,concept,as_of)).fetchone()
def ingest_financial_documents(settings):
    with Repository(settings.database_path) as repo:
        repo.initialize(); repo.ensure_source(SOURCE_ID,"Openinfo Corporate Disclosure Portal","openinfo.uz","PRIMARY","VERIFIED_AUTOMATED",{"format":"structured HTML","attribution_required":True}); run=repo.start_run(SOURCE_ID,PARSER_VERSION); docs=raw=normalized=errors=0; failures=[]
        for ticker,bits,start,end,published in REPORTS:
            url=f"https://openinfo.uz/en/reports/{bits}"
            try:
                content=fetch(url,timeout=settings.request_timeout_seconds,attempts=settings.retry_attempts,backoff=settings.retry_backoff_seconds)
                r,n=_save(repo,run,ticker,bits,start,end,published,content,settings.raw_data_dir/"openinfo"/ticker,url); raw+=r; normalized+=n; docs+=1; repo.connection.commit()
            except Exception as exc: errors+=1; failures.append(f"{ticker}: {exc}")
        status="SUCCEEDED" if not errors else ("PARTIAL" if docs else "FAILED"); repo.finish_run(run,status,docs,errors,"; ".join(failures) or None)
        return {"status":status,"documents":docs,"raw_values":raw,"normalized_observations":normalized,"errors":failures}
