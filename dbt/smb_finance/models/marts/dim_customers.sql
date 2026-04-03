-- dim_customers.sql
-- Customer dimension: lifetime value, order frequency, recency.

select
    customer_id,
    any_value(country)          as country,
    count(distinct invoice_id)  as total_orders,
    sum(revenue)                as lifetime_value,
    avg(revenue)                as avg_order_value,
    min(invoice_timestamp)      as first_purchase,
    max(invoice_timestamp)      as last_purchase,
    date_diff(
        max(invoice_date),
        min(invoice_date),
        day
    )                           as days_as_customer
from {{ ref('stg_transactions') }}
group by customer_id
