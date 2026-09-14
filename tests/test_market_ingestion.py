import tempfile,unittest
from pathlib import Path
from uzquant.config import Settings
from uzquant.market_data import ingest_market_data
from uzquant.repository import Repository,stable_id
GOOD=b'data.push([moment("20260102", "YYYYMMDD")._d.valueOf(),1,2,1,2,10]);'
DUPLICATE=GOOD+GOOD
class MarketIngestionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); root=Path(self.temp.name); self.settings=Settings(root/"db.sqlite3",root/"raw")
        with Repository(self.settings.database_path) as repo:
            repo.initialize(); repo.ensure_source("uzse-public-web","RSE","uzse.uz","PRIMARY","PARTIAL",{})
            run=repo.start_run("uzse-public-web","seed"); doc="seed-doc"
            repo.add_raw_document((doc,"uzse-public-web",run,"https://example.invalid/seed","2026-01-01",None,"text/html","0"*64,"seed"))
            issuer=stable_id("issuer","seed"); security=stable_id("security","isin:UZTEST")
            repo.upsert_candidate(issuer,"Seed issuer",security,"COMMON","UZTEST","TEST","2026-01-01",doc); repo.connection.commit(); repo.finish_run(run,"SUCCEEDED",1,0)
    def tearDown(self): self.temp.cleanup()
    def test_partial_source_failure_is_recorded(self):
        def fetcher(url,**kwargs):
            if "UZFAIL" in url: raise RuntimeError("synthetic source failure")
            return GOOD
        result=ingest_market_data(self.settings,{"TEST":"UZTEST","FAIL":"UZFAIL"},fetcher)
        self.assertEqual(result["status"],"PARTIAL"); self.assertEqual(result["securities_succeeded"],1); self.assertEqual(len(result["errors"]),1)
    def test_idempotent_rerun_and_duplicate_detection(self):
        fetcher=lambda url,**kwargs:DUPLICATE
        ingest_market_data(self.settings,{"TEST":"UZTEST"},fetcher); ingest_market_data(self.settings,{"TEST":"UZTEST"},fetcher)
        with Repository(self.settings.database_path) as repo:
            self.assertEqual(repo.connection.execute("select count(*) from market_observations").fetchone()[0],1)
            self.assertEqual(repo.connection.execute("select count(*) from market_quality_flags where flag_type='DUPLICATE_RECORD'").fetchone()[0],2)
if __name__=="__main__": unittest.main()
