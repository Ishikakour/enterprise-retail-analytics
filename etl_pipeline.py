"""ETL: Olist raw CSVs -> analytics-ready dataset + DuckDB."""
import pandas as pd
import duckdb
import os

print("Loading Olist datasets...")
orders    = pd.read_csv('data/raw/olist_orders_dataset.csv')
items     = pd.read_csv('data/raw/olist_order_items_dataset.csv')
products  = pd.read_csv('data/raw/olist_products_dataset.csv')
payments  = pd.read_csv('data/raw/olist_order_payments_dataset.csv')
customers = pd.read_csv('data/raw/olist_customers_dataset.csv')
orders = orders.merge(
    customers[['customer_id', 'customer_state']],
    on='customer_id', how='left'
)

print(f"Orders: {len(orders):,} | Items: {len(items):,}")

# Merge
items = items.merge(products[['product_id', 'product_category_name']], on='product_id', how='left')
df = items.merge(
    orders[['order_id', 'customer_id', 'order_status',
            'order_purchase_timestamp', 'customer_state']],
    on='order_id', how='left'
)

# Aggregate payments per order
pay_agg = payments.groupby('order_id', as_index=False).agg(
    payment_value=('payment_value', 'sum'),
    payment_installments=('payment_installments', 'max'),
    payment_type=('payment_type', 'first'),
)
df = df.merge(pay_agg, on='order_id', how='left')

# Delivered only
df = df[df['order_status'] == 'delivered'].copy()

# Date features
df['order_purchase_timestamp'] = pd.to_datetime(df['order_purchase_timestamp'])
df['month'] = df['order_purchase_timestamp'].dt.month_name()
df['year'] = df['order_purchase_timestamp'].dt.year

# Profit proxy
df['payment_fee'] = df['payment_value'] * 0.03
df['profit'] = df['payment_value'] - df['freight_value'] - df['payment_fee']

# Risk flags
df['is_loss'] = df['profit'] < 0
df['high_installment_risk'] = df['payment_installments'] >= 6

# Save
os.makedirs('data/processed', exist_ok=True)
df.to_csv('data/processed/analytics_ready.csv', index=False)

# DuckDB
if os.path.exists('ecommerce_analytics.db'):
    os.remove('ecommerce_analytics.db')
con = duckdb.connect('ecommerce_analytics.db')
con.execute("CREATE TABLE orders AS SELECT * FROM df")
con.close()

print(f"\nProcessed {len(df):,} delivered orders")
print(f"Total Revenue : R$ {df['payment_value'].sum():,.0f}")
print(f"Total Profit  : R$ {df['profit'].sum():,.0f}")
print(f"Loss-Making % : {df['is_loss'].mean()*100:.1f}%")