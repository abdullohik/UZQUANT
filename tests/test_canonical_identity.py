import tempfile
import unittest
from pathlib import Path

from uzquant.identity import (IDENTIFIER_OUT_OF_RANGE, IDENTITY_CONFLICT,
                              RESOLVED, create_opaque_issuer,
                              resolve_security_identifier,
                              resolve_security_pair)
from uzquant.identity_hotfix import backfill_document_assignments
from uzquant.repository import Repository
from uzquant.security_master import normalize_name


class CanonicalIdentityTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.repo=Repository(Path(self.temp.name)/"x.db"); self.repo.initialize()
        c=self.repo.connection
        c.execute("INSERT INTO data_sources VALUES('s','Source','x','PRIMARY','VERIFIED_MANUAL','{}')")
        c.execute("INSERT INTO ingestion_runs(run_id,source_id,started_at,status,parser_version) VALUES('run','s','2020-01-01','RUNNING','p')")
        c.execute("INSERT INTO raw_documents VALUES('raw','s','run','https://x','2020-01-01',NULL,'text/html',?,'x')",('a'*64,))
    def tearDown(self): self.repo.close(); self.temp.cleanup()
    def issuer(self,name): return create_opaque_issuer(self.repo,name,"2020-01-01T00:00:00+00:00","s","raw")
    def security(self,issuer,canonical,sid,ticker,isin,start="2020-01-01",end=None,known="2020-01-01T00:00:00+00:00",klass="COMMON"):
        c=self.repo.connection
        c.execute("INSERT INTO securities VALUES(?,?,?,?,?,?,?)",(sid,issuer,klass,"EQUITY",None,"UZS",known))
        for n,(kind,value) in enumerate((("TICKER",ticker),("ISIN",isin))):
            c.execute("INSERT INTO effective_identifier_evidence VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",(f"e-{sid}-{n}","SECURITY",canonical,sid,kind,value,start,end,known,"s","raw","HIGH","VERIFIED"))

    def test_identical_normalized_names_do_not_merge(self):
        a=self.issuer("Example Bank AJ"); b=self.issuer("Example Bank AJ")
        self.assertNotEqual(a,b)
    def test_punctuation_collision_does_not_merge(self):
        self.assertEqual(normalize_name("Example-Bank AJ"),normalize_name("Example Bank, AJ"))
        self.assertNotEqual(self.issuer("Example-Bank AJ"),self.issuer("Example Bank, AJ"))
    def test_fuzzy_name_is_not_authoritative(self):
        self.assertNotEqual(self.issuer("Kafolat AJ")[1],self.issuer("Kafolat Joint Stock Company")[1])
    def test_canonical_id_persists_across_reopen(self):
        issuer,canonical=self.issuer("Persistent"); self.repo.connection.commit(); path=Path(self.temp.name)/"x.db"; self.repo.close(); self.repo=Repository(path); self.repo.initialize()
        self.assertEqual(self.repo.connection.execute("SELECT canonical_issuer_id FROM issuers WHERE issuer_id=?",(issuer,)).fetchone()[0],canonical)
    def test_ticker_reuse_and_effective_date(self):
        i1,c1=self.issuer("One"); i2,c2=self.issuer("Two"); self.security(i1,c1,"s1","ABC","ISIN1",end="2022-01-01"); self.security(i2,c2,"s2","ABC","ISIN2",start="2022-01-01")
        self.assertEqual(resolve_security_identifier(self.repo,"TICKER","ABC","2021-12-31").security_id,"s1")
        self.assertEqual(resolve_security_identifier(self.repo,"TICKER","ABC","2022-01-01").security_id,"s2")
    def test_ticker_change_over_time(self):
        i,c=self.issuer("One"); self.security(i,c,"s1","OLD","ISIN1",end="2022-01-01")
        self.repo.connection.execute("INSERT INTO effective_identifier_evidence VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",("new","SECURITY",c,"s1","TICKER","NEW","2022-01-01",None,"2020-01-01T00:00:00+00:00","s","raw","HIGH","VERIFIED"))
        self.assertEqual(resolve_security_identifier(self.repo,"TICKER","NEW","2023-01-01").security_id,"s1")
        self.assertEqual(resolve_security_identifier(self.repo,"TICKER","OLD","2023-01-01").status,IDENTIFIER_OUT_OF_RANGE)
    def test_isin_conflict_fails_closed(self):
        i1,c1=self.issuer("One"); i2,c2=self.issuer("Two"); self.security(i1,c1,"s1","A","SAME"); self.security(i2,c2,"s2","B","SAME")
        self.assertEqual(resolve_security_identifier(self.repo,"ISIN","SAME","2021-01-01").status,IDENTITY_CONFLICT)
    def test_ticker_isin_disagreement(self):
        i1,c1=self.issuer("One"); i2,c2=self.issuer("Two"); self.security(i1,c1,"s1","A","I1"); self.security(i2,c2,"s2","B","I2")
        self.assertEqual(resolve_security_pair(self.repo,"A","I2","2021-01-01").status,IDENTITY_CONFLICT)
    def test_identifier_boundary_is_end_exclusive(self):
        i,c=self.issuer("One"); self.security(i,c,"s1","A","I1",end="2021-01-01")
        self.assertEqual(resolve_security_identifier(self.repo,"TICKER","A","2021-01-01").status,IDENTIFIER_OUT_OF_RANGE)
    def test_document_after_ticker_change_rejects_old_ticker(self):
        i,c=self.issuer("One"); self.security(i,c,"s1","OLD","I1",end="2022-01-01")
        self.assertEqual(resolve_security_pair(self.repo,"OLD","I1","2023-01-01").status,IDENTIFIER_OUT_OF_RANGE)
    def test_common_preferred_are_distinct_same_issuer(self):
        i,c=self.issuer("AGMK"); self.security(i,c,"common","AGMK","I1",klass="COMMON"); self.security(i,c,"preferred","AGMKP","I2",klass="PREFERRED")
        self.assertNotEqual(resolve_security_pair(self.repo,"AGMK","I1","2021-01-01").security_id,resolve_security_pair(self.repo,"AGMKP","I2","2021-01-01").security_id)
        self.assertEqual(resolve_security_pair(self.repo,"AGMK","I1","2021-01-01").canonical_issuer_id,c)
    def test_kasu_classes_are_distinct(self):
        i,c=self.issuer("KASU"); self.security(i,c,"common","KASU","I1"); self.security(i,c,"preferred","KASUP","I2",klass="PREFERRED")
        self.assertNotEqual(resolve_security_pair(self.repo,"KASU","I1","2021-01-01").security_id,resolve_security_pair(self.repo,"KASUP","I2","2021-01-01").security_id)
    def test_ambiguous_ticker_fails_closed(self):
        i1,c1=self.issuer("One"); i2,c2=self.issuer("Two"); self.security(i1,c1,"s1","A","I1"); self.security(i2,c2,"s2","A","I2")
        self.assertEqual(resolve_security_identifier(self.repo,"TICKER","A","2021-01-01").status,IDENTITY_CONFLICT)
    def test_source_disagreement_fails_closed(self):
        i1,c1=self.issuer("One"); i2,c2=self.issuer("Two"); self.security(i1,c1,"s1","A","I1"); self.security(i2,c2,"s2","B","I2")
        self.assertEqual(resolve_security_pair(self.repo,"A","I2","2021-01-01").status,IDENTITY_CONFLICT)
    def test_misassigned_existing_report_is_quarantined(self):
        i1,c1=self.issuer("AGMK"); i2,c2=self.issuer("Wrong"); self.security(i1,c1,"agmk","AGMK","UZ7000550002")
        c=self.repo.connection
        c.execute("INSERT INTO raw_documents VALUES('finraw','s','run','https://f','2024-01-01','2024-09-25','text/html',?,'f')",('b'*64,))
        c.execute("INSERT INTO financial_documents VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",('doc',i2,'finraw','Wrong','UNKNOWN','2023-01-01','2023-12-31','2024-09-25',None,'ANNUAL','HTML','LOCAL_STATUTORY','AUDITED','UZS','s','https://f','5218','2024-01-01','b'*64,'p','ORIGINAL',None))
        counts=backfill_document_assignments(self.repo)
        self.assertEqual(counts["QUARANTINED"],1)
        self.assertEqual(c.execute("SELECT assignment_status FROM financial_document_identity_assignments WHERE document_id='doc'").fetchone()[0],"QUARANTINED")


if __name__=="__main__": unittest.main()
