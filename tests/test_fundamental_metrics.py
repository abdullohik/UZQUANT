import unittest
from datetime import date
from decimal import Decimal as D
from uzquant.fundamental_metrics import PeriodValue,compute_bank,compute_general,compute_insurance,compute_quality,construct_ttm,growth,historical_growth,route_sector,safe_div

class MetricFormulaTests(unittest.TestCase):
 def test_general_formulas(self):
  v={"Revenue":D(100),"Gross Profit":D(40),"Net Income":D(10),"Short-Term Debt":D(20),"Long-Term Debt":D(30),"Cash":D(15),"Equity":D(50),"Operating Cash Flow":D(18),"CapEx":D(5),"Dividends":D(2)}
  r=compute_general(v,{"Revenue":D(80),"Net Income":D(8),"Short-Term Debt":D(10),"Long-Term Debt":D(30)})
  self.assertEqual(r["Gross Margin"].value,D("0.4")); self.assertEqual(r["Revenue Growth"].value,D("0.25")); self.assertEqual(r["Net Debt"].value,D(35)); self.assertEqual(r["FCF Margin"].value,D("0.13")); self.assertEqual(r["Dividend Payout Ratio"].value,D("0.2"))
 def test_zero_denominator_and_missing(self):
  self.assertEqual(safe_div(D(1),D(0)).reason,"ZERO_DENOMINATOR"); self.assertEqual(safe_div(None,D(2)).reason,"MISSING_INPUT"); self.assertEqual(growth(D(1),D(0)).reason,"ZERO_PRIOR_PERIOD")
 def test_negative_values_are_mathematical_not_suppressed(self): self.assertEqual(safe_div(D(-5),D(10)).value,D("-0.5"))
 def test_quality_flags(self):
  v={"Operating Cash Flow":D(5),"Net Income":D(10),"Receivables":D(150),"Inventory":D(100),"Revenue":D(110),"Short-Term Debt":D(40),"Long-Term Debt":D(40)}
  p={"Receivables":D(100),"Inventory":D(50),"Revenue":D(100),"Short-Term Debt":D(20),"Long-Term Debt":D(20)}
  _,flags=compute_quality(v,p)
  self.assertEqual(flags["POOR_CASH_CONVERSION"][0],"TRIGGERED"); self.assertEqual(flags["RAPID_DEBT_GROWTH"][0],"TRIGGERED"); self.assertEqual(flags["INVENTORY_ANOMALY"][0],"TRIGGERED")
 def test_sector_routing(self):
  self.assertEqual(route_sector("https://openinfo.uz/en/reports/bank/quarter/1"),"BANK"); self.assertEqual(route_sector("https://openinfo.uz/en/reports/insurance/quarter/1"),"INSURANCE"); self.assertEqual(route_sector("x","Mining"),"MINING"); self.assertEqual(route_sector("x"),"GENERAL")
 def test_sector_formulas(self):
  bank=compute_bank({"Net Interest Income":D(10),"Average Earning Assets":D(200),"Operating Expenses":D(8),"Non-Interest Income":D(6)})
  self.assertEqual(bank["NIM"].value,D("0.05")); self.assertEqual(bank["Cost/Income"].value,D("0.5"))
  insurer=compute_insurance({"Claims":D(40),"Premiums":D(100),"Underwriting Expenses":D(20)})
  self.assertEqual(insurer["Combined Ratio"].value,D("0.6"))
 def test_ttm_compatible_nonoverlapping(self):
  ranges=((date(2025,1,1),date(2025,3,31)),(date(2025,4,1),date(2025,6,30)),(date(2025,7,1),date(2025,9,30)),(date(2025,10,1),date(2025,12,31)))
  periods=[PeriodValue(a,b,D(10),"UZS","ONES","STANDALONE","IFRS") for a,b in ranges]
  self.assertEqual(construct_ttm(periods).value,D(40))
 def test_ttm_rejects_gap_overlap_and_mismatch(self):
  base=[PeriodValue(date(2025,1,1),date(2025,3,31),D(1),"UZS","ONES","STANDALONE","IFRS"),PeriodValue(date(2025,4,1),date(2025,6,30),D(1),"UZS","ONES","STANDALONE","IFRS"),PeriodValue(date(2025,7,2),date(2025,9,30),D(1),"UZS","ONES","STANDALONE","IFRS"),PeriodValue(date(2025,10,1),date(2025,12,31),D(1),"UZS","ONES","STANDALONE","IFRS")]
  self.assertEqual(construct_ttm(base).reason,"OVERLAPPING_OR_GAPPED_PERIODS")
  self.assertEqual(construct_ttm(base[:3]).reason,"TTM_REQUIRES_FOUR_QUARTERS")
  mismatch=[*base[:3],PeriodValue(date(2025,10,1),date(2025,12,31),D(1),"USD","ONES","STANDALONE","IFRS")]
  self.assertEqual(construct_ttm(mismatch).reason,"INCOMPATIBLE_PERIOD_METADATA")
 def test_historical_growth_requires_matching_periods_and_metadata(self):
  current=PeriodValue(date(2025,1,1),date(2025,12,31),D(120),"UZS","ONES","STANDALONE","IFRS")
  prior=PeriodValue(date(2024,1,1),date(2024,12,31),D(100),"UZS","ONES","STANDALONE","IFRS")
  self.assertEqual(historical_growth(current,prior,1).value,D("0.2"))
  bad=PeriodValue(date(2024,4,1),date(2024,12,31),D(100),"UZS","ONES","STANDALONE","IFRS")
  self.assertEqual(historical_growth(current,bad,1).reason,"PERIOD_MISMATCH")
if __name__=='__main__': unittest.main()
