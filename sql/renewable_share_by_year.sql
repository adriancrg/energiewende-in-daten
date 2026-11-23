-- Renewable share of load per year and change compared with the previous year.
-- The share is SUM / SUM (energy-weighted), not the average of hourly shares.
WITH yearly AS (
    SELECT
        year,
        COUNT(*) AS hours,
        100.0 * SUM(renewables) / SUM(load) AS share
    FROM hourly_enriched
    GROUP BY year
)
SELECT
    year,
    hours,
    ROUND(share, 1) AS renewable_share_pct,
    ROUND(share - LAG(share) OVER (ORDER BY year), 1) AS change_pct_points
FROM yearly
ORDER BY year;
