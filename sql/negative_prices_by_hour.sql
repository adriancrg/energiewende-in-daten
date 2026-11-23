-- When do negative prices happen? Count by season, weekend and hour of the day.
SELECT
    season,
    CASE WHEN weekday IN (0, 6) THEN 'weekend' ELSE 'workday' END AS day_type,
    hour,
    SUM(price < 0) AS negative_hours
FROM hourly_enriched
WHERE price IS NOT NULL
GROUP BY season, day_type, hour
ORDER BY season, day_type, hour;
