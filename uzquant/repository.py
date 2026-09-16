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
        canonical_id=str(uuid.uuid4())
        self.connection.execute("INSERT OR IGNORE INTO canonical_issuers VALUES(?,'ACTIVE',?)",(canonical_id,known_at))
        self.connection.execute("INSERT OR IGNORE INTO issuers(issuer_id,legal_name,resolution_method,created_at,canonical_issuer_id) VALUES(?,?,?,?,?)",(issuer_id,issuer_name,"OPAQUE_INTERNAL_ID_VERIFIED_SOURCE_ASSOCIATION",known_at,canonical_id))
        issuer=self.connection.execute("SELECT canonical_issuer_id FROM issuers WHERE issuer_id=?",(issuer_id,)).fetchone()
        if issuer is None: raise ValueError(f"issuer creation failed: {issuer_id}")
        if issuer[0]!=canonical_id:
            self.connection.execute("DELETE FROM canonical_issuers WHERE canonical_issuer_id=?",(canonical_id,))
        else:
            self.connection.execute("INSERT OR IGNORE INTO issuer_identity_migrations VALUES(?,?,?,?,?,?)",(str(uuid.uuid4()),issuer_id,canonical_id,"CREATED_OPAQUE_NOT_NAME_DERIVED",json.dumps([document_id]),known_at))
        self.connection.execute("INSERT OR IGNORE INTO issuer_name_history VALUES(?,?,?,?,?,?,?,?)",(stable_id("name",f"{issuer_id}:{issuer_name}:{known_at}"),issuer_id,issuer_name,"SOURCE_DISPLAY",None,None,known_at,document_id))
        row=self.connection.execute("SELECT security_class_code FROM securities WHERE security_id=?",(security_id,)).fetchone()
        if row is None: self.connection.execute("INSERT INTO securities VALUES(?,?,?,?,?,?,?)",(security_id,issuer_id,security_class,"EQUITY",None,"UZS",known_at))
        elif row[0]=="UNKNOWN" and security_class!="UNKNOWN": self.connection.execute("UPDATE securities SET security_class_code=? WHERE security_id=?",(security_class,security_id))
        self.connection.execute("INSERT OR IGNORE INTO listings VALUES(?,?,?,?,?,?,?,?,?)",(stable_id("listing",f"{security_id}:UZSE:{known_at}"),security_id,"UZSE","STK","ACTIVE",None,None,known_at,document_id))
        self.connection.execute("INSERT OR IGNORE INTO effective_security_attributes VALUES(?,?,?,?,?,?,?,?,?)",(str(uuid.uuid4()),security_id,"SECURITY_CLASS",security_class,None,None,known_at,document_id,"HIGH"))
        self.connection.execute("INSERT OR IGNORE INTO effective_security_attributes VALUES(?,?,?,?,?,?,?,?,?)",(str(uuid.uuid4()),security_id,"LISTING_STATUS","ACTIVE",None,None,known_at,document_id,"HIGH"))
        for kind,value in (("ISIN",isin),("TICKER",ticker)):
            self.connection.execute("INSERT OR IGNORE INTO identifier_history(identifier_id,entity_type,security_id,identifier_type,identifier_value,known_at,document_id) VALUES(?,'SECURITY',?,?,?,?,?)",(stable_id("identifier",f"{kind}:{value}:{known_at}"),security_id,kind,value,known_at,document_id))
            source=self.connection.execute("SELECT source_id FROM raw_documents WHERE document_id=?",(document_id,)).fetchone()
            if source:
                self.connection.execute("INSERT OR IGNORE INTO effective_identifier_evidence VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",(str(uuid.uuid4()),"SECURITY",issuer[0],security_id,kind,value,None,None,known_at,source[0],document_id,"HIGH","VERIFIED"))
    def conflict(self,run_id,kind,value,reason):
        self.connection.execute("INSERT INTO resolution_conflicts VALUES(?,?,?,?,?,'UNRESOLVED',?)",(str(uuid.uuid4()),run_id,kind,value,reason,utc_now()))
    def counts(self):
        return {t:self.connection.execute(f"SELECT count(*) FROM {t}").fetchone()[0] for t in ("issuers","securities","resolution_conflicts")}
    def close(self): self.connection.close()
    def __enter__(self): return self
    def __exit__(self,*_): self.close()
