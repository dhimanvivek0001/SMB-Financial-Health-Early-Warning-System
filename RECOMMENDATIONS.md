# Recommendations and Future Work

This document captures what was built, what was intentionally deferred, and the specific recommended next steps to take this project to production.

---

## What is complete

The Phase 1 pipeline is fully functional end to end:

- Raw transactional data is loaded into BigQuery
- dbt models clean, aggregate, and transform data through three layers (staging → intermediate → marts)
- Z-score anomaly detection flags unusual revenue days automatically
- Facebook Prophet generates a 14-day revenue forecast written back to BigQuery
- Looker Studio dashboard surfaces KPIs, alerts, customer insights, product insights, and forecasts
- dbt schema tests enforce data quality on key fields

---

## What was intentionally not built (and why)

### Vertex AI LLM summary

**What it would do:** Pull weekly KPIs, active alerts, and forecast values from BigQuery, send them to Vertex AI Gemini with a CFO-analyst prompt, and write a plain-English executive summary to `analytics.llm_weekly_summary` — surfaced as an "AI Insights" card in Looker Studio.

**Why deferred:** Enabling `aiplatform.googleapis.com` requires project-owner billing permissions not available in the current Cloud Shell environment.

**What is ready:** The full script is written at `python/generate_summary.py`. It requires only two steps to activate:
```bash
gcloud services enable aiplatform.googleapis.com --project=YOUR_PROJECT_ID
python python/generate_summary.py
```

---

### QuickBooks API connector

**What it would do:** Pull invoices, expenses, and customer records from QuickBooks Online via OAuth 2.0 and land them in `raw.quickbooks_invoices` and `raw.quickbooks_expenses` for the same dbt models to process.

**Why deferred:** Requires a QuickBooks developer account and OAuth credentials tied to a live company.

**What is ready:** Full ingestion script at `python/ingest_quickbooks.py`. To activate:
1. Register an app at [developer.intuit.com](https://developer.intuit.com)
2. Get Client ID, Client Secret, and Company ID (Realm ID)
3. Set environment variables and run:
```bash
export QUICKBOOKS_ACCESS_TOKEN=your_token
export QUICKBOOKS_COMPANY_ID=your_realm_id
python python/ingest_quickbooks.py
```

---

### Stripe API connector

**What it would do:** Pull payment intents, subscriptions, and charges from Stripe and land them in `raw.stripe_payments` and `raw.stripe_subscriptions`.

**Why deferred:** Requires a live Stripe account with API key.

**What is ready:** Full ingestion script at `python/ingest_stripe.py`. To activate:
```bash
pip install stripe
export STRIPE_SECRET_KEY=sk_live_...
python python/ingest_stripe.py
```

---

### Plaid / Bank API connector

**What it would do:** Pull account balances and transaction feeds from a connected bank account via Plaid, giving the pipeline a real cash position view — something QuickBooks and Stripe alone cannot provide.

**Why deferred:** Plaid requires a registered application and sandbox/production approval.

**Recommended approach:**
1. Register at [plaid.com/docs](https://plaid.com/docs)
2. Use Plaid Sandbox for development (no real bank needed)
3. Pull `/transactions/get` and `/accounts/balance/get` endpoints
4. Land in `raw.bank_transactions` and `raw.bank_balances`

---

### Cloud Scheduler automation

**What it would do:** Trigger the full pipeline daily — dbt run, then forecast.py, then generate_summary.py — without any manual intervention.

**Why deferred:** Adds billing cost for Cloud Run or Cloud Functions, and Cloud Scheduler jobs, which is unnecessary overhead for a portfolio project.

**Recommended setup when productionising:**
```bash
# Create a daily job at 6am
gcloud scheduler jobs create http smb-daily-pipeline \
  --schedule="0 6 * * *" \
  --uri="https://YOUR_CLOUD_RUN_URL/run" \
  --message-body='{"pipeline": "full"}' \
  --time-zone="Europe/Dublin"
```

---

### Slack and email delivery

**What it would do:** Post DROP ALERT and SPIKE ALERT notifications to a Slack channel in real time, and send a Monday morning email digest of the weekly executive summary.

**Why deferred:** Requires Slack workspace admin access and an SMTP relay or SendGrid account.

**Recommended Slack webhook setup:**
```python
import requests

def send_slack_alert(alert_date, revenue, avg, status):
    msg = f":rotating_light: *{status}* on {alert_date}\n Revenue: £{revenue:,.0f} vs 7d avg: £{avg:,.0f}"
    requests.post(SLACK_WEBHOOK_URL, json={"text": msg})
```

---

## Specific recommended next steps (priority order)

### 1. Enable Vertex AI and run the LLM summary (highest impact, lowest effort)

This is the single change that most visibly differentiates the project. The script is written. It just needs the API enabled.
```bash
gcloud services enable aiplatform.googleapis.com --project=YOUR_PROJECT_ID
python python/generate_summary.py
```

Then connect `analytics.llm_weekly_summary` as a data source in Looker Studio and add a text/table card in the AI Summary section.

---

### 2. Add dbt tests for intermediate and mart models

Currently only staging and a few mart models have schema tests. Adding coverage to intermediate models makes the pipeline production-grade:
```yaml
# Add to schema.yml
- name: int_revenue_anomalies
  columns:
    - name: z_score
      tests:
        - not_null
- name: dim_customers
  columns:
    - name: lifetime_value
      tests:
        - not_null
        - dbt_utils.expression_is_true:
            expression: ">= 0"
```

---

### 3. Add a `dbt source freshness` check

This catches stale data before it reaches the dashboard:
```yaml
# Add to sources.yml
sources:
  - name: raw
    freshness:
      warn_after: {count: 24, period: hour}
      error_after: {count: 48, period: hour}
    loaded_at_field: InvoiceDate
    tables:
      - name: Online_Retail
```

Run with: `dbt source freshness`

---

### 4. Connect QuickBooks or Stripe in sandbox mode

Both offer free sandbox environments that return realistic test data — no live account needed. This makes the "planned" connectors real and demonstrates end-to-end API ingestion:

- QuickBooks Sandbox: [developer.intuit.com/app/developer/playground](https://developer.intuit.com/app/developer/playground)
- Stripe Test Mode: use `sk_test_...` key — all endpoints work identically to production

---

### 5. Add a cash flow model to dbt

The current models only capture revenue (income side). Adding an expense dimension from QuickBooks or a manual seed file would allow a basic cash flow model:
```sql
-- proposed: int_cash_flow.sql
select
    revenue_date,
    daily_revenue,
    coalesce(daily_expenses, 0)             as daily_expenses,
    daily_revenue - coalesce(daily_expenses, 0) as net_cash_flow
from {{ ref('int_daily_revenue') }}
left join {{ ref('int_daily_expenses') }} using (revenue_date)
```

---

### 6. Add invoice late-payment risk scoring

Using `dim_customers` fields (`balance`, `due_date`, `last_purchase`) to score customers by payment risk — a high-value addition for any SMB finance product:
```sql
-- proposed: fct_invoice_risk.sql
select
    customer_id,
    lifetime_value,
    case
        when days_overdue > 60 then 'HIGH RISK'
        when days_overdue > 30 then 'MEDIUM RISK'
        else 'LOW RISK'
    end as payment_risk_band
from {{ ref('dim_customers') }}
```

---

### 7. Publish dbt docs to GitHub Pages
```bash
dbt docs generate
dbt docs serve  # preview locally first

# then copy ./target/index.html + manifest.json to a /docs branch
# enable GitHub Pages on that branch
```

This gives every recruiter and interviewer a live, browsable data catalogue at `https://yourusername.github.io/smb-finance-ai`.

---

## If this were a real production system

The following would be required beyond what is built here:

| Concern | Recommendation |
|---|---|
| Authentication | Use Google Secret Manager for all API keys — never environment variables in production |
| Incremental loading | Switch dbt models from `table` to `incremental` materialization to avoid full rebuilds |
| Data quality alerting | Integrate `elementary` or `re_data` for automated dbt test monitoring |
| Access control | Use BigQuery row-level security for multi-tenant SMB data isolation |
| Disaster recovery | Enable BigQuery table snapshots and point-in-time recovery |
| Observability | Add OpenTelemetry tracing on ingestion scripts and Cloud Run jobs |
| CI/CD | GitHub Actions workflow to run `dbt run --select state:modified` on every pull request |

---

*Recommendations document — SMB Financial Health Early Warning System*
*MSc Business Analytics portfolio project, University of Galway*
