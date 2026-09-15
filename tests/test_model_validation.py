from datetime import date
from decimal import Decimal as D

import pytest

from uzquant.model_validation import EXPERIMENTS,Experiment,bootstrap_mean_interval,chronological_split,classify_validation,factor_monotonicity,remove_best_contributor,rolling_splits,validate_experiment


def days(n):return [date(2020,1,1).fromordinal(date(2020,1,1).toordinal()+i) for i in range(n)]


def test_train_validation_oos_are_chronological_and_final_locked():
    split=chronological_split(days(100))
    assert split.train[1]<split.validation[0]<=split.validation[1]<split.out_of_sample[0]
    assert split.final_test_locked


def test_rolling_walk_forward_never_overlaps_forward_in_time():
    splits=rolling_splits(days(120),60,20,20,20)
    assert len(splits)==2 and splits[-1].final_test_locked
    assert all(s.train[1]<s.validation[0] and s.validation[1]<s.out_of_sample[0] for s in splits)


def test_final_oos_cannot_be_used_for_tuning():
    with pytest.raises(ValueError):validate_experiment(Experiment("x","weights",{},"test"),True)


def test_experiment_registry_contains_all_required_perturbation_families():
    families={e.family for e in EXPERIMENTS}
    assert {"FACTOR_WEIGHTS","LIQUIDITY","CONFIDENCE","HOLDING_PERIOD","REBALANCE","VALUATION","POSITION_SIZING","COSTS","SLIPPAGE","EXECUTION_DELAY","FILL_QUALITY","VALUATION_ERROR","CONCENTRATION","TIME_CONCENTRATION"}<=families


def test_bootstrap_requires_sample_and_is_reproducible():
    values=[D(i)/D("100") for i in range(-10,20)]
    assert bootstrap_mean_interval(values,200,seed=5)==bootstrap_mean_interval(values,200,seed=5)
    assert bootstrap_mean_interval(values[:10]) is None


def test_factor_monotonicity_and_sample_gate():
    x=[D(i) for i in range(10)]
    assert factor_monotonicity(x,x)==D("1.0")
    assert factor_monotonicity(x[:5],x[:5]) is None


def test_remove_best_security_reports_remaining_result():
    assert remove_best_contributor({"A":D("0.6"),"B":D("0.2"),"C":D("-0.1")})==("A",D("0.1"))


def test_robust_label_requires_multiple_oos_and_stress_stability():
    assert classify_validation(D(".2"),3,9,10,D(".8"),D(".2"),D(".7"))=="ROBUST"
    assert classify_validation(D(".2"),1,9,10,D(".8"),D(".2"),D(".7"))=="PROMISING_BUT_UNPROVEN"
    assert classify_validation(None,0,0,10,None,None,None)=="UNRELIABLE"
    assert classify_validation(D(".2"),3,9,10,D(".8"),D(".5"),D(".7"))=="FRAGILE"
