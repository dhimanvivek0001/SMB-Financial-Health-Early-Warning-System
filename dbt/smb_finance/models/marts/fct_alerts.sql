-- fct_alerts.sql
-- Revenue alert fact table.
-- DROP ALERT: revenue < 70% of 7-day rolling average
-- SPIKE ALERT: revenue > 150% of 7-day rolling average

select
    revenue_date,
    daily_revenue,
    rolling_7d_avg,
    case
        when daily_revenue < rolling_7d_avg * 0.7  then 'DROP ALERT'
        when daily_revenue > rolling_7d_avg * 1.5  then 'SPIKE ALERT'
        else 'NORMAL'
    end     as alert_status,
    round(safe_divide(daily_revenue, rolling_7d_avg) * 100, 1)  as pct_of_avg
from {{ ref('int_revenue_forecast') }}
