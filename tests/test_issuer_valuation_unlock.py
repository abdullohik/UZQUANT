import tempfile
import unittest
from pathlib import Path

from uzquant.issuer_valuation_unlock import import_verified_listing_shares,select_issuer_worklist
from uzquant.repository import Repository


class IssuerWorklistTests(unittest.TestCase):
    def test_groups_share_classes_and_ranks_by_liquidity_then_readiness(self):
        rows = [
            {"issuer_id":"a","issuer":"A","ticker":"A","average_daily_turnover":"10","readiness_score":20},
            {"issuer_id":"a","issuer":"A","ticker":"AP","average_daily_turnover":"5","readiness_score":30},
            {"issuer_id":"b","issuer":"B","ticker":"B","average_daily_turnover":"20","readiness_score":1},
        ]
        selected = select_issuer_worklist(rows, 2)
        self.assertEqual([row["issuer_id"] for row in selected], ["b", "a"])
        self.assertEqual([s["ticker"] for s in selected[1]["securities"]], ["A", "AP"])

    def test_limit_is_enforced(self):
        rows=[{"issuer_id":str(i),"issuer":str(i),"ticker":str(i),"average_daily_turnover":0,"readiness_score":i} for i in range(20)]
        self.assertEqual(len(select_issuer_worklist(rows, 12)), 12)

    def test_listing_shares_require_exact_verified_isin_and_class(self):
        with tempfile.TemporaryDirectory() as td:
            with Repository(Path(td)/"x.db") as repo:
                repo.initialize(); c=repo.connection
                c.execute("INSERT INTO data_sources VALUES('rse','RSE','uzse.uz','PRIMARY','VERIFIED_AUTOMATED','{}')")
                c.execute("INSERT INTO ingestion_runs(run_id,source_id,started_at,status,parser_version) VALUES('run','rse','2026-01-02','SUCCEEDED','p')")
                c.execute("INSERT INTO canonical_issuers VALUES('ci','ACTIVE','2020-01-01')")
                c.execute("INSERT INTO issuers(issuer_id,legal_name,resolution_method,created_at,canonical_issuer_id) VALUES('i','Issuer','TEST','2020-01-01','ci')")
                c.execute("INSERT INTO securities(security_id,issuer_id,security_class_code,security_type,currency,created_at) VALUES('s','i','COMMON','EQUITY','UZS','2020-01-01')")
                c.execute("INSERT INTO raw_documents VALUES('raw','rse','run','https://uzse.uz/detail','2026-01-02',NULL,'text/html',?,?)",('a'*64,'x'))
                c.execute("INSERT INTO raw_documents VALUES('list','rse','run','https://uzse.uz/list','2026-01-02',NULL,'text/html',?,?)",('b'*64,'y'))
                c.execute("INSERT INTO raw_documents VALUES('quote','rse','run','https://uzse.uz/quote','2026-01-02',NULL,'text/html',?,?)",('c'*64,'z'))
                c.execute("INSERT INTO effective_identifier_evidence VALUES('e','SECURITY',NULL,'s','ISIN','UZ0001','2020-01-01',NULL,'2026-01-02','rse','raw','HIGH','VERIFIED')")
                c.execute("INSERT INTO rse_universe_captures VALUES('cap','run','2026-01-02T00:00:00+00:00','https://uzse.uz/list','https://uzse.uz/quote','list','quote',1,1,'[1]',1,1,0,1,'p')")
                c.execute("INSERT INTO rse_universe_instruments VALUES('cap','LISTING','UZ0001','AAA','Issuer','COMMON_EQUITY','explicit','A','LISTED',NULL,NULL,'100','10','UZS','raw','{}')")
                self.assertEqual(import_verified_listing_shares(repo),1)
                row=c.execute("SELECT class_shares_outstanding,verification_status FROM share_capital_observations").fetchone()
                self.assertEqual(tuple(row),("100","VERIFIED"))
                self.assertEqual(import_verified_listing_shares(repo),0)


if __name__ == "__main__":
    unittest.main()
