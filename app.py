"""Enterprise Retail Analytics - Plotly Dash Dashboard."""
import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd
import duckdb

con = duckdb.connect('ecommerce_analytics.db', read_only=True)
df = con.execute("SELECT * FROM orders").fetchdf()

top_cats = df['product_category_name'].value_counts().head(15).index.tolist()
df['category_display'] = df['product_category_name'].where(
    df['product_category_name'].isin(top_cats), 'Other'
)

STATE_NAMES = {
    'AC': 'Acre', 'AL': 'Alagoas', 'AP': 'Amapá', 'AM': 'Amazonas',
    'BA': 'Bahia', 'CE': 'Ceará', 'DF': 'Distrito Federal',
    'ES': 'Espírito Santo', 'GO': 'Goiás', 'MA': 'Maranhão',
    'MT': 'Mato Grosso', 'MS': 'Mato Grosso do Sul', 'MG': 'Minas Gerais',
    'PA': 'Pará', 'PB': 'Paraíba', 'PR': 'Paraná', 'PE': 'Pernambuco',
    'PI': 'Piauí', 'RJ': 'Rio de Janeiro', 'RN': 'Rio Grande do Norte',
    'RS': 'Rio Grande do Sul', 'RO': 'Rondônia', 'RR': 'Roraima',
    'SC': 'Santa Catarina', 'SP': 'São Paulo', 'SE': 'Sergipe',
    'TO': 'Tocantins',
}
STATES = sorted(df['customer_state'].dropna().unique())
STATE_OPTIONS = [
    {'label': f"{STATE_NAMES.get(s, s)} ({s})", 'value': s}
    for s in STATES
]
STATE_OPTIONS.sort(key=lambda o: o['label'])

app = dash.Dash(__name__, title="Enterprise Retail Analytics")
server = app.server

app.layout = html.Div([
    html.Div([
        html.H1("Enterprise Retail Analytics", style={'margin': '0'}),
        html.P("Profitability & Risk Dashboard · 96K+ delivered orders",
               style={'margin': '5px 0 0 0', 'color': '#666'}),
        html.P("Made by Ishika Kour",
               style={'margin': '6px 0 0 0', 'color': '#888', 'fontSize': '13px'}),
    ], style={'padding': '30px 40px 10px 40px'}),

    html.Div([
        dcc.Dropdown(
            id='state-dropdown',
            options=STATE_OPTIONS,
            value='SP', clearable=False, style={'width': '300px'}
        ),
    ], style={'padding': '0 40px 20px 40px'}),

    html.Div(id='kpi-cards', style={
        'display': 'grid', 'gridTemplateColumns': 'repeat(4, 1fr)',
        'gap': '20px', 'padding': '0 40px 20px 40px'
    }),

    html.Div([dcc.Graph(id='profit-by-category')], style={'padding': '0 40px'}),
    html.Div([dcc.Graph(id='profit-by-month')], style={'padding': '0 40px 40px 40px'}),
], style={'fontFamily': 'Inter, system-ui, sans-serif',
          'background': '#fafafa', 'minHeight': '100vh'})


@app.callback(
    [Output('kpi-cards', 'children'),
     Output('profit-by-category', 'figure'),
     Output('profit-by-month', 'figure')],
    [Input('state-dropdown', 'value')]
)
def update(state):
    d = df[df['customer_state'] == state]

    def card(label, value, color='#111'):
        return html.Div([
            html.P(label, style={'margin': '0', 'fontSize': '12px',
                                 'letterSpacing': '0.5px', 'color': '#888',
                                 'textTransform': 'uppercase'}),
            html.H2(value, style={'margin': '5px 0 0 0', 'color': color}),
        ], style={'background': 'white', 'padding': '20px',
                  'borderRadius': '10px',
                  'boxShadow': '0 1px 3px rgba(0,0,0,0.06)'})

    revenue = d['payment_value'].sum()
    profit = d['profit'].sum()
    orders = len(d)
    loss_pct = d['is_loss'].mean() * 100

    kpis = [
        card("Revenue", f"R$ {revenue/1e6:.2f}M"),
        card("Profit", f"R$ {profit/1e6:.2f}M",
             '#22c55e' if profit > 0 else '#dc2626'),
        card("Orders", f"{orders:,}"),
        card("Loss-Making Orders", f"{loss_pct:.1f}%",
             '#dc2626' if loss_pct > 5 else '#22c55e'),
    ]

    cat = (d.groupby('category_display', as_index=False)['profit']
             .sum().sort_values('profit').tail(15))
    fig1 = px.bar(cat, x='profit', y='category_display', orientation='h',
                  color='profit', color_continuous_scale='RdYlGn')
    fig1.update_layout(title="Profit by Product Category",
                       showlegend=False, coloraxis_showscale=False,
                       height=450, margin=dict(l=0, r=0, t=40, b=0))

    months = ['January','February','March','April','May','June',
              'July','August','September','October','November','December']
    m = d.groupby('month', as_index=False)['profit'].sum()
    m['month'] = pd.Categorical(m['month'], months, ordered=True)
    m = m.sort_values('month')
    fig2 = px.line(m, x='month', y='profit', markers=True)
    fig2.update_traces(line_color='#6366f1', line_width=3)
    fig2.update_layout(title="Profit Trend by Month",
                       height=400, margin=dict(l=0, r=0, t=40, b=0))

    return kpis, fig1, fig2


if __name__ == '__main__':
    app.run(debug=True)