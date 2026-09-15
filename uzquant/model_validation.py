from __future__ import annotations

import json
import math
import random
import statistics
import uuid
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path

from .backtesting import readiness
from .repository import Repository, utc_now

D=Decimal
VERSION="walk-forward-validation/1.0.0"
CLASSIFICATIONS=("ROBUST","PROMISING_BUT_UNPROVEN","FRAGILE","UNRELIABLE")


@dataclass(frozen=True)
class Split:
    number:int
    train:tuple[date,date]
    validation:tuple[date,date]|None
    out_of_sample:tuple[date,date]
    final_test_locked:bool


@dataclass(frozen=True)
class Experiment:
    name:str
    family:str
    parameters:dict
    hypothesis:str


EXPERIMENTS=(
 Experiment("BASELINE","BASELINE",{},"Declared reference model; no tuning on final OOS."),
 Experiment("EQUAL_FACTOR_WEIGHTS","FACTOR_WEIGHTS",{"weight_scheme":"equal"},"Results should not depend on one weight vector."),
 Experiment("LOWER_LIQUIDITY_THRESHOLDS","LIQUIDITY",{"threshold_multiplier":"0.75"},"Stricter liquidity eligibility should not destroy the thesis."),
 Experiment("CONFIDENCE_THRESHOLD_60","CONFIDENCE",{"minimum_confidence":"60"},"Higher evidence requirements should retain economic direction."),
 Experiment("DOUBLE_HOLDING_PERIOD","HOLDING_PERIOD",{"holding_period_multiplier":"2"},"Performance should not require one exact horizon."),
 Experiment("MONTHLY_REBALANCE","REBALANCE",{"frequency":"monthly"},"Results should tolerate a slower rebalance schedule."),
 Experiment("WIDER_VALUATION_SPREAD","VALUATION",{"bear_bull_spread_multiplier":"1.25"},"Valuation uncertainty should not reverse all results."),
 Experiment("HALF_POSITION_SIZE","POSITION_SIZING",{"position_multiplier":"0.5"},"Results should scale sensibly with smaller positions."),
 Experiment("HIGHER_FEES","COSTS",{"fee_multiplier":"2"},"Performance should survive materially higher verified/modelled costs."),
 Experiment("DOUBLE_SLIPPAGE","SLIPPAGE",{"slippage_multiplier":"2"},"Performance should survive twice the baseline slippage."),
 Experiment("THREE_DAY_DELAY","EXECUTION_DELAY",{"delay_days":"3"},"Performance should not depend on immediate fills."),
 Experiment("WORSE_FILLS","FILL_QUALITY",{"participation_multiplier":"0.5","slippage_multiplier":"1.5"},"Lower fill capacity and worse prices should remain tolerable."),
 Experiment("VALUATION_ERROR_MINUS_20","VALUATION_ERROR",{"fair_value_multiplier":"0.8"},"Conclusions should tolerate a 20% valuation error."),
 Experiment("ALTERNATE_FACTOR_WEIGHTS","FACTOR_WEIGHTS",{"valuation":"0.15","quality":"0.20","liquidity":"0.20"},"Economic direction should persist under a defensible alternate weighting."),
 Experiment("LOWER_LIQUIDITY","LIQUIDITY",{"adv_multiplier":"0.5"},"Capacity conclusions should survive half the observed liquidity."),
 Experiment("REMOVE_BEST_SECURITY","CONCENTRATION",{"remove":"best_security"},"Results should not be dominated by one security."),
 Experiment("REMOVE_BEST_PERIOD","TIME_CONCENTRATION",{"remove":"best_period"},"Results should not be dominated by one period."),
)


def chronological_split(dates:list[date],train_fraction=D("0.60"),validation_fraction=D("0.20"),minimum_each:int=1)->Split:
    unique=sorted(set(dates)); n=len(unique)
    if n<minimum_each*3: raise ValueError("insufficient dates for three chronological samples")
    train_n=max(minimum_each,int(D(n)*train_fraction)); valid_n=max(minimum_each,int(D(n)*validation_fraction))
    if train_n+valid_n>n-minimum_each: valid_n=n-minimum_each-train_n
    return Split(1,(unique[0],unique[train_n-1]),(unique[train_n],unique[train_n+valid_n-1]),(unique[train_n+valid_n],unique[-1]),True)


def rolling_splits(dates:list[date],train_size:int,validation_size:int,oos_size:int,step:int|None=None)->list[Split]:
    unique=sorted(set(dates)); step=step or oos_size
    if min(train_size,validation_size,oos_size,step)<=0: raise ValueError("split sizes must be positive")
    splits=[]; start=0
    while start+train_size+validation_size+oos_size<=len(unique):
        a=start+train_size; b=a+validation_size; c=b+oos_size
        splits.append(Split(len(splits)+1,(unique[start],unique[a-1]),(unique[a],unique[b-1]),(unique[b],unique[c-1]),False)); start+=step
    if splits:
        last=splits[-1]; splits[-1]=Split(last.number,last.train,last.validation,last.out_of_sample,True)
    return splits


def validate_experiment(experiment:Experiment,uses_final_oos_for_tuning:bool=False):
    if uses_final_oos_for_tuning: raise ValueError("final out-of-sample period is locked against tuning")
    if not experiment.name or not experiment.family or not experiment.hypothesis: raise ValueError("experiment must be fully registered")
    return experiment


def bootstrap_mean_interval(returns:list[Decimal],iterations:int=1000,confidence=D("0.95"),seed:int=7):
    if len(returns)<20 or iterations<100: return None
    rng=random.Random(seed); values=[]; n=len(returns)
    for _ in range(iterations): values.append(sum((returns[rng.randrange(n)] for _ in range(n)),D("0"))/D(n))
    values.sort(); alpha=(D("1")-confidence)/D("2"); lo=int(alpha*iterations); hi=min(iterations-1,int((D("1")-alpha)*iterations)-1)
    return values[lo],values[hi]


def factor_monotonicity(scores:list[Decimal],forward_returns:list[Decimal]):
    if len(scores)!=len(forward_returns) or len(scores)<10 or len(set(scores))<3: return None
    def ranks(values):
        order=sorted(range(len(values)),key=lambda i:(values[i],i)); result=[0]*len(values)
        for rank,index in enumerate(order): result[index]=rank+1
        return result
    x,y=ranks(scores),ranks(forward_returns); mx=statistics.mean(x); my=statistics.mean(y)
    num=sum((a-mx)*(b-my) for a,b in zip(x,y)); den=math.sqrt(sum((a-mx)**2 for a in x)*sum((b-my)**2 for b in y))
    return D(str(num/den)) if den else None


def remove_best_contributor(contributions:dict[str,Decimal]):
    if not contributions:return None
    best=max(contributions,key=lambda key:(contributions[key],key)); return best,sum((v for k,v in contributions.items() if k!=best),D("0"))


def classify_validation(baseline_return:Decimal|None,oos_periods:int,available_stresses:int,total_stresses:int,stress_survival_ratio:Decimal|None,max_single_security_share:Decimal|None,subperiod_positive_ratio:Decimal|None):
    if baseline_return is None or oos_periods<1 or available_stresses<3:return "UNRELIABLE"
    if baseline_return<=0:return "FRAGILE"
    if max_single_security_share is not None and max_single_security_share>D("0.35"):return "FRAGILE"
    if stress_survival_ratio is None or subperiod_positive_ratio is None:return "PROMISING_BUT_UNPROVEN"
    coverage=D(available_stresses)/D(total_stresses) if total_stresses else D("0")
    if oos_periods>=3 and coverage>=D("0.8") and stress_survival_ratio>=D("0.75") and subperiod_positive_ratio>=D("0.67"):return "ROBUST"
    if stress_survival_ratio<D("0.5") or subperiod_positive_ratio<D("0.5"):return "FRAGILE"
    return "PROMISING_BUT_UNPROVEN"


def run_model_validation(database:Path):
    with Repository(database) as repo:
        repo.initialize(); backtest_reasons=readiness(repo); completed=repo.connection.execute("SELECT count(*) FROM backtest_runs WHERE status='COMPLETED'").fetchone()[0]
        reasons=list(backtest_reasons)
        if completed==0:reasons.append("NO_COMPLETED_POINT_IN_TIME_BACKTEST")
        classification=classify_validation(None,0,0,len(EXPERIMENTS)-1,None,None,None); run_id=str(uuid.uuid4()); now=utc_now()
        repo.connection.execute("INSERT INTO validation_runs VALUES(?,?,?,?,?,?,?)",(run_id,"Overall Ranking + Liquidity Gates",classification,"DATA_INSUFFICIENT",json.dumps(reasons),VERSION,now))
        experiment_ids={}
        for experiment in EXPERIMENTS:
            validate_experiment(experiment); eid=str(uuid.uuid4()); experiment_ids[experiment.name]=eid
            repo.connection.execute("INSERT INTO experiment_registry VALUES(?,?,?,?,?,?,?,?,?,?,?)",(eid,run_id,experiment.name,experiment.family,experiment_ids.get("BASELINE") if experiment.name!="BASELINE" else None,json.dumps(experiment.parameters,sort_keys=True),experiment.hypothesis,now,0,"DATA_INSUFFICIENT",json.dumps({"reason":"NO_COMPLETED_POINT_IN_TIME_BACKTEST"})))
            repo.connection.execute("INSERT INTO robustness_results VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(str(uuid.uuid4()),eid,None,"PRODUCTION",None,None,None,None,None,None,None,"UNAVAILABLE","NO_COMPLETED_POINT_IN_TIME_BACKTEST",now))
        risks=(("DATA_COVERAGE","CRITICAL",{"reasons":reasons}),("SINGLE_SECURITY_DEPENDENCE","HIGH",{"status":"UNTESTABLE"}),("SINGLE_PERIOD_DEPENDENCE","HIGH",{"status":"UNTESTABLE"}),("SECTOR_DEPENDENCE","HIGH",{"status":"UNTESTABLE"}),("ILLIQUID_EVENT_DEPENDENCE","HIGH",{"status":"UNTESTABLE"}),("PARAMETER_DEPENDENCE","HIGH",{"status":"UNTESTABLE"}),("VALUATION_ASSUMPTION_DEPENDENCE","HIGH",{"status":"UNTESTABLE"}))
        for kind,severity,evidence in risks:repo.connection.execute("INSERT INTO model_risk_findings VALUES(?,?,?,?,?,?)",(str(uuid.uuid4()),run_id,kind,severity,json.dumps(evidence,sort_keys=True),now))
        repo.connection.commit(); return {"validation_run_id":run_id,"status":"DATA_INSUFFICIENT","classification":classification,"experiments_registered":len(EXPERIMENTS),"reasons":reasons,"model_risks":len(risks)}
