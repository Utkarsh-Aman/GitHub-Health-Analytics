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

        html.Div([
            html.H2(
                "GitHub Repository Health Analytics",
                style={'display': 'inline', 'margin': '0', 'fontSize': '22px'}
            ),
            html.Span(
                " | CS661 Big Data Visual Analytics | IIT Kanpur | Group __",
                style={'color': 'grey', 'marginLeft': '10px'}
            )
        ], style={'textAlign': 'center', 'marginBottom': '10px'}),

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
                'width': '30%',
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
                'width': '40%',
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
            }),
        ], style={
            'padding': '10px 15px',
            'backgroundColor': 'var(--card-bg)',
            'borderRadius': '5px',
            'marginBottom': '10px',
            'boxShadow': '0 4px 6px -1px var(--shadow-color)',
            'marginLeft': '5px',
            'marginRight': '5px'
        })
    ])


def create_panels():
    """
    Six visualization panels in a 2 row x 3 column grid for overview.
    """
    panel_style_base = {
        'padding': '10px',
        'boxSizing': 'border-box',
        'backgroundColor': 'var(--card-bg)',
        'borderRadius': '5px',
        'boxShadow': '0 4px 6px -1px var(--shadow-color)',
        'margin': '5px',
        'display': 'flex',
        'flexDirection': 'column',
        'justifyContent': 'space-between'
    }
    
    panel_style_left = {**panel_style_base, 'width': 'calc(32% - 10px)'}
    panel_style_mid = {**panel_style_base, 'width': 'calc(28% - 10px)'}
    panel_style_right = {**panel_style_base, 'width': 'calc(40% - 10px)'}
    
    header_style = {'marginBottom': '5px', 'display': 'inline-block', 'fontSize': '15px', 'color': 'var(--text-primary)'}
    btn_style = {'float': 'right', 'cursor': 'pointer', 'border': 'none', 'background': 'var(--bg-color)', 'borderRadius': '3px', 'padding': '2px 8px', 'fontSize': '12px', 'fontWeight': 'bold', 'color': 'var(--text-primary)'}
    p_style = {'color': 'var(--text-muted)', 'fontSize': '11px', 'marginTop': '0px', 'marginBottom': '4px'}
    p_style_bottom = {'color': 'var(--text-muted)', 'fontSize': '11px', 'marginTop': '4px', 'marginBottom': '0px'}
    graph_style = {'height': '220px'}

    panels = html.Div([

        # ── Row 1 ──
        html.Div([
            # Panel 1 — Streamgraph
            html.Div([
                html.Div([
                    html.H4("Adoption Trends", style=header_style),
                    dcc.RadioItems(
                        id='streamgraph-group-by',
                        options=[
                            {'label': 'By Ecosystem', 'value': 'ecosystem'},
                            {'label': 'By Repository', 'value': 'repo'}
                        ],
                        value='ecosystem',
                        inline=True,
                        style={'display': 'inline-block', 'marginLeft': '15px', 'fontSize': '12px', 'color': 'var(--text-muted)'}
                    ),
                    html.Button("↗ Expand", id="btn-expand-streamgraph", style=btn_style)
                ]),
                html.P("Monthly human activity volume by ecosystem", style=p_style),
                dcc.Graph(id='streamgraph', style=graph_style, config={'displayModeBar': False})
            ], style=panel_style_left),

            # Panel 2 — Contributor Network
            html.Div([
                html.Div([
                    html.H4("Contributor Network", style=header_style),
                    dcc.Dropdown(
                        id='network-repo-filter',
                        options=[{'label': r, 'value': r} for r in REPOS],
                        value='facebook/react',
                        clearable=False,
                        style={'display': 'inline-block', 'marginLeft': '10px', 'fontSize': '11px', 'minWidth': '140px', 'verticalAlign': 'middle', 'color': 'var(--text-primary)'}
                    ),
                    html.Button("↗ Expand", id="btn-expand-network", style=btn_style)
                ]),
                html.Div(id='network-bus-factor-info', style={'fontSize': '11px', 'color': 'var(--text-muted)', 'marginBottom': '2px', 'marginTop': '4px'}),
                html.Div(id='network-hover-info', style={'minHeight': '15px', 'fontSize': '11px', 'color': 'var(--text-primary)', 'fontWeight': 'bold', 'marginBottom': '4px'}),
                cyto.Cytoscape(
                    id='contributor-network',
                    layout={'name': 'cose'},
                    style={'width': '100%', 'height': '220px'},
                    stylesheet=[
                        {'selector': 'node', 'style': {'font-size': '7px', 'width': '12px', 'height': '12px', 'background-color': '#4C78A8', 'color': '#333'}},
                        {'selector': '.top-contributor', 'style': {'label': 'data(label)', 'background-color': '#ef4444', 'width': '18px', 'height': '18px', 'font-size': '8px', 'font-weight': 'bold'}},
                        {'selector': 'edge', 'style': {'width': 'mapData(weight, 1, 30, 0.5, 4)', 'line-color': '#cccccc', 'opacity': 0.6}}
                    ]
                )
            ], style=panel_style_mid),

            # Panel 3 — PR Sankey
            html.Div([
                html.Div([
                    html.H4("PR Lifecycle & Latency", style=header_style),
                    dcc.Dropdown(
                        id='sankey-repo-filter',
                        options=[{'label': 'All Selected', 'value': 'ALL'}] + [{'label': r, 'value': r} for r in REPOS],
                        value='ALL',
                        clearable=False,
                        style={'display': 'inline-block', 'marginLeft': '10px', 'fontSize': '11px', 'minWidth': '140px', 'verticalAlign': 'middle', 'color': 'var(--text-primary)'}
                    ),
                    html.Button("↗ Expand", id="btn-expand-sankey", style=btn_style)
                ]),
                dcc.Graph(id='pr-sankey', style=graph_style, config={'displayModeBar': False}),
                html.Div([
                    html.Div([html.Span(style={'display': 'inline-block', 'width': '8px', 'height': '8px', 'backgroundColor': '#94a3b8', 'marginRight': '4px'}), html.Span("Opened PRs", style={'fontSize': '10px', 'marginRight': '10px', 'color': 'gray'})], style={'display': 'inline-block'}),
                    html.Div([html.Span(style={'display': 'inline-block', 'width': '8px', 'height': '8px', 'backgroundColor': '#3b82f6', 'marginRight': '4px'}), html.Span("Reviewed", style={'fontSize': '10px', 'marginRight': '10px', 'color': 'gray'})], style={'display': 'inline-block'}),
                    html.Div([html.Span(style={'display': 'inline-block', 'width': '8px', 'height': '8px', 'backgroundColor': '#f59e0b', 'marginRight': '4px'}), html.Span("Unreviewed", style={'fontSize': '10px', 'marginRight': '10px', 'color': 'gray'})], style={'display': 'inline-block'}),
                    html.Div([html.Span(style={'display': 'inline-block', 'width': '8px', 'height': '8px', 'backgroundColor': '#10b981', 'marginRight': '4px'}), html.Span("Merged", style={'fontSize': '10px', 'marginRight': '10px', 'color': 'gray'})], style={'display': 'inline-block'}),
                    html.Div([html.Span(style={'display': 'inline-block', 'width': '8px', 'height': '8px', 'backgroundColor': '#ef4444', 'marginRight': '4px'}), html.Span("Closed w/o Merge", style={'fontSize': '10px', 'marginRight': '10px', 'color': 'gray'})], style={'display': 'inline-block'}),
                    html.Div([html.Span(style={'display': 'inline-block', 'width': '8px', 'height': '8px', 'backgroundColor': '#64748b', 'marginRight': '4px'}), html.Span("Still Open", style={'fontSize': '10px', 'marginRight': '10px', 'color': 'gray'})], style={'display': 'inline-block'}),
                ], style={'textAlign': 'center', 'marginTop': '5px', 'marginBottom': '10px', 'lineHeight': '1.5', 'position': 'relative', 'zIndex': '10'}),
                html.P("Flow of PRs and review latency distribution", style=p_style_bottom)
            ], style=panel_style_right),

        ], style={'display': 'flex', 'flexWrap': 'wrap', 'marginLeft': '-5px', 'marginRight': '-5px', 'marginBottom': '10px'}),

        # ── Row 2 ──
        html.Div([
            # Panel 4 — Issue Heatmap
            html.Div([
                html.Div([
                    html.H4("Issue Responsiveness", style=header_style),
                    html.Button("↗ Expand", id="btn-expand-heatmap", style=btn_style)
                ]),
                html.P("Daily issue creation frequency", style=p_style),
                html.Div(
                    dcc.Graph(id='issue-heatmap', config={'displayModeBar': False}),
                    style={'height': '220px', 'overflowY': 'auto', 'overflowX': 'hidden'}
                )
            ], style=panel_style_left),

            # Panel 5 — Bot Bar Chart
            html.Div([
                html.Div([
                    html.H4("Bot vs Human Activity", style=header_style),
                    html.Button("↗ Expand", id="btn-expand-botbar", style=btn_style)
                ]),
                html.P("Proportion of automated activity", style=p_style),
                dcc.Graph(id='bot-bar', style=graph_style, config={'displayModeBar': False})
            ], style=panel_style_mid),

            # Panel 6 — Health Dashboard
            html.Div([
                html.Div([
                    html.H4("Health Dashboard", style=header_style),
                    html.Button("↗ Expand", id="btn-expand-dashboard", style=btn_style)
                ]),
                dcc.Graph(id='health-dashboard', style=graph_style, config={'displayModeBar': False}),
                html.P("Key metrics compared side by side", style=p_style_bottom)
            ], style=panel_style_right)
        ], style={'display': 'flex', 'flexWrap': 'wrap', 'marginLeft': '-5px', 'marginRight': '-5px'}),
        
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
                            html.H3("Detailed View", id="modal-title", style={"marginTop": "0"})
                        ]),
                        html.Div(id="modal-content", style={"flexGrow": "1", "marginTop": "15px", "position": "relative", "overflowY": "auto"})
                    ]
                )
            ]
        )

    ], style={'padding': '5px'})
    return panels
