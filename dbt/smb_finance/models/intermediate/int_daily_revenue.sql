-- int_daily_revenue.sql
-- Aggregates cleaned transactions to a daily grain.

select
    invoice_date                        as revenue_date,
    sum(revenue)                        as daily_revenue,
    count(distinct invoice_id)          as total_invoices,
    count(distinct customer_id)         as total_customers
from {{ ref('stg_transactions') }}
group by revenue_date
