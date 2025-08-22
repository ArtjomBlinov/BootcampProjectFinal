# app/dash_app.py
import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from dash import dcc, html
from dash.dependencies import Input, Output, State

# Setup 
API_BASE_URL = "http://127.0.0.1:8000"
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CYBORG])
app.title = "COVID-19 Advanced Dashboard"

def get_countries_from_api():
    try:
        response = requests.get(f"{API_BASE_URL}/api/countries")
        response.raise_for_status()
        return [{'label': c, 'value': c} for c in response.json()['countries']]
    except requests.exceptions.RequestException:
        return []

# Reusable Components 
def create_kpi_card(title, value, id):
    return dbc.Card(
        dbc.CardBody([
            html.H4(title, className="card-title"),
            html.H2(value, className="card-text", id=id)
        ]),
        className="text-center m-2"
    )

# App Layout
app.layout = dbc.Container([
    dbc.Row(dbc.Col(html.H1("COVID-19 Advanced Dashboard", className="text-center text-primary mt-4 mb-4"))),
    
    dbc.Row([
        dbc.Col([
            html.Label("Select Country:"),
            dcc.Dropdown(id='country-dropdown', options=get_countries_from_api(), value='Latvia'),
        ], width=12)
    ], className="mb-4"),

    # KPI Cards Row
    dbc.Row([
        dbc.Col(create_kpi_card("Total Confirmed Cases", "0", "kpi-total-cases"), md=4),
        dbc.Col(create_kpi_card("Total Deaths", "0", "kpi-total-deaths"), md=4),
        dbc.Col(create_kpi_card("Case Fatality Rate", "0%", "kpi-mortality-rate"), md=4)
    ]),

    # Charts Row
    dbc.Row([
        dbc.Col(dcc.Loading(dcc.Graph(id='cases-graph')), md=6),
        dbc.Col(dcc.Loading(dcc.Graph(id='deaths-graph')), md=6)
    ], className="mt-4"),
    dbc.Row([
        dbc.Col(dcc.Loading(dcc.Graph(id='daily-cases-graph')), md=6),
        dbc.Col(dcc.Loading(dcc.Graph(id='pie-chart')), md=6)
    ], className="mt-4"),
    
    # Forecast Row
    dbc.Row([
        dbc.Col(dcc.Loading(dcc.Graph(id='forecast-graph')), width=12)
    ], className="mt-4")

], fluid=True, className="dbc")

# Callbacks
@app.callback(
    [Output('kpi-total-cases', 'children'),
     Output('kpi-total-deaths', 'children'),
     Output('kpi-mortality-rate', 'children'),
     Output('cases-graph', 'figure'),
     Output('deaths-graph', 'figure'),
     Output('daily-cases-graph', 'figure'),
     Output('pie-chart', 'figure'),
     Output('forecast-graph', 'figure')],
    [Input('country-dropdown', 'value')]
)
def update_dashboard(country):
    if not country:
        return ["0"] * 3 + [{}] * 5

    # Fetch data from API
    try:
        summary_res = requests.get(f"{API_BASE_URL}/api/summary/{country}")
        summary_res.raise_for_status()
        summary_data = summary_res.json()

        ts_res = requests.get(f"{API_BASE_URL}/api/timeseries/{country}")
        ts_res.raise_for_status()
        ts_data = ts_res.json()
        df = pd.DataFrame(ts_data)
        
        forecast_res = requests.get(f"{API_BASE_URL}/api/forecast/{country}")
        forecast_res.raise_for_status()
        forecast_data = forecast_res.json()
    except requests.exceptions.RequestException:
        return ["Error"] * 3 + [{}] * 5

    # KPIs
    kpi_cases = f"{summary_data['total_cases']:,}"
    kpi_deaths = f"{summary_data['total_deaths']:,}"
    kpi_mortality = f"{summary_data['mortality_rate']}%"
    
    # Figures 
    df_confirmed = df[df['CASE_TYPE'] == 'Confirmed'].copy()
    df_deaths = df[df['CASE_TYPE'] == 'Deaths'].copy()
    df_confirmed['DAILY_NEW'] = df_confirmed['CASES'].diff().fillna(0).clip(lower=0)
    
    cases_fig = px.area(df_confirmed, x='DATE', y='CASES', title=f'Cumulative Cases in {country}', template='plotly_dark')
    deaths_fig = px.area(df_deaths, x='DATE', y='CASES', title=f'Cumulative Deaths in {country}', template='plotly_dark')
    daily_fig = px.bar(df_confirmed, x='DATE', y='DAILY_NEW', title=f'Daily New Cases in {country}', template='plotly_dark')
    
    pie_fig_data = {'values': [summary_data['total_deaths'], summary_data['total_cases'] - summary_data['total_deaths']],
                    'labels': ['Deaths', 'Active/Recovered']}
    pie_fig = px.pie(pie_fig_data, values='values', names='labels', title=f'Case Distribution in {country}', hole=.3, template='plotly_dark')
    
    # Forecast Figure
    if forecast_data:
        df_forecast = pd.DataFrame(forecast_data)
        forecast_fig = go.Figure(layout=go.Layout(template='plotly_dark', title=f'90-Day Case Forecast'))
        forecast_fig.add_trace(go.Scatter(x=df_forecast['ds'], y=df_forecast['yhat_upper'], fill=None, mode='lines', line_color='rgba(0,100,80,0.2)', name='Upper Bound'))
        forecast_fig.add_trace(go.Scatter(x=df_forecast['ds'], y=df_forecast['yhat_lower'], fill='tonexty', mode='lines', line_color='rgba(0,100,80,0.2)', name='Lower Bound'))
        forecast_fig.add_trace(go.Scatter(x=df_forecast['ds'], y=df_forecast['yhat'], mode='lines', line_color='cyan', name='Forecast'))
        forecast_fig.add_trace(go.Scatter(x=df_confirmed['DATE'], y=df_confirmed['CASES'], mode='markers', marker_color='orange', name='Actual Cases'))
    else:
        forecast_fig = go.Figure(layout=go.Layout(template='plotly_dark', title=f'Forecast not available for {country}'))

    return kpi_cases, kpi_deaths, kpi_mortality, cases_fig, deaths_fig, daily_fig, pie_fig, forecast_fig

if __name__ == '__main__':
    app.run(debug=True)