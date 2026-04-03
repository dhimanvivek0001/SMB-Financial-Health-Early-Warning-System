-- dim_products.sql
-- Product dimension: revenue, units sold, transaction count.

select
    product_id,
    any_value(product_name)     as product_name,
    count(*)                    as transaction_lines,
    sum(quantity)               as total_quantity_sold,
    sum(revenue)                as total_revenue,
    avg(unit_price)             as avg_unit_price
from {{ ref('stg_transactions') }}
group by product_id
