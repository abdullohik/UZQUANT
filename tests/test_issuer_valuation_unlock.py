import unittest

from uzquant.issuer_valuation_unlock import select_issuer_worklist


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


if __name__ == "__main__":
    unittest.main()
