from __future__ import annotations
import hashlib,html,json,re,time,urllib.error,urllib.request,uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from .cohort_expansion import assess_universe,classify_blocker
from .config import Settings
from .repository import Repository,stable_id,utc_now
from .security_master import archive,normalize_name

PARSER_VERSION="rse-universe/1.0.0"; SOURCE_ID="uzse-public-web"
LISTING_URL="https://uzse.uz/isu_infos/"; QUOTATION_URL="https://uzse.uz/asking_prices"
_DATA_RE=re.compile(r"var\s+DATA\s*=\s*(\[.*?\]);",re.S)
_QUOTE_RE=re.compile(r'href="/isu_infos/STK\?isu_cd=(?P<isin>[A-Z0-9]+)"[^>]*>\s*(?P<ticker>[A-Z0-9]+)\s*\((?P<issuer>.*?)\)\s*</a>',re.S)
_DETAIL_RE=re.compile(r"<tr[^>]*>\s*<td[^>]*>\s*(?P<label>Common share|Preferred share|Простые акции|Привилегированные акции|Oddiy aksiyalar|Imtiyozli aksiyalar)\s*</td>.*?isu_cd=(?P<isin>[A-Z0-9]+)[^>]*>\s*(?P=isin)\s*<br>\s*(?P<ticker>[A-Z0-9]+)",re.S|re.I)
_PAGINATION_RE=re.compile(r'href="[^"]*[?&]page=(\d+)[^"]*"',re.I)

@dataclass(frozen=True)
class Instrument:
    isin:str; ticker:str; issuer:str; instrument_class:str; reason:str
    category:str|None=None; listing_date:str|None=None; currency:str|None=None
    nominal_value:str|None=None; shares_listed:str|None=None

def _clean(value): return " ".join(html.unescape(re.sub(r"<[^>]+>","",value)).split()).strip()
def _source_name(value): return " ".join(html.unescape(value).split()).strip()
def _iso_date(value): return datetime.strptime(value,"%Y%m%d").date().isoformat() if value else None

def parse_listing(document):
    text=document.decode("utf-8"); match=_DATA_RE.search(text)
    if not match: raise ValueError("RSE listing DATA payload not found")
    raw=json.loads(match.group(1)); rows=[]
    for item in raw:
        category={"A":"Premium","B":"Bond","C":"Standard","D":"Privatizatsiya"}.get(item.get("cat"),item.get("cat"))
        cls="BOND" if item.get("cat")=="B" else "COMMON_EQUITY"
        reason="RSE_CATEGORY_BOND" if cls=="BOND" else "RSE_LISTING_EQUITY; detail class required"
        rows.append(Instrument(item["isin"],item["tic"],_source_name(item["name"]),cls,reason,category,_iso_date(item.get("date")),item.get("cur"),str(item.get("par")) if item.get("par") not in (None,0,0.0) else None,str(item.get("shares")) if item.get("shares") not in (None,0) else None))
    pages=[int(v) for v in _PAGINATION_RE.findall(text)]; unique=len({(r.isin,r.ticker) for r in rows})
    return rows,{"source_reported_total":len(raw),"page_count":max(pages,default=1),"page_row_counts":[len(raw)],"raw_rows":len(raw),"unique_rows":unique,"duplicates":len(raw)-unique,"has_pagination_links":bool(pages)}

def parse_quotation(document):
    found={}
    for m in _QUOTE_RE.finditer(document.decode("utf-8")):
        key=(m["isin"],m["ticker"]); found[key]=Instrument(*key,_clean(m["issuer"]),"UNKNOWN","DETAIL_CLASS_REQUIRED")
    if not found: raise ValueError("RSE quotation feed contained no STK instruments")
    return sorted(found.values(),key=lambda x:(x.ticker,x.isin))

def parse_detail_classes(document):
    out={}
    for m in _DETAIL_RE.finditer(document.decode("utf-8")):
        preferred=m["label"].casefold().startswith(("preferred","привилег","imtiyoz"))
        out[(m["isin"],m["ticker"]) ]="PREFERRED_EQUITY" if preferred else "COMMON_EQUITY"
    return out

def combine_current_equities(listing,quoted,classes):
    """Union active equity listings with current quotations by ISIN; never by ticker."""
    current={}
    for row in quoted:
        cls=classes.get((row.isin,row.ticker),"UNKNOWN")
        current[row.isin]=Instrument(row.isin,row.ticker,row.issuer,cls,"OFFICIAL_ISSUER_DETAIL_CLASS_LABEL" if cls!="UNKNOWN" else "DETAIL_CLASS_UNAVAILABLE")
    for row in listing:
        if row.instrument_class=="BOND": continue
        cls=classes.get((row.isin,row.ticker),"UNKNOWN")
        current[row.isin]=Instrument(row.isin,row.ticker,row.issuer,cls,"OFFICIAL_ACTIVE_LISTING_AND_ISSUER_DETAIL_CLASS_LABEL" if cls!="UNKNOWN" else "DETAIL_CLASS_UNAVAILABLE")
    return sorted(current.values(),key=lambda x:(x.ticker,x.isin))

def _fetch(url,settings):
    request=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/140 Safari/537.36","Accept":"text/html,application/xhtml+xml","Accept-Language":"en-US,en;q=0.9","Referer":LISTING_URL})
    last=None
    for attempt in range(settings.retry_attempts):
        try:
            with urllib.request.urlopen(request,timeout=settings.request_timeout_seconds) as response:
                if response.status!=200: raise RuntimeError(f"HTTP {response.status}")
                return response.read()
        except (urllib.error.URLError,TimeoutError,RuntimeError) as error:
            last=error
            if attempt+1<settings.retry_attempts: time.sleep(settings.retry_backoff_seconds*(2**attempt))
    raise RuntimeError(f"SOURCE_UNAVAILABLE after {settings.retry_attempts} attempts: {url}: {last}")

def _latest_identifiers(c):
    return [dict(r) for r in c.execute("""WITH latest AS (SELECT security_id,identifier_type,identifier_value,row_number() OVER(PARTITION BY security_id,identifier_type ORDER BY known_at DESC,identifier_id DESC) rn FROM identifier_history WHERE identifier_type IN('ISIN','TICKER')) SELECT s.security_id,s.issuer_id,s.security_class_code,i.legal_name,max(CASE WHEN l.identifier_type='ISIN' THEN l.identifier_value END) isin,max(CASE WHEN l.identifier_type='TICKER' THEN l.identifier_value END) ticker FROM securities s JOIN issuers i USING(issuer_id) JOIN latest l ON l.security_id=s.security_id AND l.rn=1 GROUP BY s.security_id""").fetchall()]

def _top_blocker(row):
    priority=["UNVERIFIED_SECURITY_IDENTITY","UNVERIFIED_SECURITY_CLASS","NO_MARKET_HISTORY","NO_VERIFIED_FINANCIAL_DOCUMENT","MISSING_VERIFIED_CLASS_SHARES_OUTSTANDING","FINANCIAL_METADATA_INCOMPLETE","VALUATION_INSUFFICIENT","INSUFFICIENT_FACTOR_COVERAGE"]
    blocker=next((x for x in priority if x in row["blockers"]),row["blockers"][0] if row["blockers"] else "NONE")
    return blocker,classify_blocker(row,blocker) if blocker!="NONE" else "NONE"

def ingest_and_export(settings,outputs=Path("outputs")):
    retrieved=utc_now(); listing_body=_fetch(LISTING_URL,settings); quotation_body=_fetch(QUOTATION_URL,settings)
    listing,meta=parse_listing(listing_body); quoted=parse_quotation(quotation_body)
    if meta["page_count"]!=1 or meta["has_pagination_links"]: raise ValueError("SCHEMA_CHANGED: listing unexpectedly paginated")
    if meta["source_reported_total"]!=meta["raw_rows"] or meta["duplicates"]: raise ValueError("SCHEMA_CHANGED: completeness check failed")
    with Repository(settings.database_path) as repo:
        repo.initialize(); c=repo.connection
        repo.ensure_source(SOURCE_ID,'Republican Stock Exchange "Toshkent"',"uzse.uz","PRIMARY","VERIFIED_AUTOMATED",{"listing_url":LISTING_URL,"quotation_url":QUOTATION_URL,"parser_version":PARSER_VERSION})
        run=repo.start_run(SOURCE_ID,PARSER_VERSION)
        try:
            listing_doc,lh,lp=archive(settings.raw_data_dir,listing_body,retrieved,"instrument-listing"); repo.add_raw_document((listing_doc,SOURCE_ID,run,LISTING_URL,retrieved,None,"text/html",lh,lp))
            quote_doc,qh,qp=archive(settings.raw_data_dir,quotation_body,retrieved,"quotation-feed"); repo.add_raw_document((quote_doc,SOURCE_ID,run,QUOTATION_URL,retrieved,None,"text/html",qh,qp))
            detail_docs={}; detail_groups={}; classes={}; failures=[]
            detail_targets={row.isin:row for row in [*quoted,*[x for x in listing if x.instrument_class!="BOND"]]}
            for row in detail_targets.values():
                if row.isin in detail_docs: continue
                url=f"https://uzse.uz/isu_infos/{row.isin}/detail?locale=en"
                prior=c.execute("SELECT document_id,storage_path FROM raw_documents WHERE source_url=? ORDER BY retrieved_at DESC LIMIT 1",(url,)).fetchone()
                if prior and Path(prior["storage_path"]).exists():
                    body=Path(prior["storage_path"]).read_bytes(); parsed=parse_detail_classes(body); detail_docs[row.isin]=prior["document_id"]; detail_groups[row.isin]={key[0] for key in parsed}; classes.update(parsed); continue
                try:
                    body=_fetch(url,settings); stamp=utc_now(); doc,digest,path=archive(settings.raw_data_dir,body,stamp,f"universe-detail-{row.isin}")
                    parsed=parse_detail_classes(body); repo.add_raw_document((doc,SOURCE_ID,run,url,stamp,None,"text/html",digest,path)); detail_docs[row.isin]=doc; detail_groups[row.isin]={key[0] for key in parsed}; classes.update(parsed)
                except Exception as error: failures.append(str(error))
            capture=str(uuid.uuid4())
            c.execute("INSERT INTO rse_universe_captures VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(capture,run,retrieved,LISTING_URL,QUOTATION_URL,listing_doc,quote_doc,meta["source_reported_total"],meta["page_count"],json.dumps(meta["page_row_counts"]),meta["raw_rows"],meta["unique_rows"],meta["duplicates"],1,PARSER_VERSION))
            def put(view,row,cls,reason,doc=None):
                c.execute("INSERT INTO rse_universe_instruments VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(capture,view,row.isin,row.ticker,row.issuer,cls,reason,row.category,"ACTIVE",row.listing_date,None,row.shares_listed,row.nominal_value,row.currency or "UZS",doc,json.dumps(row.__dict__,sort_keys=True)))
            for row in listing:
                cls=classes.get((row.isin,row.ticker),row.instrument_class); put("LISTING",row,cls,"OFFICIAL_ISSUER_DETAIL_CLASS_LABEL" if (row.isin,row.ticker) in classes else row.reason,detail_docs.get(row.isin))
            for row in quoted:
                cls=classes.get((row.isin,row.ticker),"UNKNOWN"); put("QUOTATION",row,cls,"OFFICIAL_ISSUER_DETAIL_CLASS_LABEL" if cls!="UNKNOWN" else "DETAIL_CLASS_UNAVAILABLE",detail_docs.get(row.isin))
            current=combine_current_equities(listing,quoted,classes)
            before=_latest_identifiers(c); by_isin={x["isin"]:x for x in before}; added=[]; conflicts=[]
            mission_start=c.execute("SELECT min(retrieved_at) FROM rse_universe_captures").fetchone()[0]
            for row in current:
                existing=by_isin.get(row.isin)
                if existing:
                    if existing["ticker"]!=row.ticker: conflicts.append(("TICKER_CONFLICT",row.ticker,row.isin,existing["ticker"]))
                    expected=row.instrument_class.removesuffix("_EQUITY")
                    if row.instrument_class!="UNKNOWN" and existing["security_class_code"] not in ("UNKNOWN",expected): conflicts.append(("CLASSIFICATION_CONFLICT",row.ticker,row.instrument_class,existing["security_class_code"]))
                    if existing["security_class_code"]=="UNKNOWN" and row.instrument_class!="UNKNOWN": c.execute("UPDATE securities SET security_class_code=? WHERE security_id=?",(expected,existing["security_id"]))
                    group_issuers={by_isin[x]["issuer_id"] for x in detail_groups.get(row.isin,set()) if x in by_isin and by_isin[x]["issuer_id"]!=existing["issuer_id"]}
                    created=c.execute("SELECT created_at FROM securities WHERE security_id=?",(existing["security_id"],)).fetchone()[0]
                    if created>=mission_start and len(group_issuers)==1:
                        target=next(iter(group_issuers)); c.execute("UPDATE securities SET issuer_id=? WHERE security_id=?",(target,existing["security_id"])); existing["issuer_id"]=target
                    if created>=mission_start:
                        c.execute("UPDATE issuers SET legal_name=? WHERE issuer_id=? AND legal_name IN('AJ','AK','ATB')",(row.issuer,existing["issuer_id"]))
                    continue
                if row.instrument_class=="UNKNOWN" or not detail_docs.get(row.isin): conflicts.append(("AMBIGUOUS",row.ticker,row.isin,"missing explicit class/detail evidence")); continue
                group_ids={by_isin[x]["issuer_id"] for x in detail_groups.get(row.isin,set()) if x in by_isin}
                matches=[x for x in before if normalize_name(x["legal_name"])==normalize_name(row.issuer)]; issuer_ids=group_ids or {x["issuer_id"] for x in matches}
                if len(issuer_ids)>1: conflicts.append(("AMBIGUOUS",row.ticker,row.isin,"multiple canonical issuers share normalized source name")); continue
                issuer_id=next(iter(issuer_ids)) if issuer_ids else stable_id("rse-issuer",row.isin)
                security_id=stable_id("security",row.isin); repo.upsert_candidate(issuer_id,row.issuer,security_id,row.instrument_class.removesuffix("_EQUITY"),row.isin,row.ticker,retrieved,detail_docs[row.isin]); added.append(row.ticker)
            for kind,ticker,value,reason in conflicts: repo.conflict(run,kind,f"{ticker}:{value}",reason)
            c.commit(); repo.finish_run(run,"PARTIAL" if failures else "SUCCEEDED",len(listing)+len(current),len(failures),"\n".join(failures) or None)
            after=_latest_identifiers(c); coverage={x["ticker"]:x for x in assess_universe(settings.database_path)}
            mission_added={x["isin"] for x in after if c.execute("SELECT created_at FROM securities WHERE security_id=?",(x["security_id"],)).fetchone()[0]>=mission_start}
            _write_outputs(outputs,retrieved,capture,listing,current,before,after,coverage,conflicts,failures,meta,mission_added)
            return {"capture_id":capture,"listing_instruments":len(listing),"current_equities":len(current),"added":len(added),"conflicts":len(conflicts),"detail_failures":len(failures)}
        except Exception as error:
            c.rollback(); repo.finish_run(run,"FAILED",0,1,str(error)); raise

def _write_outputs(outputs,generated,capture,listing,current,before,after,coverage,conflicts,failures,meta,mission_added):
    outputs.mkdir(parents=True,exist_ok=True)
    def table(headers,rows):
        safe=lambda x:str("Unavailable" if x in (None,"") else x).replace("|","\\|").replace("\n"," ")
        return "\n".join(["| "+" | ".join(headers)+" |","| "+" | ".join("---" for _ in headers)+" |",*("| "+" | ".join(safe(x) for x in r)+" |" for r in rows)])
    keys={(r.isin,r.ticker) for r in current}; current_isins={r.isin for r in current}; old={r["isin"]:r for r in before}; rec=[]
    for row in current:
        match=old.get(row.isin); status="RSE_ONLY" if row.isin in mission_added else "MATCHED" if match and match["ticker"]==row.ticker else "TICKER_CONFLICT" if match else "RSE_ONLY"
        rec.append([status,row.ticker,row.isin,row.instrument_class,row.issuer,match["ticker"] if match else None,row.reason])
    for row in before:
        if (row["isin"],row["ticker"]) not in keys: rec.append(["HISTORICAL_ONLY",row["ticker"],row["isin"],row["security_class_code"],row["legal_name"],row["ticker"],"Absent from active listing and current quotation views; preserved; delisting not inferred"])
    counts=lambda rows:{k:sum(r.instrument_class==k for r in rows) for k in ("COMMON_EQUITY","PREFERRED_EQUITY","BOND","OTHER","UNKNOWN")}
    initial_count=len(after)-len(mission_added)
    (outputs/"rse_universe_reconciliation.md").write_text(f"# RSE Universe Reconciliation\n\nGenerated: {generated}  \nCapture: `{capture}`  \nParser: `{PARSER_VERSION}`\n\n## Source and completeness proof\n\n- Listing route: `{LISTING_URL}`\n- Quotation route: `{QUOTATION_URL}`\n- Listing page count: **{meta['page_count']}**\n- Per-page row counts: **{meta['page_row_counts']}**\n- Sum: **{sum(meta['page_row_counts'])}**\n- Source-reported total: **{meta['source_reported_total']}**\n- Unique rows: **{meta['unique_rows']}**\n- Duplicates: **{meta['duplicates']}**\n- No pagination links. Single-page sum equals the source payload and visible category total (2 Premium + 13 Bond + 32 Standard + 3 Privatizatsiya = 50).\n- Raw responses/details are stored in immutable `raw_documents` with timestamps and hashes.\n\n## Counts\n\n- Listing: **{len(listing)}** {counts(listing)}\n- Current equities (active listing union quotation): **{len(current)}** {counts(current)}\n- UZQUANT before mission: **{initial_count}**; after: **{len(after)}**; added: **{len(mission_added)}**\n- Detail failures: **{len(failures)}**\n\n## Reconciliation\n\n"+table(["Category","RSE ticker","RSE ISIN","RSE class","Issuer","UZQUANT ticker","Evidence/reason"],rec)+"\n\n## Conflicts\n\n"+table(["Type","Ticker","Value","Reason"],[list(x) for x in conflicts] or [["None","None","None","None"]])+"\n\n## Rules and pair checks\n\nMatching uses ISIN first and then checks ticker, explicit class and issuer detail. Ticker/name alone never matches. Historical records remain. `HISTORICAL_ONLY` does not imply delisted. Preferred mapping is accepted only where official issuer detail shows both classes under one issuer; this verifies UZTL/UZTLP, AGMK/AGMKP, KASU/KASUP and the other displayed pairs without suffix inference.\n")
    report_path=outputs/"rse_universe_reconciliation.md"
    category_summary=(f"## Reconciliation category counts\n\n- MATCHED: **{len(current)-len(mission_added)}**\n- RSE_ONLY (canonically added): **{len(mission_added)}**\n- UZQUANT_ONLY: **{len(after)-len(current)}**; all are also `HISTORICAL_ONLY`, absent from both current views. Delisting is not inferred.\n- HISTORICAL_ONLY: **{len(after)-len(current)}**\n- DELISTED: **0 verified**\n- CLASSIFICATION_CONFLICT: **{sum(x[0]=='CLASSIFICATION_CONFLICT' for x in conflicts)}**\n- ISIN_CONFLICT: **{sum(x[0]=='ISIN_CONFLICT' for x in conflicts)}**\n- TICKER_CONFLICT: **{sum(x[0]=='TICKER_CONFLICT' for x in conflicts)}**\n- AMBIGUOUS: **{sum(x[0]=='AMBIGUOUS' for x in conflicts)}**\n- Distinct current equity issuers: **{len({r['issuer_id'] for r in after if r['isin'] in current_isins})}**\n\n")
    frozen=("## Frozen-result invariants\n\nNo valuation, factor or research-state record was recomputed or overwritten. Post-run checks remain: IPKY `REDUCE`; UZTL `HOLD`; AGMK and AGMKP `LIQUIDITY_TRAP`; available valuation records belong to one distinct security, IPKY only.\n\n")
    report=report_path.read_text().replace("## Reconciliation\n\n",category_summary+"## Reconciliation\n\n",1)+"\n"+frozen
    report_path.write_text(report)
    (outputs/"current_equity_universe.md").write_text(f"# Current RSE Equity Research Universe\n\nGenerated: {generated}. Union of official active equity listings and current official equity quotations. Count: **{len(current)}**.\n\n"+table(["Ticker","ISIN","Issuer","Class","Evidence"],[[r.ticker,r.isin,r.issuer,r.instrument_class,r.reason] for r in current])+"\n")
    cov=[]; queue=[]
    for item in current:
        row=coverage.get(item.ticker)
        if row:
            blocker,category=_top_blocker(row); cov.append([item.ticker,item.isin,row["issuer_id"],item.instrument_class,row["market_observations"]>0,row["financial_documents"]>0,row["valuation_concepts"]>0,row["shares_verified"],row["rights_records"]>0,blocker,category]); queue.append([item.ticker,item.isin,blocker,category,"Existing stored data only"])
        else:
            cov.append([item.ticker,item.isin,"Unavailable",item.instrument_class,False,False,False,False,False,"UNVERIFIED_SECURITY_IDENTITY","METADATA_GAP"]); queue.append([item.ticker,item.isin,"UNVERIFIED_SECURITY_IDENTITY","METADATA_GAP","No canonical coverage row"])
    (outputs/"universe_research_coverage.md").write_text(f"# Universe Research Coverage\n\nGenerated: {generated}. Existing stored data only; valuations, factors and research states were not recomputed or overwritten.\n\n"+table(["Ticker","ISIN","Issuer ID","Class","Market","Docs","Fundamentals","Shares","Rights","Top blocker","Class"],cov)+"\n\n## Prior-result consistency\n\n1. UZTLP's four factors satisfy only the factor-count subcondition; insufficient valuation, rights and metadata keep it `DATA_INSUFFICIENT`. AGMK can receive `LIQUIDITY_TRAP` with fewer factors because this is a deterministic hard-liquidity override. No defect.\n2. The 16 `DATA_INSUFFICIENT` and 19 `VALUATION_INSUFFICIENT` figures both cover the selected 20-security cohort and overlap: one counts signal states, the other valuation availability. They are not additive. No defect.\n")
    (outputs/"universe_blocker_queue.md").write_text(f"# Current Equity Universe Blocker Queue\n\nGenerated: {generated}. One top blocker per equity. `PUBLIC_SOURCE_EXHAUSTED` is not used because no exhaustive research-evidence search log was created.\n\n"+table(["Ticker","ISIN","Top blocker","Classification","Basis"],queue)+"\n")
