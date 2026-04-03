-- stg_transactions.sql
-- Cleans and standardises the raw Online Retail dataset.
-- Filters out returns (negative quantity), zero-price rows, and anonymous customers.

select
    InvoiceNo                                                   as invoice_id,
    StockCode                                                   as product_id,
    Description                                                 as product_name,
    cast(Quantity as int64)                                     as quantity,
    cast(UnitPrice as float64)                                  as unit_price,
    cast(Quantity as float64) * cast(UnitPrice as float64)      as revenue,
    InvoiceDate                                                 as invoice_timestamp,
    date(InvoiceDate)                                           as invoice_date,
    cast(CustomerID as string)                                  as customer_id,
    Country                                                     as country
from {{ source('raw', 'Online_Retail') }}
where Quantity > 0
  and UnitPrice > 0
  and CustomerID is not null
