-- Price and frequency of negative prices by residual load band (load - wind - PV).
WITH banded AS (
    SELECT
        price,
        CASE
            WHEN residual_load < 0     THEN 0
            WHEN residual_load < 10000 THEN 1
            WHEN residual_load < 20000 THEN 2
            WHEN residual_load < 30000 THEN 3
            WHEN residual_load < 40000 THEN 4
            WHEN residual_load < 50000 THEN 5
            ELSE 6
        END AS band
    FROM hourly_enriched
    WHERE price IS NOT NULL
)
SELECT
    CASE band
        WHEN 0 THEN '< 0 GW'
        WHEN 6 THEN '>= 50 GW'
        ELSE ((band - 1) * 10) || '-' || (band * 10) || ' GW'
    END AS residual_load_band,
    COUNT(*) AS hours,
    ROUND(AVG(price), 1) AS avg_price,
    SUM(price < 0) AS negative_hours,
    ROUND(100.0 * SUM(price < 0) / COUNT(*), 1) AS negative_share_pct
FROM banded
GROUP BY band
ORDER BY band;
