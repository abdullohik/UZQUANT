from __future__ import annotations
import json,sqlite3,uuid
from datetime import datetime,timezone
from pathlib import Path
NAMESPACE=uuid.UUID("f344397f-83d2-4a64-95c7-74941be1f369")
def utc_now(): return datetime.now(timezone.utc).isoformat()
def stable_id(kind,value): return str(uuid.uuid5(NAMESPACE,f"{kind}:{value}"))
class Repository:
    def __init__(self,database=":memory:"):
        self.connection=sqlite3.connect(str(database)); self.connection.row_factory=sqlite3.Row; self.connection.execute("PRAGMA foreign_keys=ON")
    def initialize(self):
        self.connection.execute("CREATE TABLE IF NOT EXISTS schema_migrations(version TEXT PRIMARY KEY,applied_at TEXT NOT NULL)")
        for path in sorted(Path(__file__).with_name("migrations").glob("*.sql")):
            version=path.stem.split("_",1)[0]
            if self.connection.execute("SELECT 1 FROM schema_migrations WHERE version=?",(version,)).fetchone(): continue
            self.connection.executescript(path.read_text()); self.connection.execute("INSERT INTO schema_migrations VALUES(?,?)",(version,utc_now()))
        self.connection.commit()
    def ensure_source(self,source_id,name,domain,authority_level,access_status,configuration):
        self.connection.execute("INSERT INTO data_sources VALUES(?,?,?,?,?,?) ON CONFLICT(source_id) DO UPDATE SET configuration_json=excluded.configuration_json",(source_id,name,domain,authority_level,access_status,json.dumps(configuration,sort_keys=True))); self.connection.commit()
    def start_run(self,source_id,parser_version):
        run_id=str(uuid.uuid4()); self.connection.execute("INSERT INTO ingestion_runs(run_id,source_id,started_at,status,parser_version) VALUES(?,?,?,'RUNNING',?)",(run_id,source_id,utc_now(),parser_version)); self.connection.commit(); return run_id
    def finish_run(self,run_id,status,records,errors,details=None):
        self.connection.execute("UPDATE ingestion_runs SET finished_at=?,status=?,records_processed=?,errors=?,error_details=? WHERE run_id=?",(utc_now(),status,records,errors,details,run_id)); self.connection.commit()
    def add_raw_document(self,values):
        self.connection.execute("INSERT INTO raw_documents VALUES(?,?,?,?,?,?,?,?,?)",values)
    def upsert_candidate(self,issuer_id,issuer_name,security_id,security_class,isin,ticker,known_at,document_id):
        self.connection.execute("INSERT OR IGNORE INTO issuers(issuer_id,legal_name,resolution_method,created_at) VALUES(?,?,?,?)",(issuer_id,issuer_name,"EXACT_SOURCE_DISPLAY_NAME",known_at))
        self.connection.execute("INSERT OR IGNORE INTO issuer_name_history VALUES(?,?,?,?,?,?,?,?)",(stable_id("name",f"{issuer_id}:{issuer_name}:{known_at}"),issuer_id,issuer_name,"SOURCE_DISPLAY",None,None,known_at,document_id))
        row=self.connection.execute("SELECT security_class_code FROM securities WHERE security_id=?",(security_id,)).fetchone()
        if row is None: self.connection.execute("INSERT INTO securities VALUES(?,?,?,?,?,?,?)",(security_id,issuer_id,security_class,"EQUITY",None,"UZS",known_at))
        elif row[0]=="UNKNOWN" and security_class!="UNKNOWN": self.connection.execute("UPDATE securities SET security_class_code=? WHERE security_id=?",(security_class,security_id))
        self.connection.execute("INSERT OR IGNORE INTO listings VALUES(?,?,?,?,?,?,?,?,?)",(stable_id("listing",f"{security_id}:UZSE:{known_at}"),security_id,"UZSE","STK","ACTIVE",None,None,known_at,document_id))
        for kind,value in (("ISIN",isin),("TICKER",ticker)):
            self.connection.execute("INSERT OR IGNORE INTO identifier_history(identifier_id,entity_type,security_id,identifier_type,identifier_value,known_at,document_id) VALUES(?,'SECURITY',?,?,?,?,?)",(stable_id("identifier",f"{kind}:{value}:{known_at}"),security_id,kind,value,known_at,document_id))
    def conflict(self,run_id,kind,value,reason):
        self.connection.execute("INSERT INTO resolution_conflicts VALUES(?,?,?,?,?,'UNRESOLVED',?)",(str(uuid.uuid4()),run_id,kind,value,reason,utc_now()))
    def counts(self):
        return {t:self.connection.execute(f"SELECT count(*) FROM {t}").fetchone()[0] for t in ("issuers","securities","resolution_conflicts")}
    def close(self): self.connection.close()
    def __enter__(self): return self
    def __exit__(self,*_): self.close()
