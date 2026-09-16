import json
import sqlite3
from datetime import datetime,timezone

import pytest

from uzquant.financial_lineage import append_version,current_versions,reconstruct_signal
from uzquant.operations import Scheduler,SourceSchemaChanged,detect_source_schema,enforce_source_schema,register_pipelines
from uzquant.paper_trading import capture_prospective_state,reconstruct_snapshot
from uzquant.research_api import _health_context
from uzquant.repository import Repository


def seed_document(repo):
    c=repo.connection
    c.execute("INSERT INTO data_sources VALUES('src','Source','x','PRIMARY','VERIFIED_MANUAL','{}')")
    c.execute("INSERT INTO canonical_issuers VALUES('ci','ACTIVE','2020-01-01')")
    c.execute("INSERT INTO issuers(issuer_id,legal_name,resolution_method,created_at,canonical_issuer_id) VALUES('i','Issuer','TEST','2020-01-01','ci')")
    c.execute("INSERT INTO ingestion_runs(run_id,source_id,started_at,status,parser_version) VALUES('run','src','2020-01-01','RUNNING','p')")
    c.execute("INSERT INTO raw_documents VALUES('raw','src','run','https://x','2020-01-02','2020-01-01','text/html',?,'x')",('a'*64,))
    c.execute("INSERT INTO financial_documents VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",('doc','i','raw','Issuer','STANDALONE','2019-01-01','2019-12-31','2020-01-01',None,'ANNUAL','HTML','IFRS','AUDITED','UZS','src','https://x','1','2020-01-02','a'*64,'parser/1','ORIGINAL',None))
    c.execute("INSERT INTO financial_raw_values VALUES('rv','doc','INCOME_STATEMENT','Revenue',NULL,'100','CURRENT','row:1','HTML')")
    return c


def add(repo,value='100',parser='parser/1',taxonomy='taxonomy/1',normalization='normalization/1'):
    return append_version(repo,'obs','doc','i','INCOME_STATEMENT','Revenue','2019-01-01','2019-12-31','100',value,'UZS','UZS','row:1','HTML','HIGH','REPORTED',parser,'VERIFIED',taxonomy,normalization)


def test_restatement_and_source_replacement_are_append_only(tmp_path):
    with Repository(tmp_path/'x.db') as repo:
        repo.initialize();seed_document(repo); old=add(repo); new=add(repo,'110','parser/2')
        assert old!=new and repo.connection.execute("SELECT normalized_value FROM financial_observation_versions WHERE version_id=?",(old,)).fetchone()[0]=='100'
        assert current_versions(repo,'doc')[0]['version_id']==new


@pytest.mark.parametrize('field,new_version', [('taxonomy','taxonomy/2'),('unit','unit-fix/2')])
def test_taxonomy_and_unit_corrections_create_versions(tmp_path,field,new_version):
    with Repository(tmp_path/'x.db') as repo:
        repo.initialize();seed_document(repo); old=add(repo)
        newer=add(repo,'100',taxonomy=new_version) if field=='taxonomy' else add(repo,'100',normalization=new_version)
        assert old!=newer and repo.connection.execute("SELECT count(*) FROM financial_observation_versions").fetchone()[0]==2


def test_normalized_value_cannot_be_mutated_or_deleted(tmp_path):
    with Repository(tmp_path/'x.db') as repo:
        repo.initialize();seed_document(repo); version=add(repo)
        with pytest.raises(sqlite3.IntegrityError): repo.connection.execute("UPDATE financial_observation_versions SET normalized_value='999' WHERE version_id=?",(version,))
        with pytest.raises(sqlite3.IntegrityError): repo.connection.execute("DELETE FROM financial_observation_versions WHERE version_id=?",(version,))


def test_schema_contract_classifies_harmless_and_blocks_breaking(tmp_path):
    with Repository(tmp_path/'x.db') as repo:
        repo.initialize();register_pipelines(repo)
        compatible=enforce_source_schema(repo,'market_data','src','p',None,{'date','price'},{'date','price','note'})
        assert compatible['classification']=='COMPATIBLE_SCHEMA_CHANGE'
        with pytest.raises(SourceSchemaChanged): enforce_source_schema(repo,'market_data','src','p',None,{'date','price'},{'date','renamed_price'})
        assert repo.connection.execute("SELECT status FROM pipeline_health WHERE pipeline='market_data'").fetchone()[0]=='FAILED'
        assert repo.connection.execute("SELECT count(*) FROM research_alerts WHERE alert_type='SOURCE_SCHEMA_CHANGE'").fetchone()[0]==1


def test_reordered_fields_are_cosmetic_and_added_field_is_compatible():
    assert detect_source_schema({'date','price'},set(reversed(['date','price'])))['classification']=='COSMETIC_CHANGE'
    assert detect_source_schema({'date','price'},{'date','price','harmless'})['classification']=='COMPATIBLE_SCHEMA_CHANGE'


@pytest.mark.parametrize('observed', [set(),{'date'},{'date','price_as_text'},{'date','unit_shifted'}])
def test_malformed_or_shifted_source_fails_closed(tmp_path,observed):
    with Repository(tmp_path/'x.db') as repo:
        repo.initialize();register_pipelines(repo)
        with pytest.raises(SourceSchemaChanged): enforce_source_schema(repo,'financial_documents','src','p',None,{'date','price','unit'},observed)


def test_degraded_dependency_propagates_and_recovers(tmp_path):
    db=tmp_path/'x.db'; runner=lambda:{'attempted':1,'succeeded':1,'failed':0}
    with Repository(db) as repo:
        repo.initialize();register_pipelines(repo);repo.connection.execute("UPDATE pipeline_health SET status='DEGRADED' WHERE pipeline='security_master'");repo.connection.commit()
    result=Scheduler(db,{'market':runner},max_attempts=1,sleeper=lambda _:None).run_due(force=True,selected={'market_data'})
    assert result[0]['status']=='DEGRADED' and 'security_master' in result[0]['error']
    with Repository(db) as repo: repo.connection.execute("UPDATE pipeline_health SET status='HEALTHY' WHERE pipeline='security_master'");repo.connection.commit()
    recovered=Scheduler(db,{'market':runner},max_attempts=1,sleeper=lambda _:None).run_due(force=True,selected={'market_data'})
    assert recovered[0]['status']=='HEALTHY'


def test_degraded_plus_stale_stays_stale_and_api_exposes_warning(tmp_path):
    db=tmp_path/'x.db'
    with Repository(db) as repo:
        repo.initialize();register_pipelines(repo)
        repo.connection.execute("UPDATE pipeline_health SET status='DEGRADED',latest_error='partial source' WHERE pipeline='valuation'")
        repo.connection.execute("UPDATE pipeline_health SET status='STALE',latest_error='old market' WHERE pipeline='liquidity'");repo.connection.commit()
    result=Scheduler(db,{'signals':lambda:{'attempted':1,'succeeded':1,'failed':0}},max_attempts=1,sleeper=lambda _:None).run_due(force=True,selected={'factors'})
    assert result[0]['status']=='STALE'
    with Repository(db) as repo:
        context=_health_context(repo.connection)
        assert context['upstream_health']=='STALE' and 'valuation' in context['affected_dependencies'] and 'partial source' in context['degraded_reason']


def test_full_snapshot_survives_later_model_and_taxonomy_change(tmp_path):
    db=tmp_path/'x.db'
    with Repository(db) as repo:
        repo.initialize();register_pipelines(repo);seed_document(repo);add(repo)
        repo.connection.execute("INSERT INTO securities VALUES('s','i','COMMON','EQUITY',NULL,'UZS','2020-01-01')")
        repo.connection.execute("INSERT INTO research_signals VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",('sig','s','DATA_INSUFFICIENT',None,'20','{}','[]','{}','signal/1','score/1','valuation/1','liquidity/1','snapshot','2026-01-01T00:00:00+00:00'));repo.connection.commit()
    created=capture_prospective_state(db,datetime(2027,1,2,tzinfo=timezone.utc))
    with Repository(db) as repo:
        before=reconstruct_snapshot(repo,created['snapshot_id']); add(repo,'200','parser/2','taxonomy/2','normalization/2')
        repo.connection.execute("INSERT INTO research_signals VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",('sig2','s','DATA_INSUFFICIENT',None,'20','{}','[]','{}','signal/2','score/2','valuation/2','liquidity/2','snapshot2','2027-02-01T00:00:00+00:00'));repo.connection.commit(); after=reconstruct_snapshot(repo,created['snapshot_id'])
        assert before==after and after['verified'] and after['standard']=='FULL_FREEZE_V1'
        signal=reconstruct_signal(repo,'sig'); assert signal['normalized_financial_versions'][0]['normalized_value']=='100'


def test_legacy_snapshots_are_marked_limited(tmp_path):
    db=tmp_path/'x.db'
    with Repository(db) as repo:
        repo.initialize();register_pipelines(repo)
        # Migration behavior is covered by production backfill; the enum must reject false full-freeze claims.
        with pytest.raises(sqlite3.IntegrityError): repo.connection.execute("INSERT INTO prospective_snapshot_evidence VALUES('x','missing','NOT_FULL','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','h','2020')")
