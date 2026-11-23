-- One row per hour. Energy in MWh per hour, price in EUR/MWh.
CREATE TABLE hourly (
    timestamp_utc      TEXT PRIMARY KEY,
    timestamp_local    TEXT NOT NULL,
    load               REAL,
    solar              REAL,
    wind_onshore       REAL,
    wind_offshore      REAL,
    biomass            REAL,
    hydro              REAL,
    other_renewables   REAL,
    lignite            REAL,
    hard_coal          REAL,
    gas                REAL,
    nuclear            REAL,
    pumped_storage     REAL,
    other_conventional REAL,
    price              REAL
);

-- Calendar fields (local German time) and derived values used by the queries
CREATE VIEW hourly_enriched AS
SELECT
    timestamp_utc,
    timestamp_local,
    date(timestamp_local) AS day,
    CAST(strftime('%Y', timestamp_local) AS INTEGER) AS year,
    CAST(strftime('%m', timestamp_local) AS INTEGER) AS month,
    CAST(strftime('%H', timestamp_local) AS INTEGER) AS hour,
    CAST(strftime('%w', timestamp_local) AS INTEGER) AS weekday,  -- 0 = Sunday
    CASE
        WHEN strftime('%m', timestamp_local) IN ('12', '01', '02') THEN 'winter'
        WHEN strftime('%m', timestamp_local) IN ('03', '04', '05') THEN 'spring'
        WHEN strftime('%m', timestamp_local) IN ('06', '07', '08') THEN 'summer'
        ELSE 'autumn'
    END AS season,
    load,
    solar + wind_onshore + wind_offshore + biomass + hydro + other_renewables AS renewables,
    load - wind_onshore - wind_offshore - solar AS residual_load,
    price
FROM hourly;
