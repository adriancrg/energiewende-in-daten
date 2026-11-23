-- Renewable share and average load by day of the week (Monday first).
SELECT
    CASE weekday
        WHEN 1 THEN 'Mon' WHEN 2 THEN 'Tue' WHEN 3 THEN 'Wed' WHEN 4 THEN 'Thu'
        WHEN 5 THEN 'Fri' WHEN 6 THEN 'Sat' ELSE 'Sun'
    END AS weekday_name,
    ROUND(AVG(load) / 1000, 1) AS avg_load_gw,
    ROUND(100.0 * SUM(renewables) / SUM(load), 1) AS renewable_share_pct
FROM hourly_enriched
GROUP BY weekday
ORDER BY (weekday + 6) % 7;
