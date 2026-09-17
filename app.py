"""Enterprise Retail Analytics - Plotly Dash Dashboard.

DuckDB-backed SQL analytics engine. Queries live in analysis.sql.
"""
import os

import dash
from dash import dcc, html, Input, Output
import duckdb
import plotly.express as px

DATABASE_PATH = os.environ.get("DATABASE_PATH", "ecommerce_analytics.db")

STATE_NAMES = {
    "AC": "Acre", "AL": "Alagoas", "AP": "Amapá", "AM": "Amazonas",
    "BA": "Bahia", "CE": "Ceará", "DF": "Distrito Federal",
    "ES": "Espírito Santo", "GO": "Goiás", "MA": "Maranhão",
    "MT": "Mato Grosso", "MS": "Mato Grosso do Sul", "MG": "Minas Gerais",
    "PA": "Pará", "PB": "Paraíba", "PR": "Paraná", "PE": "Pernambuco",
    "PI": "Piauí", "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte",
    "RS": "Rio Grande do Sul", "RO": "Rondônia", "RR": "Roraima",
    "SC": "Santa Catarina", "SP": "São Paulo", "SE": "Sergipe",
    "TO": "Tocantins",
}

KPI_SQL = """
SELECT
    COALESCE(SUM(payment_value), 0) AS revenue,
    COALESCE(SUM(profit), 0) AS total_profit,
    COUNT(DISTINCT order_id) AS orders,
    100.0 * AVG(CASE WHEN is_loss THEN 1 ELSE 0 END) AS loss_pct
FROM orders
WHERE {where}
"""

CATEGORY_SQL = """
WITH cat_profit AS (
    SELECT
        REPLACE(product_category, '_', ' ') AS category,
        SUM(profit) AS profit,
        COUNT(*) AS orders
    FROM orders
    WHERE {where}
      AND product_category IS NOT NULL
      AND product_category <> ''
    GROUP BY product_category
)
SELECT
    category,
    profit,
    orders,
    DENSE_RANK() OVER (ORDER BY profit DESC) AS profit_rank
FROM cat_profit
ORDER BY profit ASC
"""

MONTHLY_SQL = """
WITH monthly AS (
    SELECT year_month, SUM(profit) AS profit
    FROM orders
    WHERE {where}
    GROUP BY year_month
)
SELECT
    year_month,
    profit,
    SUM(profit) OVER (ORDER BY year_month) AS running_profit
FROM monthly
ORDER BY year_month
"""


def connect(path):
    if not os.path.exists(path):
        return None
    return duckdb.connect(path, read_only=True)


def segment_filter(state, category):
    clauses = ["1=1"]
    params = []
    if state and state != "ALL":
        clauses.append("customer_state = ?")
        params.append(state)
    if category and category != "ALL":
        clauses.append("product_category = ?")
        params.append(category)
    return " AND ".join(clauses), params


CATEGORY_LABELS = {
    "portateis_cozinha_e_preparadores_de_alimentos": "Portable Kitchen Food Preparers",
    "portable_kitchen_food_preparers": "Portable Kitchen Food Preparers",
    "pc_gamer": "PC Gamer",
}


def pretty_category(name):
    if not isinstance(name, str) or not name:
        return "Unknown"
    if name in CATEGORY_LABELS:
        return CATEGORY_LABELS[name]
    return name.replace("_", " ").title()


def filter_options(values, labels=None):
    opts = [{"label": "All", "value": "ALL"}]
    for value in values:
        if labels and value in labels:
            label = "{} ({})".format(labels[value], value)
        else:
            label = pretty_category(value)
        opts.append({"label": label, "value": value})
    return opts


def distinct_values(con, column):
    if con is None:
        return []
    sql = (
        "SELECT DISTINCT {} FROM orders "
        "WHERE {} IS NOT NULL AND CAST({} AS VARCHAR) <> '' "
        "ORDER BY 1"
    ).format(column, column, column)
    return [row[0] for row in con.execute(sql).fetchall()]


def card(label, value, color="#111"):
    return html.Div([
        html.P(label, style={"margin": "0", "fontSize": "12px",
                             "letterSpacing": "0.5px", "color": "#888",
                             "textTransform": "uppercase"}),
        html.H2(value, style={"margin": "5px 0 0 0", "color": color}),
    ], style={"background": "white", "padding": "20px",
              "borderRadius": "10px",
              "boxShadow": "0 1px 3px rgba(0,0,0,0.06)"})


con = connect(DATABASE_PATH)
STATES = distinct_values(con, "customer_state")
CATEGORIES = distinct_values(con, "product_category")


def fetch_kpis(state, category):
    where, params = segment_filter(state, category)
    row = con.execute(KPI_SQL.format(where=where), params).fetchdf().iloc[0]
    loss = row["loss_pct"]
    return {
        "revenue": float(row["revenue"] or 0),
        "profit": float(row["total_profit"] or 0),
        "orders": int(row["orders"] or 0),
        "loss_pct": 0.0 if loss is None else float(loss),
    }


def fetch_category_profit(state, category):
    where, params = segment_filter(state, category)
    frame = con.execute(CATEGORY_SQL.format(where=where), params).fetchdf()
    if len(frame):
        frame["category"] = frame["category"].map(pretty_category)
    return frame


def fetch_monthly_profit(state, category):
    where, params = segment_filter(state, category)
    return con.execute(MONTHLY_SQL.format(where=where), params).fetchdf()


app = dash.Dash(__name__, title="Enterprise Retail Analytics")
server = app.server

app.layout = html.Div([
    html.Div([
        html.H1("Enterprise Retail Analytics", style={"margin": "0"}),
        html.P("Profitability & Risk Dashboard · 96K+ delivered orders",
               style={"margin": "5px 0 0 0", "color": "#666"}),
        html.P("Made by Ishika Kour",
               style={"margin": "6px 0 0 0", "color": "#888", "fontSize": "13px"}),
    ], style={"padding": "30px 40px 10px 40px"}),

    html.Div([
        dcc.Dropdown(
            id="filter-state",
            options=filter_options(STATES, STATE_NAMES),
            value="ALL",
            clearable=False,
            style={"width": "300px"},
        ),
        dcc.Dropdown(
            id="filter-category",
            options=filter_options(CATEGORIES),
            value="ALL",
            clearable=False,
            style={"width": "350px"},
        ),
    ], style={"padding": "0 40px 20px 40px", "display": "flex", "gap": "12px"}),

    html.Div(id="kpi-cards", style={
        "display": "grid", "gridTemplateColumns": "repeat(4, 1fr)",
        "gap": "20px", "padding": "0 40px 20px 40px",
    }),

    html.Div([dcc.Graph(id="fig-category")], style={"padding": "0 40px"}),
    html.Div([dcc.Graph(id="fig-trend")], style={"padding": "0 40px 40px 40px"}),
], style={"fontFamily": "Inter, system-ui, sans-serif",
          "background": "#fafafa", "minHeight": "100vh"})


@app.callback(
    [Output("kpi-cards", "children"),
     Output("fig-category", "figure"),
     Output("fig-trend", "figure")],
    [Input("filter-state", "value"),
     Input("filter-category", "value")],
)
def update(state, category):
    vals = fetch_kpis(state, category)
    kpis = [
        card("Revenue", "R$ {:,.2f}M".format(vals["revenue"] / 1e6)),
        card("Profit", "R$ {:,.2f}M".format(vals["profit"] / 1e6),
             "#22c55e" if vals["profit"] >= 0 else "#dc2626"),
        card("Orders", "{:,}".format(vals["orders"])),
        card("Loss-Making Orders", "{:.1f}%".format(vals["loss_pct"]),
             "#dc2626" if vals["loss_pct"] > 5 else "#22c55e"),
    ]

    cat = fetch_category_profit(state, category)
    fig1 = px.bar(cat, x="profit", y="category", orientation="h",
                  color="profit", color_continuous_scale="RdYlGn")
    fig1.update_layout(title="Profit by Product Category",
                       showlegend=False, coloraxis_showscale=False,
                       height=450, margin=dict(l=0, r=0, t=40, b=0),
                       yaxis_title="")

    monthly = fetch_monthly_profit(state, category)
    fig2 = px.line(monthly, x="year_month", y="profit", markers=True)
    fig2.update_traces(line_color="#6366f1", line_width=3, name="Monthly Profit")
    if len(monthly):
        fig2.add_scatter(
            x=monthly["year_month"], y=monthly["running_profit"],
            mode="lines", line=dict(color="#22c55e", dash="dash"),
            name="Running Total",
        )
    fig2.update_layout(title="Profit Trend by Month (with Running Total)",
                       height=400, margin=dict(l=0, r=0, t=40, b=0),
                       xaxis_title="")

    return kpis, fig1, fig2


if __name__ == "__main__":
    app.run(debug=True)
