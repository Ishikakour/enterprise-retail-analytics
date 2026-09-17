-- ============================================================
-- Enterprise Retail Analytics — SQL queries used by app.py
-- DuckDB syntax. Column names match the ETL order grain:
--   product_category, year_month, customer_state, payment_value,
--   profit, is_loss, order_id
-- The dashboard parameterizes the WHERE clause (state / category).
-- Examples below use São Paulo + bed_bath_table.
-- ============================================================

-- Query 1: KPI aggregation for a filtered segment
SELECT
    SUM(payment_value) AS revenue,
    SUM(profit) AS total_profit,
    COUNT(DISTINCT order_id) AS orders,
    100.0 * AVG(CASE WHEN is_loss THEN 1 ELSE 0 END) AS loss_pct
FROM orders
WHERE customer_state = 'SP'
  AND product_category = 'bed_bath_table';


-- Query 2: Profit by category with DENSE_RANK
WITH cat_profit AS (
    SELECT
        REPLACE(product_category, '_', ' ') AS category,
        SUM(profit) AS profit,
        COUNT(*) AS orders
    FROM orders
    WHERE customer_state = 'SP'
      AND product_category IS NOT NULL
      AND product_category <> ''
    GROUP BY product_category
)
SELECT
    category, profit, orders,
    DENSE_RANK() OVER (ORDER BY profit DESC) AS profit_rank
FROM cat_profit
ORDER BY profit ASC;


-- Query 3: Monthly profit with running total
-- year_month (YYYY-MM) is used instead of calendar month names so
-- 2017-01 and 2018-01 are not collapsed together.
WITH monthly AS (
    SELECT year_month, SUM(profit) AS profit
    FROM orders
    WHERE customer_state = 'SP'
    GROUP BY year_month
)
SELECT
    year_month,
    profit,
    SUM(profit) OVER (ORDER BY year_month) AS running_profit
FROM monthly
ORDER BY year_month;
