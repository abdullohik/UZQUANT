ALTER TABLE market_observations ADD COLUMN observation_status TEXT NOT NULL DEFAULT 'TRADE_REPORTED' CHECK(observation_status IN('TRADE_REPORTED','NO_TRADE_PLACEHOLDER'));
UPDATE market_observations SET observation_status='NO_TRADE_PLACEHOLDER' WHERE CAST(share_volume AS REAL)=0;
