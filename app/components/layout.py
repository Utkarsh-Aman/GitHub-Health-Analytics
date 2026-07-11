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
                        6: {'label': '2023-07'},
                        12: {'label': '2024-01'},
                        18: {'label': '2024-07'},
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
    Six visualization panels in a 2 row x 3 column grid for overview.
    """
    panel_style = {
        'width': '32%',
        'display': 'inline-block',
        'verticalAlign': 'top',
        'padding': '10px',
        'boxSizing': 'border-box',
        'backgroundColor': '#ffffff',
        'borderRadius': '5px',
        'boxShadow': '0 1px 3px rgba(0,0,0,0.1)',
        'margin': '5px'
    }
    
    header_style = {'marginBottom': '5px', 'display': 'inline-block', 'fontSize': '15px'}
    btn_style = {'float': 'right', 'cursor': 'pointer', 'border': 'none', 'background': '#f1f5f9', 'borderRadius': '3px', 'padding': '2px 8px', 'fontSize': '12px', 'fontWeight': 'bold', 'color': '#475569'}
    p_style = {'color': 'grey', 'fontSize': '11px', 'marginTop': '0px', 'marginBottom': '4px'}
    graph_style = {'height': '200px'}

    panels = html.Div([

        # ── Row 1 ──
        html.Div([
            # Panel 1 — Streamgraph
            html.Div([
                html.Div([
                    html.H4("Adoption Trends", style=header_style),
                    html.Button("↗ Expand", id="btn-expand-streamgraph", style=btn_style)
                ]),
                html.P("Monthly human activity volume by ecosystem", style=p_style),
                dcc.Graph(id='streamgraph', style=graph_style, config={'displayModeBar': False})
            ], style=panel_style),

            # Panel 2 — Contributor Network
            html.Div([
                html.Div([
                    html.H4("Contributor Network", style=header_style),
                    html.Button("↗ Expand", id="btn-expand-network", style=btn_style)
                ]),
                html.Div(id='network-bus-factor-info', style={'fontSize': '11px', 'color': '#555', 'marginBottom': '2px'}),
                cyto.Cytoscape(
                    id='contributor-network',
                    layout={'name': 'cose'},
                    style={'width': '100%', 'height': '150px'},
                    stylesheet=[
                        {'selector': 'node', 'style': {'font-size': '7px', 'width': '12px', 'height': '12px', 'background-color': '#4C78A8', 'color': '#333'}},
                        {'selector': '.top-contributor', 'style': {'label': 'data(label)', 'background-color': '#ef4444', 'width': '18px', 'height': '18px', 'font-size': '8px', 'font-weight': 'bold'}},
                        {'selector': 'edge', 'style': {'width': 'mapData(weight, 1, 30, 0.5, 4)', 'line-color': '#cccccc', 'opacity': 0.6}}
                    ]
                )
            ], style=panel_style),

            # Panel 3 — PR Sankey
            html.Div([
                html.Div([
                    html.H4("PR Lifecycle & Latency", style=header_style),
                    html.Button("↗ Expand", id="btn-expand-sankey", style=btn_style)
                ]),
                html.P("Flow of PRs and review latency distribution", style=p_style),
                dcc.Graph(id='pr-sankey', style=graph_style, config={'displayModeBar': False})
            ], style=panel_style),

        ]),

        html.Br(),

        # ── Row 2 ──
        html.Div([
            # Panel 4 — Issue Heatmap
            html.Div([
                html.Div([
                    html.H4("Issue Responsiveness", style=header_style),
                    html.Button("↗ Expand", id="btn-expand-heatmap", style=btn_style)
                ]),
                html.P("Daily issue creation frequency", style=p_style),
                dcc.Graph(id='issue-heatmap', style=graph_style, config={'displayModeBar': False})
            ], style=panel_style),

            # Panel 5 — Bot Bar Chart
            html.Div([
                html.Div([
                    html.H4("Bot vs Human Activity", style=header_style),
                    html.Button("↗ Expand", id="btn-expand-botbar", style=btn_style)
                ]),
                html.P("Proportion of automated activity", style=p_style),
                dcc.Graph(id='bot-bar', style=graph_style, config={'displayModeBar': False})
            ], style=panel_style),

            # Panel 6 — Health Dashboard
            html.Div([
                html.Div([
                    html.H4("Health Dashboard", style=header_style),
                    html.Button("↗ Expand", id="btn-expand-dashboard", style=btn_style)
                ]),
                html.P("Key metrics compared side by side", style=p_style),
                dcc.Graph(id='health-dashboard', style=graph_style, config={'displayModeBar': False})
            ], style=panel_style)
        ]),
        
        # ── Modal Overlay ──
        html.Div(
            id="detail-modal",
            style={
                "display": "none",
                "position": "fixed",
                "zIndex": "1000",
                "left": "0",
                "top": "0",
                "width": "100%",
                "height": "100%",
                "backgroundColor": "rgba(0,0,0,0.6)",
                "justifyContent": "center",
                "alignItems": "center"
            },
            children=[
                html.Div(
                    style={
                        "backgroundColor": "#fff",
                        "padding": "20px",
                        "borderRadius": "8px",
                        "width": "85%",
                        "height": "85%",
                        "display": "flex",
                        "flexDirection": "column"
                    },
                    children=[
                        html.Div([
                            html.Button(
                                "✖ Close", 
                                id="btn-close-modal", 
                                style={
                                    "float": "right", "cursor": "pointer", 
                                    "border": "none", "background": "#ef4444", 
                                    "color": "white", "padding": "5px 15px", 
                                    "borderRadius": "4px", "fontWeight": "bold"
                                }
                            ),
                            html.H3("Detailed View", style={"marginTop": "0"})
                        ]),
                        html.Div(id="modal-content", style={"flexGrow": "1", "marginTop": "15px", "position": "relative"})
                    ]
                )
            ]
        )

    ], style={'padding': '5px'})
    return panels
