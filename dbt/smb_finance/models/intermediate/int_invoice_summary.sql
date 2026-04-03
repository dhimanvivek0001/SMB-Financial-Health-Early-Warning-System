-- int_invoice_summary.sql
-- Summarises each invoice to a single row.

select
    invoice_id,
    invoice_date,
    customer_id,
    country,
    count(*)        as line_items,
    sum(quantity)   as total_units,
    sum(revenue)    as invoice_revenue
from {{ ref('stg_transactions') }}
group by invoice_id, invoice_date, customer_id, country
