import argparse,json
from .config import Settings
from .logging_config import configure_logging
from .repository import Repository
from .security_master import ingest_security_master
from .market_data import ingest_market_data
from .financial_documents import ingest_financial_documents
def main(argv=None):
    parser=argparse.ArgumentParser(prog="uzquant"); sub=parser.add_subparsers(dest="command",required=True)
    sub.add_parser("init-db"); sub.add_parser("update-security-master"); sub.add_parser("update-market-data"); sub.add_parser("update-financial-documents")
    args=parser.parse_args(argv); configure_logging(); settings=Settings.from_env()
    if args.command=="init-db":
        settings.database_path.parent.mkdir(parents=True,exist_ok=True)
        with Repository(settings.database_path) as repo: repo.initialize()
        result={"status":"initialized","database":str(settings.database_path)}
    elif args.command=="update-security-master": result=ingest_security_master(settings)
    elif args.command=="update-market-data": result=ingest_market_data(settings)
    else: result=ingest_financial_documents(settings)
    print(json.dumps(result,indent=2,sort_keys=True)); return 0 if result["status"] in ("initialized","SUCCEEDED") else 2
