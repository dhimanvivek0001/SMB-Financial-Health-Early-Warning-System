-- int_weekly_summary.sql
-- Rolls daily revenue up to weekly grain (week starting Monday).

select
    date_trunc(revenue_date, week(monday))  as week_start,
    sum(daily_revenue)                      as weekly_revenue,
    avg(daily_revenue)                      as avg_daily_revenue,
    count(*)                                as days_count
from {{ ref('int_daily_revenue') }}
group by week_start
