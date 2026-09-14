import unittest
from datetime import date
from uzquant.market_quality import calculate_quality
from uzquant.market_time import normalize_exchange_timestamp
class QualityTests(unittest.TestCase):
    def test_missing_days_are_not_zero_returns(self):
        rows=[{"trade_date":"2026-01-01","close":"100","share_volume":"2","observation_status":"TRADE_REPORTED"},{"trade_date":"2026-01-02","close":"100","share_volume":"0","observation_status":"NO_TRADE_PLACEHOLDER"},{"trade_date":"2026-01-03","close":"100","share_volume":"3","observation_status":"TRADE_REPORTED"}]
        result=calculate_quality(rows,as_of=date(2026,1,3),expected_trading_days={date(2026,1,1),date(2026,1,2),date(2026,1,3)})
        self.assertEqual(result["zero_trade_day_ratio"],"0.3333333333333333333333333333")
        self.assertEqual(result["observed_returns"],["0"])
    def test_stale_price(self):
        result=calculate_quality([{"trade_date":"2026-01-01","close":"1","share_volume":"1"}],as_of=date(2026,2,1))
        self.assertIn("VERY_STALE_PRICE",{f[1] for f in result["flags"]})
    def test_timezone_conversion(self):
        self.assertEqual(normalize_exchange_timestamp("2026-01-01T00:00:00+00:00"),"2026-01-01T05:00:00+05:00")
if __name__=="__main__": unittest.main()
