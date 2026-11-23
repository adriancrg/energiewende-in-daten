-- Number of missing values per column.
SELECT
    COUNT(*) AS hours,
    SUM(load IS NULL) AS missing_load,
    SUM(solar IS NULL OR wind_onshore IS NULL OR wind_offshore IS NULL) AS missing_wind_solar,
    SUM(price IS NULL) AS missing_price
FROM hourly;
