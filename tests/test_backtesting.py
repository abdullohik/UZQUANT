from datetime import date,datetime,timezone
from decimal import Decimal as D

from uzquant.backtesting import CostModel,TradeBar,apply_verified_split,delisting_outcome,financial_documents_as_of,macro_vintages_as_of,simulate_order,universe_as_of,verified_cash_dividend


def test_future_filing_and_restatement_leakage():
    docs=[{"document_id":"original","issuer_id":"i","period_end":"2023-12-31","publication_date":"2024-02-01","reporting_perimeter":"CONSOLIDATED","accounting_standard":"IFRS"},{"document_id":"restated","issuer_id":"i","period_end":"2023-12-31","publication_date":"2024-05-01","reporting_perimeter":"CONSOLIDATED","accounting_standard":"IFRS"}]
    assert financial_documents_as_of(docs,date(2024,3,1))[0]["document_id"]=="original"
    assert financial_documents_as_of(docs,date(2024,6,1))[0]["document_id"]=="restated"


def test_future_macro_vintage_leakage():
    rows=[{"observation_id":"old","series_id":"cpi","period_start":"2023-12-01","period_end":"2023-12-31","vintage_known_at":"2024-01-10T00:00:00+00:00"},{"observation_id":"revised","series_id":"cpi","period_start":"2023-12-01","period_end":"2023-12-31","vintage_known_at":"2024-03-10T00:00:00+00:00"}]
    assert macro_vintages_as_of(rows,datetime(2024,2,1,tzinfo=timezone.utc))[0]["observation_id"]=="old"
    assert macro_vintages_as_of(rows,datetime(2024,4,1,tzinfo=timezone.utc))[0]["observation_id"]=="revised"


def test_future_corporate_action_and_dividend_are_not_applied():
    assert apply_verified_split(D("10"),D("2"),date(2024,5,1),date(2024,6,1),date(2024,4,1),True)==D("10")
    assert apply_verified_split(D("10"),D("2"),date(2024,5,1),date(2024,6,1),date(2024,6,1),True)==D("20")
    assert verified_cash_dividend(D("10"),D("5"),date(2024,5,1),date(2024,6,1),date(2024,4,1))==0


def test_historical_universe_includes_later_delisted_security():
    rows=[{"security_id":"failed","known_at":"2020-01-01","listing_date":"2018-01-01","delisting_date":"2022-01-01"},{"security_id":"survivor","known_at":"2020-01-01","listing_date":"2018-01-01","delisting_date":None}]
    assert universe_as_of(rows,date(2021,1,1))=={"failed","survivor"}
    assert universe_as_of(rows,date(2023,1,1))=={"survivor"}


def test_unrealistic_fill_is_partial_and_volume_limited():
    bars=[TradeBar("a",date(2024,1,2),D("100"),D("100")),TradeBar("b",date(2024,1,3),D("101"),D("100"))]
    result=simulate_order("BUY",D("100"),date(2024,1,1),bars,D("0.1"),CostModel(),max_fill_days=2)
    assert result.status=="PARTIALLY_FILLED" and result.filled_shares==D("20") and result.unfilled_shares==D("80")


def test_stale_or_zero_trade_price_cannot_execute():
    bars=[TradeBar("stale",date(2024,1,1),D("100"),D("100")),TradeBar("zero",date(2024,1,3),D("100"),D("0"),False)]
    result=simulate_order("BUY",D("10"),date(2024,1,2),bars,D("0.1"),CostModel())
    assert result.status=="REJECTED" and result.filled_shares==0


def test_fees_slippage_and_delay_are_in_fill_ledger():
    bars=[TradeBar("same",date(2024,1,1),D("100"),D("1000")),TradeBar("next",date(2024,1,2),D("100"),D("1000"),True,D("0.02"))]
    result=simulate_order("BUY",D("10"),date(2024,1,1),bars,D("0.1"),CostModel(D(".001"),D(".002"),D(".003"),D(".004"),D(".01")))
    fill=result.fills[0]
    assert fill.observation_id=="next" and fill.fill_price==D("102.00")
    assert fill.transaction_fee>0 and fill.depository_fee>0 and fill.slippage_value==D("20.00")


def test_delisting_is_not_silently_dropped():
    unresolved=delisting_outcome(D("100"),None); settled=delisting_outcome(D("100"),D("4"))
    assert unresolved["status"]=="UNRESOLVED_DELISTING" and unresolved["shares"]==D("100")
    assert settled=={"status":"CASH_SETTLED","cash":D("400"),"shares":D("0")}
