import statistics
from datetime import date
from decimal import Decimal
def _average(v): return str(sum(v)/len(v)) if v else None
def _median(v): return str(statistics.median(v)) if v else None
def calculate_quality(rows,as_of:date,expected_trading_days=None):
    ordered=sorted(rows,key=lambda r:r["trade_date"]); volumes=[]; turnovers=[]; counts=[]; flags=[]
    for row in ordered:
        if row.get("share_volume") is None: flags.append((row["trade_date"],"MISSING_VOLUME","WARNING","Source supplied no volume"))
        else: volumes.append(Decimal(row["share_volume"]))
        if row.get("turnover_value") is not None: turnovers.append(Decimal(row["turnover_value"]))
        if row.get("trade_count") is not None: counts.append(Decimal(row["trade_count"]))
    for previous,current in zip(ordered,ordered[1:]):
        move=abs(Decimal(current["close"])/Decimal(previous["close"])-1)
        if move>=Decimal(".5"):
            flags.extend([(current["trade_date"],"ABNORMAL_PRICE_MOVE","WARNING",f"Absolute close move {move:.2%}"),(current["trade_date"],"POSSIBLE_CORPORATE_ACTION","WARNING","Large discontinuity requires investigation")])
        if move>=Decimal("9"): flags.append((current["trade_date"],"POSSIBLE_UNIT_CHANGE","ERROR","Close changed by at least 10x"))
        if move>=Decimal(".5") and current.get("trade_count")==1: flags.append((current["trade_date"],"SINGLE_TRADE_MOVE","WARNING","Large move with one reported trade"))
    traded=[r for r in ordered if r.get("observation_status","TRADE_REPORTED")=="TRADE_REPORTED"]
    observed={date.fromisoformat(r["trade_date"]) for r in traded}; days=(as_of-max(observed)).days if observed else None
    if days is not None and days>=20: flags.append((None,"VERY_STALE_PRICE","ERROR",f"{days} calendar days since last trade"))
    elif days is not None and days>=5: flags.append((None,"STALE_PRICE","WARNING",f"{days} calendar days since last trade"))
    if len(ordered)<20: flags.append((None,"LOW_OBSERVATION_COUNT","WARNING",f"Only {len(ordered)} observations"))
    expected=set(expected_trading_days or [])
    if expected: frequency=str(Decimal(len(observed&expected))/Decimal(len(expected))); zero=str(Decimal(len(expected-observed))/Decimal(len(expected))); basis="SUPPLIED_TRADING_CALENDAR"
    elif ordered and all("observation_status" in r for r in ordered):
        frequency=str(Decimal(len(traded))/Decimal(len(ordered))); zero=str(Decimal(len(ordered)-len(traded))/Decimal(len(ordered))); basis="SOURCE_REPORTED_DATES"
    else: frequency=zero=None; basis="UNAVAILABLE_SOURCE_CALENDAR"
    returns=[str(Decimal(b["close"])/Decimal(a["close"])-1) for a,b in zip(traded,traded[1:])]
    return {"observation_count":len(ordered),"trading_frequency":frequency,"zero_trade_day_ratio":zero,"average_daily_share_volume":_average(volumes),"median_daily_share_volume":_median(volumes),"average_daily_trading_value":_average(turnovers),"median_daily_trading_value":_median(turnovers),"average_trade_count":_average(counts),"median_trade_count":_median(counts),"days_since_last_trade":days,"observed_returns":returns,"calendar_basis":basis,"flags":flags}
