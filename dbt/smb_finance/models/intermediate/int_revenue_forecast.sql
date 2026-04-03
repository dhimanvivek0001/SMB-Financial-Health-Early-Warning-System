-- int_revenue_forecast.sql
-- Adds a rolling 7-day average to each day's revenue.
-- This 7d average is used as the alert threshold in fct_alerts.

select
    revenue_date,
    daily_revenue,
    avg(daily_revenue) over (
        order by revenue_date
        rows between 6 preceding and current row
    )   as rolling_7d_avg
from {{ ref('int_daily_revenue') }}
