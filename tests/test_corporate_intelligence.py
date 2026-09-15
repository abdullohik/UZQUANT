import tempfile,unittest
from pathlib import Path
from uzquant.corporate_intelligence import after,iso,ownership_as_of,rights_as_of,visible_tokens
from uzquant.repository import Repository

class CorporateIntelligenceTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.repo=Repository(Path(self.tmp.name)/"test.db");self.repo.initialize();c=self.repo.connection
  c.execute("INSERT INTO data_sources VALUES('s','Source','x','PRIMARY','VERIFIED_MANUAL','{}')");c.execute("INSERT INTO ingestion_runs(run_id,source_id,started_at,status,parser_version) VALUES('run','s','2020-01-01','RUNNING','p')")
  c.execute("INSERT INTO raw_documents VALUES('raw','s','run','https://x','2020-01-01','2020-01-01','text/html',?,'x')",('a'*64,));c.execute("INSERT INTO raw_documents VALUES('raw2','s','run','https://y','2021-01-01','2021-01-01','text/html',?,'y')",('b'*64,))
  c.execute("INSERT INTO issuers(issuer_id,legal_name,resolution_method,created_at) VALUES('issuer','Issuer','TEST','2020-01-01')")
  c.execute("INSERT INTO securities VALUES('common','issuer','COMMON','EQUITY',NULL,'UZS','2020-01-01')");c.execute("INSERT INTO securities VALUES('preferred','issuer','PREFERRED','EQUITY',NULL,'UZS','2020-01-01')");c.commit()
 def tearDown(self):self.repo.close();self.tmp.cleanup()
 def test_share_class_specific_dividends(self):
  c=self.repo.connection;c.execute("INSERT INTO dividends VALUES('d1','issuer','common','2020-01-01',NULL,NULL,NULL,NULL,'10','UZS','REGULAR','raw','x','HIGH')");c.execute("INSERT INTO dividends VALUES('d2','issuer','preferred','2020-01-01',NULL,NULL,NULL,NULL,'20','UZS','REGULAR','raw','x','HIGH')")
  self.assertEqual(c.execute("SELECT dividend_per_share FROM dividends WHERE security_id='preferred'").fetchone()[0],'20')
 def test_effective_date_is_distinct(self):
  self.repo.connection.execute("INSERT INTO corporate_actions VALUES('a','issuer','common','NEW_ISSUANCE','2020-02-01',NULL,'2020-01-30',NULL,NULL,'{}','raw','x','HIGH','VERIFIED')")
  row=self.repo.connection.execute("SELECT announcement_date,effective_date,adjustment_factor FROM corporate_actions").fetchone();self.assertEqual(tuple(row),('2020-02-01','2020-01-30',None))
 def test_ownership_history_and_missing_free_float(self):
  c=self.repo.connection;c.execute("INSERT INTO ownership_positions VALUES('o1','issuer',NULL,'State','STATE','80',NULL,NULL,'2020-01-01','2020-02-01','raw','x','HIGH')");c.execute("INSERT INTO ownership_positions VALUES('o2','issuer',NULL,'Fund','INSTITUTIONAL','25',NULL,NULL,'2021-01-01','2021-02-01','raw2','y','HIGH')");c.execute("INSERT INTO ownership_metrics VALUES('m','issuer','2021-02-01','Free float',NULL,'UNAVAILABLE','not disclosed','[\"raw2\"]')")
  self.assertEqual(len(ownership_as_of(self.repo,'issuer','2020-12-31')),1);self.assertIsNone(c.execute("SELECT metric_value FROM ownership_metrics").fetchone()[0])
 def test_rights_uncertainty_and_point_in_time(self):
  values=('r','preferred',None,'2020-01-01',None,'Observed dividend',None,None,None,None,None,None,None,None,None,None,'fact','Other rights unknown','LOW','raw','x');self.repo.connection.execute("INSERT INTO security_rights VALUES("+','.join('?'*21)+")",values)
  self.assertEqual(rights_as_of(self.repo,'preferred','2020-12-31')['rights_confidence'],'LOW');self.assertIsNone(rights_as_of(self.repo,'preferred','2020-12-31')['voting_rights'])
 def test_conflicting_disclosures_are_preserved(self):
  c=self.repo.connection;c.execute("INSERT INTO corporate_data_conflicts VALUES('c','issuer','preferred','minimum_dividend','10','20','raw','raw2','UNRESOLVED','2021-01-01')");self.assertEqual(c.execute("SELECT status FROM corporate_data_conflicts").fetchone()[0],'UNRESOLVED')
 def test_visible_text_and_dates(self):
  tokens=visible_tokens(b'<script>bad</script><div>Date</div><span>01.02.2020</span>');self.assertEqual(after(tokens,'Date'),'01.02.2020');self.assertEqual(iso('01.02.2020'),'2020-02-01')
if __name__=='__main__':unittest.main()
