"""
forecast.py
-----------
Reads historical daily revenue from BigQuery (analytics.int_daily_revenue),
trains a Facebook Prophet model, and writes a 14-day forecast back to
analytics.forecast_results.

Usage:
    python python/forecast.py

Requirements:
    pip install -r requirements.txt
    GCP authentication must be set up (gcloud auth application-default login)
"""

import pandas as pd
from prophet import Prophet
from google.cloud import bigquery

# ── Config ────────────────────────────────────────────────────────────────────
PROJECT_ID      = "smb-finance-project"      # Change to your GCP project ID
DATASET         = "analytics"
SOURCE_TABLE    = f"{PROJECT_ID}.{DATASET}.int_daily_revenue"
DEST_TABLE      = f"{PROJECT_ID}.{DATASET}.forecast_results"
FORECAST_DAYS   = 14
# ─────────────────────────────────────────────────────────────────────────────


def load_revenue_from_bigquery() -> pd.DataFrame:
    """Pull daily revenue history from BigQuery."""
    client = bigquery.Client(project=PROJECT_ID)
    query = f"""
        SELECT
            revenue_date AS ds,
            daily_revenue AS y
        FROM `{SOURCE_TABLE}`
        ORDER BY revenue_date
    """
    print(f"Loading revenue data from {SOURCE_TABLE}...")
    df = client.query(query).to_dataframe()
    df["ds"] = pd.to_datetime(df["ds"])
    print(f"  Loaded {len(df)} rows. Date range: {df['ds'].min()} to {df['ds'].max()}")
    return df


def train_and_forecast(df: pd.DataFrame) -> pd.DataFrame:
    """Train Prophet on historical data and generate a 14-day forecast."""
    print(f"Training Prophet model on {len(df)} daily revenue observations...")

    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False,
        changepoint_prior_scale=0.05,   # Controls trend flexibility
        seasonality_prior_scale=10.0,
    )
    model.fit(df)

    future = model.make_future_dataframe(periods=FORECAST_DAYS)
    forecast = model.predict(future)

    # Keep only the forecast columns we need
    result = forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].copy()
    result.columns = ["forecast_date", "yhat", "yhat_lower", "yhat_upper"]
    result["yhat"]       = result["yhat"].clip(lower=0)
    result["yhat_lower"] = result["yhat_lower"].clip(lower=0)
    result["yhat_upper"] = result["yhat_upper"].clip(lower=0)

    print(f"  Forecast generated for dates: {result['forecast_date'].min()} to {result['forecast_date'].max()}")
    return result


def write_forecast_to_bigquery(df: pd.DataFrame) -> None:
    """Write forecast results to BigQuery, replacing previous run."""
    client = bigquery.Client(project=PROJECT_ID)

    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        schema=[
            bigquery.SchemaField("forecast_date", "DATE"),
            bigquery.SchemaField("yhat",          "FLOAT64"),
            bigquery.SchemaField("yhat_lower",    "FLOAT64"),
            bigquery.SchemaField("yhat_upper",    "FLOAT64"),
        ],
    )

    print(f"Writing {len(df)} forecast rows to {DEST_TABLE}...")
    job = client.load_table_from_dataframe(df, DEST_TABLE, job_config=job_config)
    job.result()
    print(f"  Done. Forecast written successfully.")


def main():
    print("=" * 60)
    print("SMB Financial Health — Revenue Forecast Pipeline")
    print("=" * 60)

    df_history  = load_revenue_from_bigquery()
    df_forecast = train_and_forecast(df_history)
    write_forecast_to_bigquery(df_forecast)

    print("\nSample forecast (last 5 rows):")
    print(df_forecast.tail(5).to_string(index=False))
    print("\nForecast pipeline complete.")


if __name__ == "__main__":
    main()
