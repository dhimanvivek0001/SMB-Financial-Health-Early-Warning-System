-- ad_hoc_queries.sql
-- Useful analysis queries for the SMB Financial Health project.
-- Run these directly in BigQuery console or bq CLI.

-- ── 1. Top 10 customers by lifetime value ────────────────────────────────────
SELECT
    customer_id,
    country,
    round(lifetime_value, 2)            AS lifetime_value,
    total_orders,
    round(avg_order_value, 2)           AS avg_order_value,
    date(first_purchase)                AS first_purchase,
    date(last_purchase)                 AS last_purchase
FROM `smb-finance-project.analytics.dim_customers`
ORDER BY lifetime_value DESC
LIMIT 10;


-- ── 2. Revenue trend — last 30 days ─────────────────────────────────────────
SELECT
    revenue_date,
    round(daily_revenue, 2)             AS daily_revenue,
    round(rolling_7d_avg, 2)            AS rolling_7d_avg,
    round(daily_revenue - rolling_7d_avg, 2) AS vs_avg
FROM `smb-finance-project.analytics.int_revenue_forecast`
ORDER BY revenue_date DESC
LIMIT 30;


-- ── 3. All active alerts ─────────────────────────────────────────────────────
SELECT
    revenue_date,
    round(daily_revenue, 2)             AS daily_revenue,
    round(rolling_7d_avg, 2)            AS rolling_7d_avg,
    pct_of_avg,
    alert_status
FROM `smb-finance-project.analytics.fct_alerts`
WHERE alert_status != 'NORMAL'
ORDER BY revenue_date DESC;


-- ── 4. Top 10 products by revenue ────────────────────────────────────────────
SELECT
    product_id,
    product_name,
    round(total_revenue, 2)             AS total_revenue,
    total_quantity_sold,
    transaction_lines,
    round(avg_unit_price, 2)            AS avg_unit_price
FROM `smb-finance-project.analytics.dim_products`
ORDER BY total_revenue DESC
LIMIT 10;


-- ── 5. Weekly revenue summary ────────────────────────────────────────────────
SELECT
    week_start,
    round(weekly_revenue, 2)            AS weekly_revenue,
    round(avg_daily_revenue, 2)         AS avg_daily_revenue,
    days_count
FROM `smb-finance-project.analytics.int_weekly_summary`
ORDER BY week_start DESC
LIMIT 12;


-- ── 6. Revenue anomalies (Z-score > 2 or < -2) ──────────────────────────────
SELECT
    revenue_date,
    round(daily_revenue, 2)             AS daily_revenue,
    round(z_score, 2)                   AS z_score,
    anomaly_flag
FROM `smb-finance-project.analytics.int_revenue_anomalies`
WHERE anomaly_flag != 'NORMAL'
ORDER BY abs(z_score) DESC;


-- ── 7. Revenue by country ────────────────────────────────────────────────────
SELECT
    country,
    count(distinct customer_id)         AS customers,
    count(distinct invoice_id)          AS invoices,
    round(sum(revenue), 2)              AS total_revenue
FROM `smb-finance-project.analytics.fct_transactions`
GROUP BY country
ORDER BY total_revenue DESC;


-- ── 8. Forecast vs actuals (last 7 days where both exist) ───────────────────
SELECT
    a.revenue_date,
    round(a.daily_revenue, 2)           AS actual_revenue,
    round(f.yhat, 2)                    AS forecast_yhat,
    round(f.yhat_lower, 2)              AS forecast_lower,
    round(f.yhat_upper, 2)              AS forecast_upper,
    round(a.daily_revenue - f.yhat, 2)  AS forecast_error
FROM `smb-finance-project.analytics.int_daily_revenue` a
JOIN `smb-finance-project.analytics.forecast_results` f
    ON a.revenue_date = f.forecast_date
ORDER BY a.revenue_date DESC
LIMIT 7;
