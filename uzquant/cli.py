import argparse,json
from .config import Settings
from .logging_config import configure_logging
from .repository import Repository
from .security_master import ingest_security_master
from .market_data import ingest_market_data
from .financial_documents import ingest_financial_documents
from .fundamental_metrics import calculate_all,query_metrics
from .corporate_intelligence import ingest_corporate_intelligence
from .valuation import run_real_validation
from .liquidity import run_liquidity_assessments
from .scoring import score_real_universe
from .events import ingest_archived_events
from .macro import ingest_macro,export_macro_outputs
def main(argv=None):
    parser=argparse.ArgumentParser(prog="uzquant"); sub=parser.add_subparsers(dest="command",required=True)
    sub.add_parser("init-db"); sub.add_parser("update-security-master"); sub.add_parser("update-market-data"); sub.add_parser("update-financial-documents"); sub.add_parser("calculate-fundamentals"); sub.add_parser("update-corporate-intelligence"); sub.add_parser("update-events"); sub.add_parser("update-macro"); sub.add_parser("export-macro"); sub.add_parser("run-valuations"); sub.add_parser("rank-universe"); liquidity=sub.add_parser("assess-liquidity"); liquidity.add_argument("--position-shares",default="10000"); liquidity.add_argument("--participation-rate",default="0.10"); query=sub.add_parser("query-fundamentals"); query.add_argument("--ticker",required=True)
    args=parser.parse_args(argv); configure_logging(); settings=Settings.from_env()
    if args.command=="init-db":
        settings.database_path.parent.mkdir(parents=True,exist_ok=True)
        with Repository(settings.database_path) as repo: repo.initialize()
        result={"status":"initialized","database":str(settings.database_path)}
    elif args.command=="update-security-master": result=ingest_security_master(settings)
    elif args.command=="update-market-data": result=ingest_market_data(settings)
    elif args.command=="update-financial-documents": result=ingest_financial_documents(settings)
    elif args.command=="calculate-fundamentals": result={"status":"SUCCEEDED",**calculate_all(settings.database_path)}
    elif args.command=="update-corporate-intelligence": result=ingest_corporate_intelligence(settings)
    elif args.command=="update-events": result={"status":"SUCCEEDED",**ingest_archived_events(settings.database_path)}
    elif args.command=="update-macro": result=ingest_macro(settings)
    elif args.command=="export-macro": result={"status":"SUCCEEDED",**export_macro_outputs(settings.database_path,__import__('pathlib').Path("outputs/macro_history.csv"),__import__('pathlib').Path("outputs/sector_macro_mapping.csv"))}
    elif args.command=="run-valuations":
        cases=run_real_validation(settings.database_path); result={"status":"SUCCEEDED","cases":cases,"available":sum(c["status"]=="AVAILABLE" for c in cases),"insufficient":sum(c["status"]=="VALUATION_INSUFFICIENT" for c in cases)}
    elif args.command=="assess-liquidity":
        from decimal import Decimal
        cases,distribution=run_liquidity_assessments(settings.database_path,position_shares=Decimal(args.position_shares),participation_rate=Decimal(args.participation_rate)); result={"status":"SUCCEEDED","distribution":distribution,"cases":[{"ticker":c["ticker"],"state":c["result"].liquidity_state,"confidence":c["result"].liquidity_confidence,"horizon_days":str(c["result"].liquidation_horizon_days) if c["result"].liquidation_horizon_days is not None else None,"flags":c["result"].hard_flags} for c in cases]}
    elif args.command=="rank-universe":
        signals=score_real_universe(settings.database_path); result={"status":"SUCCEEDED","signals":[{"ticker":s["ticker"],"state":s["result"].state,"attractiveness":str(s["result"].attractiveness) if s["result"].attractiveness is not None else None,"confidence":str(s["result"].confidence),"gates":s["result"].gates,"signal_id":s["signal_id"]} for s in signals]}
    else:
        with Repository(settings.database_path) as repo: repo.initialize(); rows=query_metrics(repo,args.ticker)
        result={"status":"SUCCEEDED","ticker":args.ticker,"metrics":[dict(row) for row in rows]}
    print(json.dumps(result,indent=2,sort_keys=True)); return 0 if result["status"] in ("initialized","SUCCEEDED") else 2
