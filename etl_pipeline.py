"""ETL: Olist raw CSVs -> order-grain analytics + DuckDB."""
import os

import duckdb
import pandas as pd

from profit import high_installment_risk, is_loss, order_profit

RAW_TABLES = [
    "olist_orders_dataset.csv",
    "olist_order_items_dataset.csv",
    "olist_products_dataset.csv",
    "olist_order_payments_dataset.csv",
    "olist_customers_dataset.csv",
    "olist_order_reviews_dataset.csv",
    "olist_sellers_dataset.csv",
    "product_category_name_translation.csv",
]


def load_raw(data_dir):
    frames = {}
    for name in RAW_TABLES:
        path = os.path.join(data_dir, name)
        frames[name] = pd.read_csv(path)
    return frames


def _primary_category(items):
    idx = items.groupby("order_id")["price"].idxmax()
    primary = items.loc[idx, ["order_id", "product_category", "seller_id"]]
    return primary


def build_orders(raw):
    orders = raw["olist_orders_dataset.csv"]
    items = raw["olist_order_items_dataset.csv"]
    products = raw["olist_products_dataset.csv"]
    payments = raw["olist_order_payments_dataset.csv"]
    customers = raw["olist_customers_dataset.csv"]
    reviews = raw["olist_order_reviews_dataset.csv"]
    sellers = raw["olist_sellers_dataset.csv"]
    trans = raw["product_category_name_translation.csv"]

    orders = orders[orders["order_status"] == "delivered"].copy()
    orders = orders.merge(
        customers[["customer_id", "customer_unique_id", "customer_state"]],
        on="customer_id",
        how="left",
    )

    items = items.merge(
        products[["product_id", "product_category_name"]],
        on="product_id",
        how="left",
    )
    items = items.merge(trans, on="product_category_name", how="left")
    # Olist translation file is missing a few Portuguese names.
    fallback_en = {
        "portateis_cozinha_e_preparadores_de_alimentos": "portable_kitchen_food_preparers",
        "pc_gamer": "pc_gamer",
    }
    items["product_category"] = (
        items["product_category_name_english"]
        .fillna(items["product_category_name"].map(fallback_en))
        .fillna(items["product_category_name"])
    )
    items = items.merge(
        sellers[["seller_id"]],
        on="seller_id",
        how="left",
    )

    item_agg = items.groupby("order_id", as_index=False).agg(
        price=("price", "sum"),
        freight_value=("freight_value", "sum"),
    )
    primary = _primary_category(items)

    pay_agg = payments.groupby("order_id", as_index=False).agg(
        payment_value=("payment_value", "sum"),
        payment_installments=("payment_installments", "max"),
        payment_type=("payment_type", "first"),
    )
    review_agg = reviews.groupby("order_id", as_index=False).agg(
        review_score=("review_score", "mean"),
    )

    df = orders.merge(item_agg, on="order_id", how="inner")
    df = df.merge(primary, on="order_id", how="left")
    df = df.merge(pay_agg, on="order_id", how="left")
    df = df.merge(review_agg, on="order_id", how="left")

    df["order_purchase_timestamp"] = pd.to_datetime(df["order_purchase_timestamp"])
    df["year"] = df["order_purchase_timestamp"].dt.year
    df["year_month"] = df["order_purchase_timestamp"].dt.strftime("%Y-%m")
    df["payment_value"] = df["payment_value"].fillna(0)
    df["payment_installments"] = df["payment_installments"].fillna(1)
    df["price"] = df["price"].fillna(0)
    df["freight_value"] = df["freight_value"].fillna(0)

    df["profit"] = [
        order_profit(p, f, pay, inst)
        for p, f, pay, inst in zip(
            df["price"], df["freight_value"], df["payment_value"], df["payment_installments"]
        )
    ]
    df["is_loss"] = [is_loss(x) for x in df["profit"]]
    df["high_installment_risk"] = [
        high_installment_risk(x) for x in df["payment_installments"]
    ]

    cols = [
        "order_id", "customer_unique_id", "customer_state", "order_purchase_timestamp",
        "year", "year_month", "price", "freight_value", "payment_value",
        "payment_installments", "payment_type", "product_category", "review_score",
        "seller_id", "profit", "is_loss", "high_installment_risk",
    ]
    return df[cols].copy()


def write_outputs(orders, processed_csv, duckdb_path):
    os.makedirs(os.path.dirname(processed_csv) or ".", exist_ok=True)
    orders.to_csv(processed_csv, index=False)
    if os.path.exists(duckdb_path):
        os.remove(duckdb_path)
    con = duckdb.connect(duckdb_path)
    con.execute("CREATE TABLE orders AS SELECT * FROM orders")
    con.close()


def run_etl(data_dir, processed_csv, duckdb_path):
    orders = build_orders(load_raw(data_dir))
    write_outputs(orders, processed_csv, duckdb_path)
    return orders


if __name__ == "__main__":
    df = run_etl(
        "data/raw",
        "data/processed/analytics_ready.csv",
        "ecommerce_analytics.db",
    )
    print("Processed {:,} delivered orders".format(len(df)))
    print("Total Revenue : R$ {:,.0f}".format(df["payment_value"].sum()))
    print("Total Profit  : R$ {:,.0f}".format(df["profit"].sum()))
    print("Loss-Making % : {:.1f}%".format(df["is_loss"].mean() * 100))
