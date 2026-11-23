-- Hours with negative wholesale prices per year. Hours without a price are ignored.
SELECT
    year,
    COUNT(price) AS hours_with_price,
    SUM(price < 0) AS negative_hours,
    ROUND(100.0 * SUM(price < 0) / COUNT(price), 1) AS negative_share_pct,
    ROUND(MIN(price), 1) AS min_price,
    ROUND(AVG(price), 1) AS avg_price
FROM hourly_enriched
GROUP BY year
ORDER BY year;
