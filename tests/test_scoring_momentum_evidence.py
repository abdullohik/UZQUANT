from uzquant.scoring import momentum_factor


def test_momentum_reports_short_raw_history_only_when_count_is_below_threshold():
    factor = momentum_factor(59)

    assert factor.status == "UNAVAILABLE"
    assert factor.reason == "MARKET_HISTORY_BELOW_60_OBSERVATIONS"


def test_momentum_does_not_mislabel_sufficient_raw_observation_count():
    factor = momentum_factor(73)

    assert factor.status == "UNAVAILABLE"
    assert factor.reason == "NO_VERIFIED_CORPORATE_ACTION_ADJUSTED_RETURN_SERIES"
