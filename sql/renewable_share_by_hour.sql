-- Renewable share of load by hour of the day (local time) and season.
SELECT
    season,
    hour,
    ROUND(100.0 * SUM(renewables) / SUM(load), 1) AS renewable_share_pct
FROM hourly_enriched
GROUP BY season, hour
ORDER BY season, hour;
