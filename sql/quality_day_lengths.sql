-- Local days that do not have 24 hours (clock changes).
SELECT
    day,
    COUNT(*) AS hours
FROM hourly_enriched
GROUP BY day
HAVING COUNT(*) <> 24
ORDER BY day;
