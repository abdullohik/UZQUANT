import tempfile,unittest
from decimal import Decimal
from pathlib import Path
from uzquant.financial_documents import parse_decimal,parse_statement_rows,point_in_time
from uzquant.financial_taxonomy import map_concept
from uzquant.repository import Repository,stable_id

FIXTURE=b'''<table><tr><th>Indicator Name</th><th>Row Code</th><th>At the Beginning of the Reporting Period</th><th>At the End of the Reporting Period</th></tr><tr><td>Total Assets</td><td>400</td><td>900,00</td><td>1 000,00</td></tr><tr><td>Missing</td><td>401</td><td>-</td><td>-</td></tr></table>'''
class FinancialTests(unittest.TestCase):
 def test_locale_decimal_and_parentheses(self):
  self.assertEqual(parse_decimal("1 234 567,89"),Decimal("1234567.89")); self.assertEqual(parse_decimal("(15,2)"),Decimal("-15.2")); self.assertIsNone(parse_decimal("-"))
 def test_structured_html_and_missing_not_inferred(self):
  rows=parse_statement_rows(FIXTURE); self.assertEqual(len(rows),1); self.assertEqual(rows[0].raw_value,"1 000,00")
 def test_multilingual_taxonomy(self):
  self.assertEqual(map_concept("Чистая прибыль"),"Net Income"); self.assertEqual(map_concept("Sotishdan sof tushum"),"Revenue"); self.assertIsNone(map_concept("Unmapped custom row"))
  self.assertEqual(map_concept("Net interest income"),"Net Interest Income")
  self.assertEqual(map_concept("Страховые резервы"),"Insurance Reserves")
 def test_point_in_time_excludes_later_publication(self):
  with tempfile.TemporaryDirectory() as td:
   repo=Repository(Path(td)/"x.db"); repo.initialize()
   repo.connection.execute("INSERT INTO data_sources VALUES('s','s','x','PRIMARY','VERIFIED_MANUAL','{}')")
   repo.connection.execute("INSERT INTO issuers(issuer_id,legal_name,resolution_method,created_at) VALUES('i','Issuer','TEST','2020-01-01')")
   repo.connection.execute("INSERT INTO ingestion_runs(run_id,source_id,started_at,status,parser_version) VALUES('r','s','2020-01-01','RUNNING','p')")
   for num,pub in (("1","2024-02-01"),("2","2024-05-01")):
    raw="r"+num; doc="d"+num
    repo.connection.execute("INSERT INTO raw_documents VALUES(?,?,?,?,?,?,?,?,?)",(raw,'s','r','https://x/'+num,'2024-01-01',pub,'text/html','a'*63+num,'x'))
    repo.connection.execute("INSERT INTO financial_documents VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(doc,'i',raw,'Issuer','UNKNOWN','2023-01-01','2023-12-31',pub,None,'ANNUAL','HTML','LOCAL_GAAP','UNAUDITED',None,'s','https://x/'+num,num,'2024-01-01','a'*63+num,'p','ORIGINAL',None))
    repo.connection.execute("INSERT INTO financial_observations VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",('o'+num,doc,'i','INCOME_STATEMENT','Revenue','2023-01-01','2023-12-31',num,num,None,'UNKNOWN','AS_REPORTED','row','HTML','HIGH','REPORTED'))
   self.assertEqual(point_in_time(repo,'i','Revenue','2024-03-01')['normalized_value'],'1')
   self.assertEqual(point_in_time(repo,'i','Revenue','2024-06-01')['normalized_value'],'2'); repo.close()
 def test_migrations_idempotent(self):
  repo=Repository(); repo.initialize(); repo.initialize(); self.assertEqual(repo.connection.execute("select count(*) from schema_migrations where version='005'").fetchone()[0],1); repo.close()
if __name__=='__main__': unittest.main()
