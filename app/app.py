from dash import Dash, dcc, html
import dash_cytoscape as cyto
import plotly.express as px
import sqlite3
import pandas as pd

app = Dash(__name__)

# Load repo list for dropdown
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
conn = sqlite3.connect(os.path.join(BASE_DIR, 'github_analytics.db'))
repos = pd.read_sql("SELECT DISTINCT repo FROM events", conn)['repo'].tolist()
conn.close()

app.layout = html.Div([
    html.H1("GitHub Repository Health Analytics"),

    # Global filters
    html.Div([
        dcc.Dropdown(
            id='repo-filter',
            options=[{'label': r, 'value': r} for r in repos],
            multi=True,
            placeholder='Select repositories...'
        ),
        dcc.Dropdown(
            id='ecosystem-filter',
            options=[
                {'label': 'Frontend', 'value': 'Frontend'},
                {'label': 'ML/Data', 'value': 'ML/Data'},
                {'label': 'Backend/DevOps', 'value': 'Backend/DevOps'}
            ],
            placeholder='Select ecosystem...'
        )
    ]),

    # Placeholder panels
    html.Div([
        dcc.Graph(id='streamgraph'),
        dcc.Graph(id='pr-sankey'),
        dcc.Graph(id='issue-heatmap'),
        dcc.Graph(id='bot-bar'),
        dcc.Graph(id='health-dashboard'),
    ]),

    # Contributor Collaboration Network panel
    # Network edges are per-repo, so this uses its own single-select
    # dropdown rather than the global multi-select repo-filter.
    html.Div([
        html.H3("Contributor Collaboration Network"),
        dcc.Dropdown(
            id='network-repo-filter',
            options=[{'label': r, 'value': r} for r in repos],
            multi=False,
            placeholder='Select a single repository...'
        ),
        html.Div(id='network-bus-factor-info', style={'margin': '8px 0'}),
        cyto.Cytoscape(
            id='contributor-network',
            layout={'name': 'cose'},
            style={'width': '100%', 'height': '600px'},
            elements=[],
            stylesheet=[
                {
                    'selector': 'node',
                    'style': {
                        'label': 'data(label)',
                        'width': 'mapData(centrality, 0, 1, 12, 50)',
                        'height': 'mapData(centrality, 0, 1, 12, 50)',
                        'background-color': '#4C78A8',
                        'font-size': '8px',
                    }
                },
                {
                    'selector': '.top-contributor',
                    'style': {
                        'background-color': '#F58518',
                    }
                },
                {
                    'selector': 'edge',
                    'style': {
                        'width': 'mapData(weight, 1, 10, 1, 6)',
                        'line-color': '#CCCCCC',
                        'curve-style': 'bezier',
                    }
                },
            ],
        ),
    ]),
])

# Register callbacks (each module attaches its @app.callback to `app`
# on import). Must come after app.layout is defined.
from app.callbacks import streamgraph_cb, network_cb  # noqa: E402,F401

if __name__ == '__main__':
    app.run(debug=True)