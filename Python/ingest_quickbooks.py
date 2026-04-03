"""
ingest_quickbooks.py
---------------------
Planned Phase 2 connector: Pull invoices and expenses from QuickBooks Online API
and land them into BigQuery raw tables.

STATUS: Architecture and auth flow designed. Requires QuickBooks developer account
        and OAuth 2.0 credentials. Not yet connected in Phase 1.

PLANNED TABLES CREATED:
    raw.quickbooks_invoices   — all invoice headers
    raw.quickbooks_expenses   — all expense transactions
    raw.quickbooks_customers  — customer master data

QuickBooks Developer Portal:
    https://developer.intuit.com/

OAuth 2.0 Flow:
    1. Register app at developer.intuit.com
    2. Get Client ID + Client Secret
    3. Redirect user to Intuit auth URL
    4. Exchange code for access_token + refresh_token
    5. Use access_token in API calls (expires every 60 min)
    6. Use refresh_token to get new access_token (expires every 100 days)

Usage (once credentials are configured):
    python python/ingest_quickbooks.py
"""

import os
import json
import requests
import pandas as pd
from datetime import datetime
from google.cloud import bigquery

# ── Config ─────────────────────────────────────────────────────────────────
PROJECT_ID     = "smb-finance-project"
COMPANY_ID     = os.environ.get("QUICKBOOKS_COMPANY_ID", "")   # Realm ID
ACCESS_TOKEN   = os.environ.get("QUICKBOOKS_ACCESS_TOKEN", "")
QBO_BASE_URL   = "https://quickbooks.api.intuit.com/v3/company"
SANDBOX_URL    = "https://sandbox-quickbooks.api.intuit.com/v3/company"
USE_SANDBOX    = True   # Set False for production
# ─────────────────────────────────────────────────────────────────────────────

BASE_URL = SANDBOX_URL if USE_SANDBOX else QBO_BASE_URL


def get_auth_headers() -> dict:
    return {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Accept":        "application/json",
        "Content-Type":  "application/json",
    }


def query_quickbooks(sql: str) -> list:
    """Run a QuickBooks query language (QQL) statement."""
    url    = f"{BASE_URL}/{COMPANY_ID}/query"
    params = {"query": sql, "minorversion": "65"}
    resp   = requests.get(url, headers=get_auth_headers(), params=params)
    resp.raise_for_status()
    return resp.json().get("QueryResponse", {})


def pull_invoices() -> pd.DataFrame:
    """Pull all invoices from QuickBooks."""
    print("  Fetching invoices from QuickBooks...")
    result = query_quickbooks(
        "SELECT * FROM Invoice WHERE TxnDate >= '2024-01-01' ORDERBY TxnDate DESC MAXRESULTS 1000"
    )
    invoices = result.get("Invoice", [])
    rows = []
    for inv in invoices:
        rows.append({
            "invoice_id":    inv.get("Id"),
            "doc_number":    inv.get("DocNumber"),
            "txn_date":      inv.get("TxnDate"),
            "due_date":      inv.get("DueDate"),
            "customer_id":   inv.get("CustomerRef", {}).get("value"),
            "customer_name": inv.get("CustomerRef", {}).get("name"),
            "total_amount":  inv.get("TotalAmt"),
            "balance":       inv.get("Balance"),
            "status":        "Paid" if inv.get("Balance", 0) == 0 else "Outstanding",
            "currency":      inv.get("CurrencyRef", {}).get("value", "USD"),
            "ingested_at":   datetime.utcnow().isoformat(),
        })
    print(f"  Fetched {len(rows)} invoices.")
    return pd.DataFrame(rows)


def pull_expenses() -> pd.DataFrame:
    """Pull expense transactions from QuickBooks."""
    print("  Fetching expenses from QuickBooks...")
    result = query_quickbooks(
        "SELECT * FROM Purchase WHERE TxnDate >= '2024-01-01' ORDERBY TxnDate DESC MAXRESULTS 1000"
    )
    purchases = result.get("Purchase", [])
    rows = []
    for p in purchases:
        rows.append({
            "expense_id":   p.get("Id"),
            "txn_date":     p.get("TxnDate"),
            "vendor_name":  p.get("EntityRef", {}).get("name"),
            "total_amount": p.get("TotalAmt"),
            "payment_type": p.get("PaymentType"),
            "account_name": p.get("AccountRef", {}).get("name"),
            "currency":     p.get("CurrencyRef", {}).get("value", "USD"),
            "ingested_at":  datetime.utcnow().isoformat(),
        })
    print(f"  Fetched {len(rows)} expenses.")
    return pd.DataFrame(rows)


def write_to_bigquery(df: pd.DataFrame, table_name: str) -> None:
    """Write a DataFrame to BigQuery raw layer."""
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
    print("SMB Financial Health — QuickBooks Ingestion (Planned Phase 2)")
    print("=" * 60)

    if not ACCESS_TOKEN or not COMPANY_ID:
        print(
            "\nNOTE: QUICKBOOKS_ACCESS_TOKEN and QUICKBOOKS_COMPANY_ID "
            "environment variables are not set.\n"
            "This script requires QuickBooks OAuth 2.0 credentials.\n"
            "See: https://developer.intuit.com/app/developer/qbo/docs/develop/authentication-and-authorization\n"
        )
        return

    invoices = pull_invoices()
    write_to_bigquery(invoices, "quickbooks_invoices")

    expenses = pull_expenses()
    write_to_bigquery(expenses, "quickbooks_expenses")

    print("\nQuickBooks ingestion complete.")


if __name__ == "__main__":
    main()
