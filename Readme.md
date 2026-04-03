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
