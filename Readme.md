# SMB Financial Health Early Warning System

![BigQuery](https://img.shields.io/badge/BigQuery-4285F4?style=flat&logo=google-cloud&logoColor=white)
![dbt](https://img.shields.io/badge/dbt-FF694B?style=flat&logo=dbt&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![Prophet](https://img.shields.io/badge/Prophet-FF694B?style=flat)
![Looker Studio](https://img.shields.io/badge/Looker_Studio-4285F4?style=flat&logo=google&logoColor=white)
![Vertex AI](https://img.shields.io/badge/Vertex_AI-Planned-lightgrey?style=flat&logo=google-cloud)

> End-to-end financial analytics pipeline: raw transactions → dbt models → anomaly detection → revenue forecasting → Looker Studio dashboard — with a production roadmap for QuickBooks, Stripe, Plaid, and Vertex AI LLM summaries.

---

## Overview

Small and medium businesses lack real-time financial visibility and early-warning systems. This project demonstrates a **modern analytics engineering pipeline** that:

- Ingests raw transaction data into BigQuery
- Transforms it into analytics-ready models using dbt (staging → intermediate → marts)
- Detects revenue anomalies automatically (Z-score based)
- Forecasts 14-day future revenue using Facebook Prophet
- Surfaces business alerts and KPIs in a Looker Studio dashboard
- Is designed to connect to live financial APIs (QuickBooks, Stripe, Plaid) in production

---

## Full Production Architecture
![Screenshot_3-4-2026_18751_](https://github.com/user-attachments/assets/1a15f9e9-a3e5-4df9-b724-dfaf2ec4823e)


## Implementation Status

| Component | Status | Details |
|---|---|---|
| BigQuery warehouse | ✅ Complete | Raw + analytics datasets |
| dbt staging layer | ✅ Complete | `stg_transactions` |
| dbt intermediate layer | ✅ Complete | 5 models |
| dbt marts layer | ✅ Complete | `dim_customers`, `dim_products`, `fct_transactions`, `fct_alerts` |
| Prophet forecasting | ✅ Complete | 14-day forecast → `analytics.forecast_results` |
| Looker Studio dashboard | ✅ Complete | 6 sections — KPIs, alerts, charts, forecast |
| dbt schema tests | ✅ Complete | `not_null`, `unique`, `accepted_values` |
| Vertex AI LLM summary | 🔜 Planned | Script prepared — API permissions pending |
| QuickBooks connector | 🔜 Planned | Architecture + ingestion script designed |
| Stripe connector | 🔜 Planned | Architecture + ingestion script designed |
| Plaid / bank connector | 🔜 Planned | Architecture designed |
| Cloud Scheduler | 🔜 Planned | Daily pipeline automation |
| Slack / email delivery | 🔜 Planned | Webhook integration designed |

---

## Tech Stack

| Tool | Role |
|---|---|
| Google BigQuery | Cloud data warehouse |
| dbt Core | Transformation and analytics engineering |
| Python + Prophet | Time series forecasting |
| Looker Studio | Dashboard and reporting |
| Vertex AI Gemini | LLM executive summary (planned) |
| QuickBooks API | Invoice and expense ingestion (planned) |
| Stripe API | Payment and subscription ingestion (planned) |
| Plaid API | Bank feed and balance ingestion (planned) |
| Cloud Scheduler | Pipeline automation (planned) |
| Google Cloud Shell | Development environment |

---

## Data Source

**Online Retail Dataset** — loaded into BigQuery as `Raw.Online_Retail`.
A public transactional dataset of UK-based online retail invoices used to simulate the SMB financial data model.

In production this layer is replaced by live API connectors (QuickBooks, Stripe, Plaid).

---

## dbt Models

### Staging
| Model | Description |
|---|---|
| `stg_transactions` | Cleaned, typed, and filtered source transactions |

### Intermediate
| Model | Description |
|---|---|
| `int_daily_revenue` | Revenue, invoices, and customers aggregated per day |
| `int_invoice_summary` | Per-invoice line aggregation |
| `int_weekly_summary` | Week-level revenue rollup (Mon–Sun) |
| `int_revenue_forecast` | Rolling 7-day average — used as alert threshold |
| `int_revenue_anomalies` | Z-score anomaly scoring on daily revenue |

### Marts
| Model | Description |
|---|---|
| `dim_customers` | Lifetime value, order frequency, first/last purchase |
| `dim_products` | Total revenue and quantity sold per product |
| `fct_transactions` | Fact table — one row per invoice line |
| `fct_alerts` | DROP ALERT / SPIKE ALERT / NORMAL flags per day |

---

## Production Roadmap

### Phase 2 — Live API Connectors

| Source | Data | Output Table |
|---|---|---|
| QuickBooks API | Invoices, expenses, chart of accounts | `raw.quickbooks_invoices`, `raw.quickbooks_expenses` |
| Stripe API | Payments, subscriptions, charges | `raw.stripe_payments`, `raw.stripe_subscriptions` |
| Plaid / Bank API | Account balances, transaction feeds | `raw.bank_transactions`, `raw.bank_balances` |
| Shopify (optional) | Orders, sales, product data | `raw.shopify_orders` |

All sources land in the BigQuery raw layer and flow through the existing dbt transformation architecture unchanged.

### Phase 3 — Vertex AI LLM Summary
```python
# python/generate_summary.py — workflow:
# 1. Pull KPIs from analytics.int_weekly_summary
# 2. Pull active alerts from analytics.fct_alerts
# 3. Pull forecast from analytics.forecast_results
# 4. Send context to Vertex AI Gemini with a CFO-analyst prompt
# 5. Write summary_text to analytics.llm_weekly_summary
# 6. Surface in Looker Studio "AI Summary" section
```

> Not fully enabled: Vertex AI requires `aiplatform.googleapis.com` to be active on the project. The script is fully written — see `python/generate_summary.py`.

### Phase 4 — Automation and Delivery

- Cloud Scheduler triggers daily: `dbt run` → `forecast.py` → `generate_summary.py`
- Slack webhook posts DROP ALERT and SPIKE ALERT notifications in real time
- Email digest of weekly executive summary every Monday morning

---

## How to Run

### dbt
```bash
dbt debug
dbt run
dbt test
dbt docs generate && dbt docs serve
```

### Forecast
```bash
pip install -r requirements.txt
python python/forecast.py
```

### LLM Summary (once Vertex AI is enabled)
```bash
python python/generate_summary.py
```

---

## Repository Structure
