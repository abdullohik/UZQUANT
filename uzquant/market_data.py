import hashlib,json,uuid
from datetime import date
from .market_quality import calculate_quality
from .repository import Repository,stable_id,utc_now
from .rse import fetch,parse_daily_history
PARSER_VERSION="rse-daily-history/1.0.0"
TICKERS={"AGMK":"UZ7000550002","AGMKP":"UZ700055K015","KASU":"UZ7028660007","KASUP":"UZ702866K013","IPKY":"UZ7039920002","UZTL":"UZ7047110000","QZSM":"UZ7029000005"}
def ingest_market_data(settings,targets=None,fetcher=fetch):
    targets=targets or TICKERS
    with Repository(settings.database_path) as repo:
        repo.initialize(); run=str(uuid.uuid4()); started=utc_now()
        repo.connection.execute("INSERT INTO market_ingestion_runs(market_run_id,source_id,started_at,status,securities_requested,parser_version) VALUES(?,'uzse-public-web',?,'RUNNING',?,?)",(run,started,len(targets),PARSER_VERSION)); repo.connection.commit()
        repo.connection.execute("INSERT INTO ingestion_runs(run_id,source_id,started_at,status,parser_version) VALUES(?,'uzse-public-web',?,'RUNNING',?)",(run,started,PARSER_VERSION)); repo.connection.commit()
        successes=records=0; errors=[]
        for ticker,isin in targets.items():
            security_id=None
            url=f"https://uzse.uz/isu_infos/STK?isu_cd={isin}"
            try:
                body=fetcher(url,timeout=settings.request_timeout_seconds,attempts=settings.retry_attempts,backoff=settings.retry_backoff_seconds); stamp=utc_now()
                digest=hashlib.sha256(body).hexdigest(); path=settings.raw_data_dir/"uzse"/stamp[:10]/f"market-{isin}-{digest}.html"; path.parent.mkdir(parents=True,exist_ok=True)
                if not path.exists(): path.write_bytes(body)
                doc=str(uuid.uuid4()); repo.add_raw_document((doc,"uzse-public-web",run,url,stamp,None,"text/html",digest,str(path)))
                security=repo.connection.execute("SELECT security_id FROM identifier_history WHERE identifier_type='ISIN' AND identifier_value=? ORDER BY known_at DESC LIMIT 1",(isin,)).fetchone()
                if not security: raise ValueError(f"security master has no ISIN {isin}")
                security_id=security[0]; rows=parse_daily_history(body); seen=set()
                for row in rows:
                    payload=json.dumps(row,sort_keys=True); payload_hash=hashlib.sha256(payload.encode()).hexdigest(); key=(security_id,row["trade_date"],payload_hash)
                    if key in seen:
                        repo.connection.execute("INSERT OR IGNORE INTO market_quality_flags VALUES(?,?,?,?,?,?,?,?)",(str(uuid.uuid4()),security_id,row["trade_date"],"DUPLICATE_RECORD","WARNING","Duplicate row in response",run,stamp)); continue
                    seen.add(key); observation=stable_id("market-observation",":".join(key))
                    status="NO_TRADE_PLACEHOLDER" if float(row["share_volume"])==0 else "TRADE_REPORTED"
                    cursor=repo.connection.execute("""INSERT OR IGNORE INTO market_observations(observation_id,security_id,trade_date,source_timestamp,timezone,open,high,low,close,share_volume,currency,source_id,document_id,market_run_id,series_type,parser_version,payload_hash,first_seen_at,last_seen_at,observation_status) VALUES(?,?,?,?,?,?,?,?,?,?,?,'uzse-public-web',?,?,'RAW_OBSERVED',?,?,?,?,?)""",(observation,security_id,row["trade_date"],stamp,"Asia/Tashkent",row["open"],row["high"],row["low"],row["close"],row["share_volume"],"UZS",doc,run,PARSER_VERSION,payload_hash,stamp,stamp,status))
                    if cursor.rowcount==0: repo.connection.execute("UPDATE market_observations SET last_seen_at=? WHERE observation_id=?",(stamp,observation))
                stored=[dict(r) for r in repo.connection.execute("SELECT trade_date,close,share_volume,turnover_value,trade_count,observation_status FROM market_observations WHERE security_id=? AND series_type='RAW_OBSERVED'",(security_id,))]
                quality=calculate_quality(stored,as_of=date.today())
                for trade_date,kind,severity,details in quality["flags"]:
                    repo.connection.execute("INSERT OR IGNORE INTO market_quality_flags VALUES(?,?,?,?,?,?,?,?)",(str(uuid.uuid4()),security_id,trade_date,kind,severity,details,run,stamp))
                repo.connection.execute("""INSERT INTO market_quality_metrics VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",(str(uuid.uuid4()),security_id,date.today().isoformat(),quality["observation_count"],quality["trading_frequency"],quality["zero_trade_day_ratio"],quality["average_daily_share_volume"],quality["median_daily_share_volume"],quality["average_daily_trading_value"],quality["median_daily_trading_value"],quality["average_trade_count"],quality["median_trade_count"],quality["days_since_last_trade"],quality["calendar_basis"],run,stamp))
                records+=len(rows); successes+=1
            except Exception as error:
                errors.append(f"{ticker}: {error}")
                if security_id and "impossible" in str(error).lower():
                    repo.connection.execute("INSERT OR IGNORE INTO market_quality_flags VALUES(?,?,?,?,?,?,?,?)",(str(uuid.uuid4()),security_id,None,"IMPOSSIBLE_PRICE","CRITICAL",str(error),run,utc_now()))
            repo.connection.commit()
        status="SUCCEEDED" if not errors else ("PARTIAL" if successes else "FAILED")
        repo.connection.execute("UPDATE market_ingestion_runs SET finished_at=?,status=?,securities_succeeded=?,records_processed=?,errors=?,error_details=? WHERE market_run_id=?",(utc_now(),status,successes,records,len(errors),"\n".join(errors) or None,run)); repo.connection.commit()
        repo.finish_run(run,status,records,len(errors),"\n".join(errors) or None)
        return {"run_id":run,"status":status,"securities_requested":len(targets),"securities_succeeded":successes,"records_processed":records,"errors":errors}
