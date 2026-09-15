import sqlite3,tempfile,unittest
from pathlib import Path
from uzquant.repository import Repository,stable_id
class DatabaseTests(unittest.TestCase):
    def test_fresh_database_migrates_reproducibly(self):
        with tempfile.TemporaryDirectory() as d:
            with Repository(Path(d)/"db.sqlite3") as repo:
                repo.initialize(); repo.initialize()
                tables={r[0] for r in repo.connection.execute("select name from sqlite_master where type='table'")}
                self.assertTrue({"issuers","securities","security_classes","listings","identifier_history","data_sources","ingestion_runs"}<=tables)
                self.assertTrue({"share_capital_observations","source_coverage_audits"}<=tables)
    def test_stable_ids_are_reproducible_and_isin_based(self):
        self.assertEqual(stable_id("security","isin:UZ000"),stable_id("security","isin:UZ000"))
        self.assertNotEqual(stable_id("security","isin:UZ000"),stable_id("security","ticker:TEST"))
    def test_identifier_history_rejects_missing_entity(self):
        with Repository() as repo:
            repo.initialize()
            with self.assertRaises(sqlite3.IntegrityError):
                repo.connection.execute("insert into identifier_history(identifier_id,entity_type,identifier_type,identifier_value,known_at,document_id) values('x','SECURITY','ISIN','x','2025-01-01','missing')")
    def test_raw_document_requires_provenance(self):
        with Repository() as repo:
            repo.initialize()
            with self.assertRaises(sqlite3.IntegrityError):
                repo.add_raw_document(("d","missing","missing","https://example.invalid","2025-01-01",None,"text/html","0"*64,"raw/file"))
    def test_raw_document_is_immutable(self):
        with Repository() as repo:
            repo.initialize(); repo.ensure_source("s","Synthetic","example.invalid","PRIMARY","VERIFIED_MANUAL",{})
            run=repo.start_run("s","test/1"); repo.add_raw_document(("d","s",run,"https://example.invalid","2025-01-01",None,"text/html","0"*64,"raw/file"))
            with self.assertRaises(sqlite3.IntegrityError):
                repo.connection.execute("update raw_documents set source_url='changed' where document_id='d'")
if __name__=="__main__": unittest.main()
