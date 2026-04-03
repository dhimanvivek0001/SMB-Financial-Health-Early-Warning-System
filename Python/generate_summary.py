"""
generate_summary.py
--------------------
Planned Phase 3 enhancement: Generate a weekly natural-language executive
summary using Vertex AI Gemini, and write it to analytics.llm_weekly_summary.

STATUS: Script fully designed. Vertex AI API enablement is pending.
        Requires: gcloud projects add-iam-policy-binding for aiplatform.googleapis.com

PLANNED WORKFLOW:
    1. Pull KPIs from analytics.int_weekly_summary (last 2 weeks)
    2. Pull active alerts from analytics.fct_alerts
    3. Pull forecast from analytics.forecast_results (next 7 days)
    4. Send combined context to Vertex AI Gemini with a business prompt
    5. Write the LLM output to analytics.llm_weekly_summary
    6. This table feeds the "AI Summary" section in Looker Studio

Usage (once Vertex AI is enabled):
    python python/generate_summary.py
"""

import json
from datetime import datetime
import pandas as pd
from google.cloud import bigquery

# ── Config ────────────────────────────────────────────────────────────────────
PROJECT_ID   = "smb-finance-project"      # Change to your GCP project ID
LOCATION     = "us-central1"
MODEL_ID     = "gemini-1.5-flash"         # Or gemini-1.5-pro for richer output
DEST_TABLE   = f"{PROJECT_ID}.analytics.llm_weekly_summary"
# ─────────────────────────────────────────────────────────────────────────────


def pull_weekly_kpis(client: bigquery.Client) -> dict:
    """Pull last 2 weeks of KPIs for context."""
    query = """
        SELECT
            week_start,
            weekly_revenue,
            avg_daily_revenue,
            days_count
        FROM `analytics.int_weekly_summary`
        ORDER BY week_start DESC
        LIMIT 2
    """
    rows = client.query(query).to_dataframe().to_dict(orient="records")
    return rows


def pull_active_alerts(client: bigquery.Client) -> list:
    """Pull recent DROP or SPIKE alerts."""
    query = """
        SELECT revenue_date, daily_revenue, alert_status
        FROM `analytics.fct_alerts`
        WHERE alert_status != 'NORMAL'
        ORDER BY revenue_date DESC
        LIMIT 5
    """
    rows = client.query(query).to_dataframe().to_dict(orient="records")
    return rows


def pull_forecast(client: bigquery.Client) -> list:
    """Pull next 7 days of revenue forecast."""
    query = """
        SELECT forecast_date, yhat, yhat_lower, yhat_upper
        FROM `analytics.forecast_results`
        WHERE forecast_date >= CURRENT_DATE()
        ORDER BY forecast_date
        LIMIT 7
    """
    rows = client.query(query).to_dataframe().to_dict(orient="records")
    return rows


def build_prompt(kpis: list, alerts: list, forecast: list) -> str:
    """Compose the business context prompt for Gemini."""
    prompt = f"""
You are a senior CFO analyst for a small business. Below is the weekly financial 
performance data. Write a concise executive summary (4-6 sentences) that a 
non-technical business owner can understand. Focus on: what happened this week, 
any alerts or anomalies, and what the revenue forecast suggests for the coming week.
End with one specific recommended action.

--- WEEKLY KPIs ---
{json.dumps(kpis, indent=2, default=str)}

--- REVENUE ALERTS (last 5 flagged days) ---
{json.dumps(alerts, indent=2, default=str)}

--- 7-DAY REVENUE FORECAST ---
{json.dumps(forecast, indent=2, default=str)}

Write your executive summary below:
"""
    return prompt.strip()


def call_vertex_ai(prompt: str) -> str:
    """
    Call Vertex AI Gemini to generate the summary.

    NOTE: This block requires Vertex AI API to be enabled on your project.
    Enable with:
        gcloud services enable aiplatform.googleapis.com --project=smb-finance-project
    """
    try:
        import vertexai
        from vertexai.generative_models import GenerativeModel

        vertexai.init(project=PROJECT_ID, location=LOCATION)
        model = GenerativeModel(MODEL_ID)
        response = model.generate_content(prompt)
        return response.text

    except ImportError:
        return "[Vertex AI not installed. Run: pip install google-cloud-aiplatform]"
    except Exception as e:
        return f"[Vertex AI API call failed: {e}. Enable aiplatform.googleapis.com on your project.]"


def write_summary_to_bigquery(summary_text: str, client: bigquery.Client) -> None:
    """Write the LLM-generated summary to BigQuery."""
    row = [{
        "summary_date":  datetime.today().strftime("%Y-%m-%d"),
        "model_used":    MODEL_ID,
        "summary_text":  summary_text,
        "generated_at":  datetime.utcnow().isoformat(),
    }]

    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        schema=[
            bigquery.SchemaField("summary_date",  "DATE"),
            bigquery.SchemaField("model_used",    "STRING"),
            bigquery.SchemaField("summary_text",  "STRING"),
            bigquery.SchemaField("generated_at",  "TIMESTAMP"),
        ],
    )

    job = client.load_table_from_json(row, DEST_TABLE, job_config=job_config)
    job.result()
    print(f"Summary written to {DEST_TABLE}")


def main():
    print("=" * 60)
    print("SMB Financial Health — Vertex AI LLM Summary Generator")
    print("=" * 60)

    client = bigquery.Client(project=PROJECT_ID)

    print("Pulling KPIs, alerts, and forecast from BigQuery...")
    kpis     = pull_weekly_kpis(client)
    alerts   = pull_active_alerts(client)
    forecast = pull_forecast(client)

    print("Building prompt for Vertex AI Gemini...")
    prompt = build_prompt(kpis, alerts, forecast)

    print("Calling Vertex AI Gemini...")
    summary = call_vertex_ai(prompt)

    print("\n--- GENERATED SUMMARY ---")
    print(summary)
    print("-------------------------\n")

    write_summary_to_bigquery(summary, client)
    print("LLM summary pipeline complete.")


if __name__ == "__main__":
    main()
