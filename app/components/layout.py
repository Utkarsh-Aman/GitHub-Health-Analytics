import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))

from dash import dcc, html
import dash_cytoscape as cyto
from app.globals import REPOS, ECOSYSTEMS, MONTHS


def create_filters():
    """
    Global filter bar at the top of the app.
    Repo filter, ecosystem filter, date slider, bot toggle.
    """
    return html.Div([

        html.H1(
            "GitHub Repository Health Analytics",
            style={
                'textAlign': 'center',
                'marginBottom': '5px',
                'fontSize': '24px'
            }
        ),
        html.P(
            "CS661 Big Data Visual Analytics | IIT Kanpur | Group __",
            style={
                'textAlign': 'center',
                'color': 'grey',
                'marginTop': '0px',
                'marginBottom': '15px'
            }
        ),

        html.Hr(),

        html.Div([

            # Repo multi-select
            html.Div([
                html.Label("Repositories",
                           style={'fontWeight': 'bold',
                                  'marginBottom': '4px'}),
                dcc.Dropdown(
                    id='repo-filter',
                    options=[{'label': r, 'value': r}
                             for r in REPOS],
                    value=['facebook/react', 'pytorch/pytorch'],
                    multi=True,
                    placeholder='Select repositories...'
                )
            ], style={
                'width': '35%',
                'display': 'inline-block',
                'verticalAlign': 'top',
                'paddingRight': '15px'
            }),

            # Ecosystem filter
            html.Div([
                html.Label("Ecosystem",
                           style={'fontWeight': 'bold',
                                  'marginBottom': '4px'}),
                dcc.Dropdown(
                    id='ecosystem-filter',
                    options=[{'label': e, 'value': e}
                             for e in ECOSYSTEMS],
                    placeholder='All ecosystems...',
                    clearable=True
                )
            ], style={
                'width': '15%',
                'display': 'inline-block',
                'verticalAlign': 'top',
                'paddingRight': '15px'
            }),

            # Date range slider
            html.Div([
                html.Label("Date Range",
                           style={'fontWeight': 'bold',
                                  'marginBottom': '4px'}),
                dcc.RangeSlider(
                    id='month-slider',
                    min=0,
                    max=len(MONTHS) - 1,
                    value=[0, len(MONTHS) - 1],
                    marks={
                        0: {'label': '2023-01'},
                        5: {'label': '2023-06'},
                        11: {'label': '2023-12'},
                        12: {'label': '2024-01'},
                        17: {'label': '2024-06'},
                        23: {'label': '2024-12'}
                    },
                    step=1,
                    tooltip={
                        "placement": "bottom",
                        "always_visible": False
                    }
                )
            ], style={
                'width': '35%',
                'display': 'inline-block',
                'verticalAlign': 'top',
                'paddingRight': '15px'
            }),

            # Bot toggle
            html.Div([
                html.Label("Bots",
                           style={'fontWeight': 'bold',
                                  'marginBottom': '4px'}),
                dcc.RadioItems(
                    id='bot-toggle',
                    options=[
                        {'label': 'Exclude', 'value': 0},
                        {'label': 'Include', 'value': 1}
                    ],
                    value=0,
                    inline=False
                )
            ], style={
                'width': '10%',
                'display': 'inline-block',
                'verticalAlign': 'top'
            })

        ], style={
            'padding': '15px',
            'backgroundColor': '#f5f5f5',
            'borderRadius': '5px',
            'marginBottom': '20px'
        })
    ])


def create_panels():
    """
    Six visualization panels in a 3 row x 2 column grid.
    """
    panel_style = {
        'width': '49%',
        'display': 'inline-block',
        'verticalAlign': 'top',
        'padding': '10px',
        'boxSizing': 'border-box',
        'backgroundColor': '#ffffff',
        'borderRadius': '5px',
        'boxShadow': '0 1px 3px rgba(0,0,0,0.1)',
        'margin': '5px'
    }

    return html.Div([

        # ── Row 1: Streamgraph + Contributor Network ──
        html.Div([

            # Panel 1 — Streamgraph
            html.Div([
                html.H4(
                    "Technology Adoption Trends",
                    style={'marginBottom': '5px'}
                ),
                html.P(
                    "Monthly human activity volume by ecosystem",
                    style={'color': 'grey', 'fontSize': '12px',
                           'marginTop': '0px'}
                ),
                dcc.Graph(
                    id='streamgraph',
                    style={'height': '320px'},
                    config={'displayModeBar': False}
                )
            ], style=panel_style),

            # Panel 2 — Contributor Network
            html.Div([
                html.H4(
                    "Contributor Collaboration Network",
                    style={'marginBottom': '5px'}
                ),
                html.P(
                    "Select one repository to view its network",
                    style={'color': 'grey', 'fontSize': '12px',
                           'marginTop': '0px'}
                ),

                # Separate single-repo dropdown for network
                dcc.Dropdown(
                    id='network-repo-filter',
                    options=[{'label': r, 'value': r}
                             for r in REPOS],
                    value='facebook/react',
                    multi=False,
                    placeholder='Select one repository...',
                    style={'marginBottom': '8px'}
                ),

                # Bus factor info text
                html.Div(
                    id='network-bus-factor-info',
                    style={
                        'fontSize': '12px',
                        'color': '#555',
                        'marginBottom': '6px',
                        'padding': '4px'
                    }
                ),

                # Cytoscape network graph
                cyto.Cytoscape(
                    id='contributor-network',
                    layout={'name': 'cose'},
                    style={'width': '100%', 'height': '260px'},
                    stylesheet=[
                        {
                            'selector': 'node',
                            'style': {
                                'label': 'data(label)',
                                'font-size': '7px',
                                'width': '12px',
                                'height': '12px',
                                'background-color': '#4C78A8',
                                'color': '#333'
                            }
                        },
                        {
                            'selector': '.top-contributor',
                            'style': {
                                'background-color': '#ef4444',
                                'width': '22px',
                                'height': '22px',
                                'font-size': '8px',
                                'font-weight': 'bold'
                            }
                        },
                        {
                            'selector': 'edge',
                            'style': {
                                'width': 'mapData(weight, 1, 30, 0.5, 4)',
                                'line-color': '#cccccc',
                                'opacity': 0.6
                            }
                        }
                    ]
                )
            ], style=panel_style)

        ]),

        html.Br(),

        # ── Row 2: PR Sankey + Issue Heatmap ──
        html.Div([

            # Panel 3 — PR Sankey
            html.Div([
                html.H4(
                    "PR Lifecycle and Review Latency",
                    style={'marginBottom': '5px'}
                ),
                html.P(
                    "Flow of PRs from opened to merged or closed",
                    style={'color': 'grey', 'fontSize': '12px',
                           'marginTop': '0px'}
                ),
                dcc.Graph(
                    id='pr-sankey',
                    style={'height': '320px'},
                    config={'displayModeBar': False}
                )
            ], style=panel_style),

            # Panel 4 — Issue Heatmap
            html.Div([
                html.H4(
                    "Issue Responsiveness",
                    style={'marginBottom': '5px'}
                ),
                html.P(
                    "Daily issue creation frequency — gaps = inactivity",
                    style={'color': 'grey', 'fontSize': '12px',
                           'marginTop': '0px'}
                ),
                dcc.Graph(
                    id='issue-heatmap',
                    style={'height': '320px'},
                    config={'displayModeBar': False}
                )
            ], style=panel_style)

        ]),

        html.Br(),

        # ── Row 3: Bot Bar + Health Dashboard ──
        html.Div([

            # Panel 5 — Bot Bar Chart
            html.Div([
                html.H4(
                    "Bot vs Human Activity",
                    style={'marginBottom': '5px'}
                ),
                html.P(
                    "How much of each repo's activity is automated",
                    style={'color': 'grey', 'fontSize': '12px',
                           'marginTop': '0px'}
                ),
                dcc.Graph(
                    id='bot-bar',
                    style={'height': '320px'},
                    config={'displayModeBar': False}
                )
            ], style=panel_style),

            # Panel 6 — Health Dashboard
            html.Div([
                html.H4(
                    "Repository Health Dashboard",
                    style={'marginBottom': '5px'}
                ),
                html.P(
                    "Key health metrics compared side by side",
                    style={'color': 'grey', 'fontSize': '12px',
                           'marginTop': '0px'}
                ),
                dcc.Graph(
                    id='health-dashboard',
                    style={'height': '320px'},
                    config={'displayModeBar': False}
                )
            ], style=panel_style)

        ])

    ], style={'padding': '5px'})