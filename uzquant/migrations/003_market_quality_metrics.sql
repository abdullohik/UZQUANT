CREATE TABLE market_quality_metrics(
    metric_id TEXT PRIMARY KEY,
    security_id TEXT NOT NULL REFERENCES securities,
    as_of_date TEXT NOT NULL,
    observation_count INTEGER NOT NULL,
    trading_frequency TEXT,
    zero_trade_day_ratio TEXT,
    average_daily_share_volume TEXT,
    median_daily_share_volume TEXT,
    average_daily_trading_value TEXT,
    median_daily_trading_value TEXT,
    average_trade_count TEXT,
    median_trade_count TEXT,
    days_since_last_trade INTEGER,
    calendar_basis TEXT NOT NULL,
    market_run_id TEXT NOT NULL REFERENCES market_ingestion_runs,
    created_at TEXT NOT NULL,
    UNIQUE(security_id,as_of_date,market_run_id)
);
