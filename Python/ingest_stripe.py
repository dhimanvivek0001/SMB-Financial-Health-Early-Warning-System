"""
ingest_stripe.py
-----------------
Planned Phase 2 connector: Pull payment and subscription data from the Stripe API
and land it into BigQuery raw tables.

STATUS: Architecture designed. Requires Stripe API key. Not connected in Phase 1.

PLANNED TABLES CREATED:
    raw.stripe_payments       — all payment intents
    raw.stripe_subscriptions  — active subscriptions

Stripe Dashboard:
    https://dashboard.stripe.com/apikeys

Usage (once API key is set):
    export STRIPE_SECRET_KEY=sk_live_...
    python python/ingest_stripe.py
"""

import os
import pandas as pd
from datetime import datetime
from google.cloud import bigquery

PROJECT_ID      = "smb-finance-project"
STRIPE_API_KEY  = os.environ.get("STRIPE_SECRET_KEY", "")


def pull_stripe_payments() -> pd.DataFrame:
    """Pull payment intents from Stripe API."""
    try:
        import stripe
        stripe.api_key = STRIPE_API_KEY

        print("  Fetching Stripe payment intents...")
        payments = stripe.PaymentIntent.list(limit=100)
        rows = []
        for p in payments.auto_paging_iter():
            rows.append({
                "payment_id":    p["id"],
                "amount":        p["amount"] / 100,        # Stripe stores cents
                "currency":      p["currency"].upper(),
                "status":        p["status"],
                "customer_id":   p.get("customer"),
                "created_date":  datetime.fromtimestamp(p["created"]).strftime("%Y-%m-%d"),
                "payment_method": p.get("payment_method_types", [""])[0],
                "ingested_at":   datetime.utcnow().isoformat(),
            })
        print(f"  Fetched {len(rows)} payments.")
        return pd.DataFrame(rows)

    except ImportError:
        print("  stripe library not installed. Run: pip install stripe")
        return pd.DataFrame()
    except Exception as e:
        print(f"  Stripe API error: {e}")
        return pd.DataFrame()


def write_to_bigquery(df: pd.DataFrame, table_name: str) -> None:
    """Write DataFrame to BigQuery raw layer."""
    if df.empty:
        print(f"  No data to write for {table_name}.")
        return
    client = bigquery.Client(project=PROJECT_ID)
    dest   = f"{PROJECT_ID}.raw.{table_name}"
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        autodetect=True,
    )
    job = client.load_table_from_dataframe(df, dest, job_config=job_config)
    job.result()
    print(f"  Written {len(df)} rows to {dest}")


def main():
    print("=" * 60)
    print("SMB Financial Health — Stripe Ingestion (Planned Phase 2)")
    print("=" * 60)

    if not STRIPE_API_KEY:
        print(
            "\nNOTE: STRIPE_SECRET_KEY environment variable not set.\n"
            "Get your key at: https://dashboard.stripe.com/apikeys\n"
            "Then run: export STRIPE_SECRET_KEY=sk_live_...\n"
        )
        return

    payments = pull_stripe_payments()
    write_to_bigquery(payments, "stripe_payments")

    print("\nStripe ingestion complete.")


if __name__ == "__main__":
    main()
