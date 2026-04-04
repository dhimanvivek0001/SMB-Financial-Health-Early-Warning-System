# AI Weekly Summary — Vertex AI Gemini Integration

> **Status: Planned — Phase 3**  
> Vertex AI requires billing enabled on GCP. This document explains the full
> architecture, exact workflow, expected output, and how to activate it when ready.

---

## What This Feature Does

Every week, instead of a business owner manually reading charts and tables,
this feature automatically generates a plain-English paragraph like this:

---

### Example Output (what the business owner sees in the dashboard)

## AI Weekly Summary — Architecture

### Full workflow
<img width="709" height="910" alt="image" src="https://github.com/user-attachments/assets/d972eb95-9866-4ab0-905d-eb80244ca9ef" />


## How It Works — Step by Step

### Step 1 — Pull data from BigQuery

| Table | What it contains |
|---|---|
| `analytics.int_weekly_summary` | Weekly revenue KPIs |
| `analytics.fct_alerts` | DROP ALERT and SPIKE ALERT rows |
| `analytics.forecast_results` | yhat, yhat_lower, yhat_upper |

### Step 2 — Build the prompt
```python
# python/generate_summary.py
client   = bigquery.Client(project="smb-finance-project")
kpis     = pull_weekly_kpis(client)      # from int_weekly_summary
alerts   = pull_active_alerts(client)    # from fct_alerts
forecast = pull_forecast(client)         # from forecast_results
prompt   = build_prompt(kpis, alerts, forecast)
```

### Step 3 — Call Vertex AI Gemini
```python
import vertexai
from vertexai.generative_models import GenerativeModel

vertexai.init(project="smb-finance-project", location="us-central1")
model   = GenerativeModel("gemini-1.5-flash")
summary = model.generate_content(prompt).text
```

### Step 4 — Write back to BigQuery
```python
# Writes to analytics.llm_weekly_summary
write_summary_to_bigquery(summary, client)
```
<img width="1274" height="899" alt="image" src="https://github.com/user-attachments/assets/2c28fdf9-8e78-492b-b72f-ab5f55a9b9c0" />

Output table columns:
```sql
SELECT
    summary_date,   -- DATE      e.g. 2011-12-09
    model_used,     -- STRING    e.g. gemini-1.5-flash
    summary_text,   -- STRING    full plain-English paragraph
    generated_at    -- TIMESTAMP UTC time of generation
FROM `smb-finance-project.analytics.llm_weekly_summary`
ORDER BY summary_date DESC
```

### Step 5 — Display in Looker Studio
```
Add data source → BigQuery → analytics → llm_weekly_summary

Chart type  → Table
Dimension   → summary_date
Metric      → summary_text
Sort        → summary_date DESC
Rows        → 1

Style:
  Header background → #534AB7
  Row background    → #EEEDFE
  Text colour       → #3C3489
```

---

## Example Output
```
┌──────────────────────────────────────────────────────────────┐
│  AI WEEKLY SUMMARY                      Powered by Gemini    │
│──────────────────────────────────────────────────────────────│
│  This week's revenue reached £42,380, up 8% vs last week,   │
│  driven by strong Thursday and Friday performance. Two DROP  │
│  ALERTs were flagged mid-week, both 30%+ below the 7-day    │
│  rolling average. The 14-day forecast projects revenue       │
│  stabilising near £6,200/day through mid-December.          │
│                                                              │
│  Recommended action: Investigate Tuesday's revenue drop —   │
│  check for fulfilment delays or gaps in promotions.         │
│                                                              │
│  Generated: 2011-12-09  |  Model: gemini-1.5-flash          │
└──────────────────────────────────────────────────────────────┘
```

---

## How to Activate

### Step 1 — Enable Vertex AI API
```bash
gcloud services enable aiplatform.googleapis.com \
  --project=smb-finance-project
```

### Step 2 — Grant permission
```bash
gcloud projects add-iam-policy-binding smb-finance-project \
  --member="user:YOUR_EMAIL@gmail.com" \
  --role="roles/aiplatform.user"
```

### Step 3 — Install library
```bash
pip install google-cloud-aiplatform
```

### Step 4 — Run the script
```bash
cd ~/smb_finance
python python/generate_summary.py
```

### Step 5 — Verify in BigQuery
```sql
SELECT *
FROM `smb-finance-project.analytics.llm_weekly_summary`
ORDER BY summary_date DESC
LIMIT 5
```

---

## Why Not Enabled in Phase 1

| Reason | Detail |
|---|---|
| Billing required | Vertex AI charges per 1,000 tokens |
| Estimated cost | ~$0.002 per weekly run |
| Permission level | Requires `aiplatform.googleapis.com` enabled |
| Script status | Fully written — `python/generate_summary.py` |

---

## Estimated Cost

| Frequency | Cost per run | Monthly cost |
|---|---|---|
| Weekly | ~$0.002 | ~$0.008 |
| Daily | ~$0.002 | ~$0.06 |

---

## Phase 4 — Full Automation
```
Cloud Scheduler (every Monday 6am)
         │
         ▼
     dbt run
         │
         ▼
 python forecast.py
         │
         ▼
 python generate_summary.py
         │
         ▼
 analytics.llm_weekly_summary
         │
         ▼
 Looker Studio + Slack + Email
```
```bash
gcloud scheduler jobs create http smb-weekly-summary \
  --schedule="0 6 * * 1" \
  --uri="https://YOUR_CLOUD_RUN_URL/run" \
  --time-zone="Europe/Dublin" \
  --location="europe-west1"
