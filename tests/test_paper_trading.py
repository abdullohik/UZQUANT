import sqlite3
from datetime import date,datetime,timezone
from decimal import Decimal

import pytest

from uzquant.backtesting import CostModel,TradeBar
from uzquant.operations import register_pipelines
from uzquant.paper_trading import AccountState,apply_dividend,apply_fill,capture_prospective_state,execute_with_future_bars,settle_paper_order,submit_paper_order
from uzquant.repository import Repository

D=Decimal


def bars():
    return [TradeBar("old",date(2025,12,31),D("90"),D("100")),TradeBar("one",date(2026,1,2),D("100"),D("20")),TradeBar("two",date(2026,1,3),D("110"),D("20"))]


def seed_signal(repo):
    repo.connection.execute("INSERT INTO issuers(issuer_id,legal_name,resolution_method,created_at) VALUES('i','Issuer','TEST','2025-01-01')")
    repo.connection.execute("INSERT INTO securities VALUES('s','i','COMMON','EQUITY',NULL,'UZS','2025-01-01')")
    repo.connection.execute("INSERT INTO research_signals VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",('sig','s','DATA_INSUFFICIENT',None,'20','{}','["DATA_QUALITY_CRITICAL"]','{}','signal/1','score/1','valuation/1','liquidity/1','snapshot-1','2026-01-01T00:00:00+00:00'))
    repo.connection.commit()


def test_prospective_snapshot_is_immutable_and_preserves_staleness(tmp_path):
    database=tmp_path/'paper.sqlite3'
    with Repository(database) as repo:
        repo.initialize();register_pipelines(repo);seed_signal(repo)
    result=capture_prospective_state(database,datetime(2026,1,2,tzinfo=timezone.utc))
    assert result['shadow_portfolios']==3 and result['signals_captured']==1
    assert result['upstream_state']=='STALE' and result['paper_orders']==0
    with Repository(database) as repo:
        snapshot=repo.connection.execute("SELECT * FROM prospective_decision_snapshots").fetchone()
        state=repo.connection.execute("SELECT * FROM prospective_security_states").fetchone()
        assert state['signal_id']=='sig' and 'signal/1' in state['model_versions_json']
        with pytest.raises(sqlite3.IntegrityError): repo.connection.execute("UPDATE prospective_decision_snapshots SET trigger_type='CHANGED' WHERE prospective_snapshot_id=?",(snapshot['prospective_snapshot_id'],))


def test_future_knowledge_is_excluded_and_partial_fills_span_days():
    result=execute_with_future_bars('BUY',D('30'),datetime(2026,1,1,tzinfo=timezone.utc),bars(),D('0.5'),CostModel())
    assert result.status=='PARTIALLY_FILLED' and result.filled_shares==D('20')
    assert [fill.observation_id for fill in result.fills]==['one','two']


def test_no_observed_trade_produces_no_fill_result():
    no_trade=[TradeBar('n',date(2026,1,2),D('100'),D('0'),False)]
    result=execute_with_future_bars('BUY',D('10'),datetime(2026,1,1,tzinfo=timezone.utc),no_trade,D('0.1'),CostModel())
    assert result.filled_shares==0 and result.reason=='NO_EXECUTABLE_OBSERVED_VOLUME'


def test_fees_and_portfolio_accounting():
    bought=apply_fill(AccountState(D('1000')),'BUY',D('5'),D('100'),D('10'))
    assert bought.cash==D('490') and bought.cost_basis==D('510') and bought.fees==D('10')
    sold=apply_fill(bought,'SELL',D('2'),D('120'),D('4'))
    assert sold.shares==D('3') and sold.realized_pnl==D('32') and sold.cash==D('726')


def test_dividend_requires_information_and_payment_to_be_known():
    state=AccountState(D('0'),D('10'))
    early=apply_dividend(state,D('5'),date(2026,1,5),date(2026,1,20),datetime(2026,1,10,tzinfo=timezone.utc))
    paid=apply_dividend(state,D('5'),date(2026,1,5),date(2026,1,20),datetime(2026,1,21,tzinfo=timezone.utc))
    assert early.cash==0 and paid.cash==D('50') and paid.dividends==D('50')


def test_stale_snapshot_rejects_order_without_forcing_position(tmp_path):
    database=tmp_path/'paper.sqlite3'
    with Repository(database) as repo:
        repo.initialize();register_pipelines(repo);seed_signal(repo)
    result=capture_prospective_state(database,datetime(2026,1,2,tzinfo=timezone.utc))
    with Repository(database) as repo:
        portfolio=repo.connection.execute("SELECT shadow_portfolio_id FROM shadow_portfolios LIMIT 1").fetchone()[0]
        order=submit_paper_order(repo,portfolio,result['snapshot_id'],'s','BUY',D('10'),D('0.1'),datetime(2026,1,2,tzinfo=timezone.utc),D('100'))
        row=repo.connection.execute("SELECT status,reason FROM paper_orders WHERE paper_order_id=?",(order,)).fetchone()
        assert row['status']=='REJECTED' and row['reason']=='PROSPECTIVE_ADMISSION_BLOCKED'
        assert repo.connection.execute("SELECT count(*) FROM paper_positions").fetchone()[0]==0


def test_open_order_with_no_future_market_evidence_is_recorded_no_fill(tmp_path):
    database=tmp_path/'paper.sqlite3'
    with Repository(database) as repo:
        repo.initialize();register_pipelines(repo);seed_signal(repo)
    result=capture_prospective_state(database,datetime(2026,1,2,tzinfo=timezone.utc))
    with Repository(database) as repo:
        portfolio=repo.connection.execute("SELECT shadow_portfolio_id FROM shadow_portfolios LIMIT 1").fetchone()[0]
        order=submit_paper_order(repo,portfolio,result['snapshot_id'],'s','BUY',D('10'),D('0.1'),datetime(2026,1,2,tzinfo=timezone.utc),D('100'))
        repo.connection.execute("UPDATE paper_orders SET status='OPEN',reason=NULL WHERE paper_order_id=?",(order,))
        settled=settle_paper_order(repo,order,datetime(2026,1,5,tzinfo=timezone.utc))
        assert settled.filled_shares==0
        assert repo.connection.execute("SELECT status FROM paper_orders WHERE paper_order_id=?",(order,)).fetchone()[0]=='NO_FILL'
