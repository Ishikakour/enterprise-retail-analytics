# Enterprise Retail Analytics — Profitability & Risk Dashboard

**Live Dashboard:** [[YOUR-DASH-DEPLOYED-URL](https://enterprise-retail-analytics.onrender.com)]

## Business Problem

A major e-commerce platform (Brazil) is experiencing margin pressure despite high order volume. Leadership needs to identify loss-making orders and the categories that concentrate those losses.

## Data & Scale

- **Source:** Brazilian E-Commerce Public Dataset (Olist) — 100K+ orders, 2016–2018.
- **Volume:** 99,441 orders in the raw extract; dashboard uses **96,478 delivered orders** (one row per order, not per item).
- **Problem:** High order volume is undermined by freight-heavy, low-price baskets and installment fees.
- **Objective:** Identify loss-making orders and recommend targeted interventions.

## Data Pipeline

`Kaggle CSVs` → `Python (Pandas, NumPy)` → `DuckDB` → `Plotly Dash`

1. **Data Ingestion & Cleaning:** Loaded 8 raw tables, kept delivered orders, joined items/products/customers/payments.
2. **Feature Engineering:** `Profit = Price − Freight − Payment Installment Fees` (fee = 1.5% of payment × installment count).
3. **Analysis:** DuckDB SQL in `analysis.sql` (KPIs, `DENSE_RANK` by category, monthly running total).
4. **Dashboard:** Interactive Dash app with drill-downs by **state** and **category**.

## Key Findings

Computed from the delivered-order grain after the profit formula above:

- **Loss Concentration:** About 8% of categories (electronics, furniture decor, telephony, housewares, health beauty, sports leisure) account for **54%** of total losses. Loss-making orders are **3.6%** of delivered volume.
- **Payment Risk:** Orders with more than 6 installments are **not** riskier under this fee model (1.6% loss rate vs 3.9% for the rest). Losses cluster in cheap baskets where freight exceeds price.
- **Regional Effect:** Rio de Janeiro’s loss rate is **2.5×** São Paulo (3.7% vs 1.5%).

## Tech Stack

- **Data:** Python, Pandas, NumPy, DuckDB
- **Dashboard:** Plotly Dash
- **Deployment:** Render or Railway (`Procfile` included)

## Repository Contents

| File | Purpose |
| :--- | :--- |
| `app.py` | Dash app; all charts/KPIs run as DuckDB SQL |
| `analysis.sql` | KPI, category rank, and monthly running-total queries |
| `etl_pipeline.py` | Script to build the DuckDB database |
| `profit.py` | Profit = price − freight − installment fees |
| `requirements.txt` | Python dependencies |
| `Procfile` | Gunicorn entrypoint for Render/Railway |
| `data/` | Raw (gitignored) and processed datasets |

## How to Run

Put the Olist CSVs in `data/raw/`, then:

```bash
pip install -r requirements.txt
python etl_pipeline.py
python app.py
```
