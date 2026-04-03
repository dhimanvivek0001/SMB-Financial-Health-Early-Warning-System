-- int_revenue_anomalies.sql
-- Applies Z-score anomaly detection to daily revenue.
-- A Z-score above +2 or below -2 is considered anomalous.

with revenue_stats as (
    select
        revenue_date,
        daily_revenue,
        avg(daily_revenue)    over () as avg_revenue,
        stddev(daily_revenue) over () as std_revenue
    from {{ ref('int_daily_revenue') }}
)

select
    revenue_date,
    daily_revenue,
    avg_revenue,
    std_revenue,
    safe_divide(daily_revenue - avg_revenue, std_revenue)   as z_score,
    case
        when safe_divide(daily_revenue - avg_revenue, std_revenue) > 2  then 'HIGH ANOMALY'
        when safe_divide(daily_revenue - avg_revenue, std_revenue) < -2 then 'LOW ANOMALY'
        else 'NORMAL'
    end                                                     as anomaly_flag
from revenue_stats
