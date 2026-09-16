from datetime import datetime,timezone
from decimal import Decimal

from uzquant.operations import Scheduler,detect_source_schema,numeric_jump,record_alert,record_source_schema_check,register_pipelines,signal_transition
from uzquant.repository import Repository


def test_scheduler_retries_records_health_and_is_not_due_twice(tmp_path):
    database=tmp_path/"ops.sqlite3"; calls=[]
    def flaky():
        calls.append(1)
        if len(calls)==1: raise ConnectionError("source unavailable")
        return {"attempted":3,"succeeded":3,"failed":0}
    scheduler=Scheduler(database,{"security":flaky},max_attempts=2,sleeper=lambda _:None)
    first=scheduler.run_due(force=True,selected={"security_master"},now=datetime(2026,1,1,tzinfo=timezone.utc))
    second=scheduler.run_due(force=False,selected={"security_master"},now=datetime(2026,1,1,tzinfo=timezone.utc))
    assert first[0]["status"]=="HEALTHY" and first[0]["retry_state"]=="SUCCEEDED_ATTEMPT_2"
    assert second==[]
    with Repository(database) as repo:
        assert repo.connection.execute("SELECT count(*) FROM scheduled_pipeline_runs").fetchone()[0]==1


def test_persistent_source_failure_is_explicit_and_alerted(tmp_path):
    database=tmp_path/"ops.sqlite3"
    scheduler=Scheduler(database,{"security":lambda:(_ for _ in ()).throw(RuntimeError("parser failure"))},max_attempts=2,sleeper=lambda _:None)
    result=scheduler.run_due(force=True,selected={"security_master"})
    assert result[0]["status"]=="FAILED" and "parser failure" in result[0]["error"]
    with Repository(database) as repo:
        health=repo.connection.execute("SELECT status,latest_error FROM pipeline_health WHERE pipeline='security_master'").fetchone()
        assert health[0]=="FAILED" and "parser failure" in health[1]
        assert repo.connection.execute("SELECT count(*) FROM research_alerts WHERE alert_type='PIPELINE_FAILED'").fetchone()[0]==1


def test_recovery_resolves_pipeline_failure_alert(tmp_path):
    database=tmp_path/"ops.sqlite3"; failing=True
    def runner():
        if failing: raise RuntimeError("temporary failure")
        return {"attempted":1,"succeeded":1,"failed":0}
    scheduler=Scheduler(database,{"security":runner},max_attempts=1,sleeper=lambda _:None)
    scheduler.run_due(force=True,selected={"security_master"})
    failing=False
    scheduler.run_due(force=True,selected={"security_master"})
    with Repository(database) as repo:
        alert=repo.connection.execute("SELECT status,resolved_at FROM research_alerts WHERE alert_type='PIPELINE_FAILED'").fetchone()
        assert alert[0]=="RESOLVED" and alert[1]


def test_upstream_staleness_blocks_downstream(tmp_path):
    database=tmp_path/"ops.sqlite3";scheduler=Scheduler(database,{"market":lambda:{"attempted":1,"succeeded":1,"failed":0}},sleeper=lambda _:None)
    result=scheduler.run_due(force=True,selected={"market_data"})
    assert result[0]["status"]=="STALE" and "security_master" in result[0]["error"]


def test_alert_deduplication(tmp_path):
    with Repository(tmp_path/"ops.sqlite3") as repo:
        repo.initialize();register_pipelines(repo)
        assert record_alert(repo,"STALE_SOURCE","WARNING","PIPELINE","market_data","stale","stale",dedupe_key="same")
        assert record_alert(repo,"STALE_SOURCE","WARNING","PIPELINE","market_data","stale","stale",dedupe_key="same") is None
        repo.connection.commit();assert repo.connection.execute("SELECT count(*) FROM research_alerts").fetchone()[0]==1


def test_source_schema_change_fails_closed():
    result=detect_source_schema({"ticker","price","volume"},{"ticker","price","renamed_volume"})
    assert result["status"]=="FAILED" and result["missing"]==["volume"]


def test_source_schema_change_creates_configurable_alert(tmp_path):
    with Repository(tmp_path/"ops.sqlite3") as repo:
        repo.initialize();register_pipelines(repo)
        result=record_source_schema_check(repo,"market_data",{"price","volume"},{"price"})
        assert result["status"]=="FAILED"
        assert repo.connection.execute("SELECT count(*) FROM research_alerts WHERE alert_type='SOURCE_SCHEMA_CHANGE'").fetchone()[0]==1
        repo.connection.execute("UPDATE alert_rules SET enabled=0 WHERE alert_type='SOURCE_SCHEMA_CHANGE'")
        assert record_source_schema_check(repo,"security_master",{"ticker"},set())["status"]=="FAILED"
        assert repo.connection.execute("SELECT count(*) FROM research_alerts WHERE alert_type='SOURCE_SCHEMA_CHANGE'").fetchone()[0]==1


def test_anomaly_and_signal_transition_rules():
    assert numeric_jump(Decimal("100"),Decimal("1000000"))
    assert signal_transition("DATA_INSUFFICIENT","HOLD")
    assert not signal_transition("HOLD","HOLD")
