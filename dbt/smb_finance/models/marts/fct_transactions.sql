-- fct_transactions.sql
-- Core fact table: one row per transaction line.

select
    invoice_id,
    product_id,
    product_name,
    quantity,
    unit_price,
    revenue,
    invoice_timestamp,
    invoice_date,
    customer_id,
    country
from {{ ref('stg_transactions') }}
