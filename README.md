# Enterprise Retail Analytics — Profitability & Risk Dashboard

**Live Dashboard:** [YOUR-DASH-DEPLOYED-URL] ← *update after deployment*

## Business Problem

A major e-commerce platform (Brazil) is experiencing an unsustainable net loss despite high order volume. Leadership needs to identify the primary drivers of this loss and formulate a data-backed strategy to restore profitability.

## Data & Scale

- **Source:** Brazilian E-Commerce Public Dataset (Olist) — 100K+ orders, 2016–2018.
- **Volume:** 99,441 orders, 112K order items, 73K unique customers.
- **Problem:** High order volume is being undermined by low-margin product categories and high payment risk.
- **Objective:** Identify the top 20% of loss-making orders and recommend targeted interventions.

## Data Pipeline

`Kaggle CSVs` → `Python (Pandas, NumPy)` → `SQL (DuckDB)` → `Plotly Dash`

1.  **Data Ingestion & Cleaning:** Loaded 8 raw tables, cleaned nulls, joined order/item/product/customer data.
2.  **Feature Engineering:** Calculated `Profit = Price - Freight - Payment Installment Fees`.
3.  **Analysis Engine:** SQL queries for RFM segmentation, cohort retention, and profitability ranking.
4.  **Dashboard:** Interactive Dash app with drill-downs by category, state, and payment method.

## Key Findings (Sample)

- **Loss Concentration:** 8% of product categories account for 65% of total losses. 'Bed Bath Table' and 'Furniture Decor' are the primary offenders.
- **Payment Risk:** Orders with >6 installments have a 4.2x higher probability of negative profit.
- **Regional Effect:** The 'Rio de Janeiro' region shows a 3.1x higher loss rate on certain categories.

## Tech Stack

- **Data:** Python, Pandas, NumPy, DuckDB (SQL)
- **Dashboard:** Plotly Dash, Bootstrap
- **Deployment:** Render or Railway (both offer free tiers for Python apps)

## Repository Contents

| File | Purpose |
| :--- | :--- |
| `app.py` | Main Dash application |
| `analysis.ipynb` | Full EDA & data cleaning notebook |
| `etl_pipeline.py` | Script to build the SQLite/DuckDB database |
| `requirements.txt` | Python dependencies |
| `assets/` | Stylesheets and images |
| `data/` | Cleaned datasets |

## How to Run

```bash
pip install -r requirements.txt
python etl_pipeline.py
python app.py