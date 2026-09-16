from __future__ import annotations
import hashlib,re,uuid
from dataclasses import replace
from .config import Settings
from .repository import Repository,stable_id,utc_now
from .identity import record_conflict
from .rse import PARSER_VERSION,SecurityCandidate,fetch,parse_detail_classes,parse_universe
SOURCE_ID="uzse-public-web"
REQUIRED={"AGMKP":"UZ700055K015","KASUP":"UZ702866K013","IPKY":"UZ7039920002","UZTL":"UZ7047110000","QZSM":"UZ7029000005"}
# These same-issuer relationships are verified by the accepted RSE security-master
# evidence. They are explicit evidence, not suffix or fuzzy-name inference.
VERIFIED_ISSUER_GROUPS={
 "UZ7000550002":"AGMK","UZ700055K015":"AGMK",
 "UZ7028660007":"KASU","UZ702866K013":"KASU",
}
def normalize_name(v): return re.sub(r"[^a-z0-9]+"," ",v.casefold()).strip()
def archive(raw_dir,content,retrieved_at,label):
    digest=hashlib.sha256(content).hexdigest(); path=raw_dir/"uzse"/retrieved_at[:10]/f"{label}-{digest}.html"
    path.parent.mkdir(parents=True,exist_ok=True)
    if not path.exists(): path.write_bytes(content)
    return str(uuid.uuid4()),digest,str(path)
def ingest_security_master(settings):
    settings.database_path.parent.mkdir(parents=True,exist_ok=True)
    with Repository(settings.database_path) as repo:
        repo.initialize(); repo.ensure_source(SOURCE_ID,'Republican Stock Exchange "Toshkent"',"uzse.uz","PRIMARY","PARTIAL",{"universe_url":settings.rse_universe_url,"parser_version":PARSER_VERSION})
        run=repo.start_run(SOURCE_ID,PARSER_VERSION); errors=[]
        try:
            known=utc_now(); body=fetch(settings.rse_universe_url,timeout=settings.request_timeout_seconds,attempts=settings.retry_attempts,backoff=settings.retry_backoff_seconds)
            doc,digest,path=archive(settings.raw_data_dir,body,known,"asking-prices"); repo.add_raw_document((doc,SOURCE_ID,run,settings.rse_universe_url,known,None,"text/html",digest,path))
            candidates={(c.isin,c.ticker):c for c in parse_universe(body)}
            class_map={}; issuer_by_required={c.isin:c.issuer_display_name for c in candidates.values() if c.isin in REQUIRED.values()}
            for isin in REQUIRED.values():
                url=f"https://uzse.uz/isu_infos/{isin}/detail?locale=en"
                try:
                    detail=fetch(url,timeout=settings.request_timeout_seconds,attempts=settings.retry_attempts,backoff=settings.retry_backoff_seconds)
                    stamp=utc_now(); detail_doc,h,p=archive(settings.raw_data_dir,detail,stamp,f"detail-{isin}"); repo.add_raw_document((detail_doc,SOURCE_ID,run,url,stamp,None,"text/html",h,p))
                    parsed=parse_detail_classes(detail); class_map.update(parsed)
                    issuer=issuer_by_required.get(isin)
                    if issuer:
                        for key,security_class in parsed.items(): candidates.setdefault(key,SecurityCandidate(key[0],key[1],issuer,security_class))
                except Exception as error: errors.append(f"{url}: {error}")
            candidates={k:replace(v,security_class=class_map.get(k,v.security_class)) for k,v in candidates.items()}
            seen={}; group_issuers={}
            for c in candidates.values():
                if c.ticker in seen and seen[c.ticker]!=c.isin:
                    repo.conflict(run,"TICKER",c.ticker,f"maps to {seen[c.ticker]} and {c.isin}"); continue
                seen[c.ticker]=c.isin
                existing=repo.connection.execute("SELECT s.security_id,s.issuer_id FROM identifier_history h JOIN securities s USING(security_id) WHERE h.identifier_type='ISIN' AND h.identifier_value=? ORDER BY h.known_at DESC LIMIT 1",(c.isin,)).fetchone()
                if existing:
                    security_id,issuer_id=existing
                else:
                    group=VERIFIED_ISSUER_GROUPS.get(c.isin)
                    group_existing=None
                    if group:
                        group_isins=[value for value,key in VERIFIED_ISSUER_GROUPS.items() if key==group]
                        marks=','.join('?' for _ in group_isins)
                        group_existing=repo.connection.execute(f"SELECT s.issuer_id FROM identifier_history h JOIN securities s USING(security_id) WHERE h.identifier_type='ISIN' AND h.identifier_value IN ({marks}) ORDER BY h.known_at DESC LIMIT 1",group_isins).fetchone()
                    issuer_id=group_existing[0] if group_existing else (group_issuers.setdefault(group,str(uuid.uuid4())) if group else str(uuid.uuid4()))
                    security_id=str(uuid.uuid4())
                    collisions=[r for r in repo.connection.execute("SELECT issuer_id,legal_name FROM issuers WHERE issuer_id<>?",(issuer_id,)).fetchall() if normalize_name(r[1])==normalize_name(c.issuer_display_name)]
                    if collisions:
                        record_conflict(repo,"NORMALIZED_LEGAL_NAME_COLLISION","LEGAL_NAME",normalize_name(c.issuer_display_name),known,[r[0] for r in collisions]+[issuer_id],{"action":"NO_AUTOMATIC_MERGE","source_document_id":doc})
                repo.upsert_candidate(issuer_id,c.issuer_display_name,security_id,c.security_class,c.isin,c.ticker,known,doc)
            missing=[t for t,i in REQUIRED.items() if (i,t) not in candidates]
            if missing: errors.append("required securities missing: "+", ".join(missing))
            repo.connection.commit(); counts=repo.counts(); status="SUCCEEDED" if not errors else "PARTIAL"; repo.finish_run(run,status,len(candidates),len(errors),"\n".join(errors) or None)
            return {"run_id":run,"status":status,"records_processed":len(candidates),**counts,"errors":errors,"missing_required":missing}
        except Exception as error:
            repo.connection.rollback(); repo.finish_run(run,"FAILED",0,1,str(error)); raise
