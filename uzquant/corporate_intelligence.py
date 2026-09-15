from __future__ import annotations
import hashlib,json,re
from html.parser import HTMLParser
from pathlib import Path
from .financial_documents import TableParser,parse_decimal
from .repository import Repository,stable_id,utc_now
from .rse import fetch

PARSER_VERSION="openinfo-corporate/1.0.0"; SOURCE_ID="openinfo-disclosure"
SOURCES=(
 ("AGMK","https://openinfo.uz/en/facts/32/2059","AGMK_DIVIDEND"),
 ("UZTL","https://openinfo.uz/en/facts/25/1706","UZTL_ISSUANCE"),
 ("UZTL","https://openinfo.uz/ru/facts/8/14659","UZTL_MANAGEMENT"),
 ("QZSM","https://openinfo.uz/en/facts/6/12599","QZSM_GOVERNANCE"),
 ("UZTL","https://openinfo.uz/en/reports/jsc/annual/6116","UZTL_ANNUAL"),
)
class VisibleTextParser(HTMLParser):
    def __init__(self): super().__init__(); self.tokens=[]; self.hidden=0
    def handle_starttag(self,tag,attrs):
        if tag in ("script","style"): self.hidden+=1
    def handle_endtag(self,tag):
        if tag in ("script","style"): self.hidden=max(0,self.hidden-1)
    def handle_data(self,data):
        value=" ".join(data.split())
        if value and not self.hidden:self.tokens.append(value)
def visible_tokens(content):
    p=VisibleTextParser();p.feed(content.decode("utf-8",errors="replace"));return p.tokens
def after(tokens,label,offset=1):
    try:return tokens[tokens.index(label)+offset]
    except (ValueError,IndexError):raise ValueError(f"required source label absent: {label}")
def iso(value):
    if re.fullmatch(r"\d{2}\.\d{2}\.\d{4}",value):
        d,m,y=value.split('.');return f"{y}-{m}-{d}"
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}",value):return value
    raise ValueError(f"invalid source date: {value}")
def _entity(repo,ticker):
    row=repo.connection.execute("SELECT s.security_id,s.issuer_id,s.security_class_code FROM identifier_history h JOIN securities s ON s.security_id=h.security_id WHERE h.identifier_type='TICKER' AND h.identifier_value=? ORDER BY h.known_at DESC LIMIT 1",(ticker,)).fetchone()
    if not row:raise ValueError(f"security not found: {ticker}")
    return row
def _archive(repo,run,url,content,raw_dir,published):
    digest=hashlib.sha256(content).hexdigest(); rid=stable_id("raw-corporate",f"{url}:{digest}"); raw_dir.mkdir(parents=True,exist_ok=True); path=raw_dir/f"{rid}.html"
    if not path.exists():path.write_bytes(content)
    repo.connection.execute("INSERT OR IGNORE INTO raw_documents VALUES(?,?,?,?,?,?,?,?,?)",(rid,SOURCE_ID,run,url,utc_now(),published,"text/html",digest,str(path)));return rid
def _right(repo,security,raw_id,url,disclosure,summary,provision):
    values=(stable_id("rights",f"{raw_id}:{security[0]}"),security[0],None,disclosure,None,summary,None,None,None,None,None,None,None,None,None,None,provision,summary,"LOW",raw_id,url)
    repo.connection.execute("INSERT OR IGNORE INTO security_rights VALUES("+','.join('?'*21)+")",values)
def _dividend(repo,ticker,raw_id,url,announcement,amount,pay_start=None,pay_end=None):
    security=_entity(repo,ticker); did=stable_id("dividend",f"{raw_id}:{security[0]}:REGULAR")
    repo.connection.execute("INSERT OR IGNORE INTO dividends VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(did,security[1],security[0],announcement,None,None,pay_start,pay_end,str(parse_decimal(amount)),"UZS","REGULAR",raw_id,url,"HIGH"))
    _right(repo,security,raw_id,url,announcement,f"Observed class-specific dividend declaration/accrual of {amount} UZS per share; governing voting, liquidation, conversion and cumulative rights remain unverified.","Openinfo dividend disclosure; evidence of observed treatment, not a charter provision")
def parse_agmk(repo,raw_id,url,content):
    t=visible_tokens(content); disclosure=iso(after(t,"Date of disclosure:",2)); decision=iso(after(t,"Decision date")); common=after(t,"Dividends on common shares",2); preferred=after(t,"Dividends on preferred shares",2)
    p=TableParser();p.feed(content.decode(errors="replace")); dates={r[0]:(iso(r[1]),iso(r[2])) for r in p.rows if len(r)==3 and r[0] in ("Common shares","Preferred shares")}
    _dividend(repo,"AGMK",raw_id,url,disclosure,common,*dates["Common shares"]);_dividend(repo,"AGMKP",raw_id,url,disclosure,preferred,*dates["Preferred shares"])
def parse_issuance(repo,raw_id,url,content):
    t=visible_tokens(content); disclosure=iso(after(t,"Date of disclosure:",2)); security=_entity(repo,"UZTL")
    details={"decision_date":iso(after(t,"Decision Date")),"number_of_securities":after(t,"Number of Securities"),"nominal_value":after(t,"Nominal Value of One Security"),"total_issuance_amount":after(t,"Total Issuance Amount"),"state_registration_number":after(t,"State Registration Number"),"placement_method":after(t,"Securities Placement Method")}
    effective=iso(after(t,"Date of State Registration of Issuance")); aid=stable_id("action",f"{raw_id}:NEW_ISSUANCE:{security[0]}")
    repo.connection.execute("INSERT OR IGNORE INTO corporate_actions VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(aid,security[1],security[0],"NEW_ISSUANCE",disclosure,None,effective,None,None,json.dumps(details,ensure_ascii=False,sort_keys=True),raw_id,url,"HIGH","VERIFIED"))
    gid=stable_id("governance",f"{raw_id}:DILUTION:{details['decision_date']}")
    repo.connection.execute("INSERT OR IGNORE INTO governance_events VALUES(?,?,?,?,?,?,?,?,?,?,?)",(gid,security[1],security[0],"DILUTION",details["decision_date"],disclosure,json.dumps(details,ensure_ascii=False,sort_keys=True),"HIGH","DETERMINISTIC_FACT_TYPE_25",raw_id,url))
def parse_management(repo,raw_id,url,content):
    t=visible_tokens(content); disclosure=iso(after(t,"Дата раскрытия:",2)); event_date=iso(after(t,"Дата принятия решения")); p=TableParser();p.feed(content.decode(errors="replace")); names=[r[0] for r in p.rows[2:11] if len(r)>=7]
    security=_entity(repo,"UZTL"); evidence="Appointed/terminated persons listed by source: "+"; ".join(names); eid=stable_id("governance",f"{raw_id}:MANAGEMENT_CHANGE:{event_date}")
    repo.connection.execute("INSERT OR IGNORE INTO governance_events VALUES(?,?,?,?,?,?,?,?,?,?,?)",(eid,security[1],None,"MANAGEMENT_CHANGE",event_date,disclosure,evidence,"HIGH","DETERMINISTIC_FACT_TYPE_8",raw_id,url))
def parse_qzsm(repo,raw_id,url,content):
    t=visible_tokens(content); disclosure=iso(after(t,"Date of disclosure:",2)); event_date=iso(after(t,"Date of the general meeting")); p=TableParser();p.feed(content.decode(errors="replace")); vote=next(r for r in p.rows if len(r)>=8 and r[0]=="6")
    security=_entity(repo,"QZSM"); evidence=json.dumps({"question":vote[1],"for_percent":vote[2],"against_percent":vote[4],"abstained_percent":vote[6]},ensure_ascii=False,sort_keys=True); eid=stable_id("governance",f"{raw_id}:GOVERNANCE_DECISION:{event_date}")
    repo.connection.execute("INSERT OR IGNORE INTO governance_events VALUES(?,?,?,?,?,?,?,?,?,?,?)",(eid,security[1],None,"GOVERNANCE_DECISION",event_date,disclosure,evidence,"HIGH","DETERMINISTIC_VOTE_TABLE",raw_id,url))
def parse_annual(repo,raw_id,url,content):
    t=visible_tokens(content); disclosure=iso(after(t,"Date of disclosure:",2)); _dividend(repo,"UZTL",raw_id,url,"2025-07-09",after(t,"On Common Shares (per share in sum)"));_dividend(repo,"UZTLP",raw_id,url,"2025-07-09",after(t,"On Preferred Shares (per share in sum)"))
    p=TableParser();p.feed(content.decode(errors="replace")); issuer=_entity(repo,"UZTL")[1]
    for row in p.rows:
        if len(row)==4 and "Компаниянинг 20%дан ортиқ улушига эгалик қилади" in row[2]:
            kind="STATE" if "вазирлиги" in row[0].casefold() else "OTHER"; oid=stable_id("ownership",f"{raw_id}:{issuer}:{row[0]}:{row[3]}")
            repo.connection.execute("INSERT OR IGNORE INTO ownership_positions VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",(oid,issuer,None,row[0],kind,None,">","20",iso(row[3]),disclosure,raw_id,url,"MEDIUM"))
    for name in ("Top1 concentration","Top3 concentration","Free float"):
        mid=stable_id("ownership-metric",f"{issuer}:{disclosure}:{name}");repo.connection.execute("INSERT OR IGNORE INTO ownership_metrics VALUES(?,?,?,?,?,?,?,?)",(mid,issuer,disclosure,name,None,"UNAVAILABLE","Exact ownership percentages not disclosed",json.dumps([raw_id])))
def ingest_corporate_intelligence(settings):
    handlers={"AGMK_DIVIDEND":parse_agmk,"UZTL_ISSUANCE":parse_issuance,"UZTL_MANAGEMENT":parse_management,"QZSM_GOVERNANCE":parse_qzsm,"UZTL_ANNUAL":parse_annual}
    with Repository(settings.database_path) as repo:
        repo.initialize();repo.ensure_source(SOURCE_ID,"Openinfo Corporate Disclosure Portal","openinfo.uz","PRIMARY","VERIFIED_AUTOMATED",{"format":"structured HTML","attribution_required":True});run=repo.start_run(SOURCE_ID,PARSER_VERSION);done=errors=0;failures=[]
        for ticker,url,kind in SOURCES:
            try:
                content=fetch(url,timeout=settings.request_timeout_seconds,attempts=settings.retry_attempts,backoff=settings.retry_backoff_seconds); tokens=visible_tokens(content); published=iso(after(tokens,"Date of disclosure:" if "/ru/" not in url else "Дата раскрытия:",2)); raw=_archive(repo,run,url,content,settings.raw_data_dir/"openinfo"/"corporate",published);handlers[kind](repo,raw,url,content);repo.connection.commit();done+=1
            except Exception as exc:errors+=1;failures.append(f"{kind}: {exc}")
        status="SUCCEEDED" if not errors else ("PARTIAL" if done else "FAILED");repo.finish_run(run,status,done,errors,"; ".join(failures) or None)
        counts={t:repo.connection.execute(f"SELECT count(*) FROM {t}").fetchone()[0] for t in ("corporate_actions","dividends","ownership_positions","security_rights","governance_events")}
        return {"status":status,"sources_processed":done,"errors":failures,**counts}
def ownership_as_of(repo,issuer_id,as_of):return repo.connection.execute("SELECT * FROM ownership_positions WHERE issuer_id=? AND disclosure_date<=? ORDER BY effective_date DESC",(issuer_id,as_of)).fetchall()
def rights_as_of(repo,security_id,as_of):return repo.connection.execute("SELECT * FROM security_rights WHERE security_id=? AND disclosure_date<=? ORDER BY disclosure_date DESC LIMIT 1",(security_id,as_of)).fetchone()
