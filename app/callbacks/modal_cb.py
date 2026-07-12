from dash import Input, Output, State, callback_context, html, dcc
import dash_cytoscape as cyto

def register(app):
    @app.callback(
        Output("detail-modal", "style"),
        Output("modal-content", "children"),
        Output("modal-title", "children"),
        [
            Input("btn-expand-streamgraph", "n_clicks"),
            Input("btn-expand-network", "n_clicks"),
            Input("btn-expand-sankey", "n_clicks"),
            Input("btn-expand-heatmap", "n_clicks"),
            Input("btn-expand-botbar", "n_clicks"),
            Input("btn-expand-dashboard", "n_clicks"),
            Input("btn-close-modal", "n_clicks"),
        ],
        [
            State("streamgraph", "figure"),
            State("contributor-network", "elements"),
            State("pr-sankey", "figure"),
            State("issue-heatmap", "figure"),
            State("bot-bar", "figure"),
            State("health-dashboard", "figure"),
            State("sankey-repo-filter", "value"),
            State("network-repo-filter", "value"),
        ]
    )
    def toggle_modal(btn_sg, btn_net, btn_sankey, btn_hm, btn_bot, btn_dash, btn_close,
                     fig_sg, ele_net, fig_sankey, fig_hm, fig_bot, fig_dash,
                     sankey_repo, network_repo):
        
        ctx = callback_context
        if not ctx.triggered:
            return {"display": "none"}, None, "Detailed View"
            
        button_id = ctx.triggered[0]["prop_id"].split(".")[0]
        
        # Base style for the modal wrapper to show it
        modal_visible_style = {
            "display": "flex",
            "position": "fixed", "zIndex": "1000",
            "left": "0", "top": "0", "width": "100%", "height": "100%",
            "backgroundColor": "rgba(0,0,0,0.6)",
            "justifyContent": "center", "alignItems": "center"
        }
        modal_hidden_style = {"display": "none"}
        
        if button_id == "btn-close-modal":
            return modal_hidden_style, None, "Detailed View"
            
        if button_id == "btn-expand-streamgraph" and fig_sg:
            return modal_visible_style, dcc.Graph(figure=fig_sg, style={"height": "100%", "width": "100%"}), "Adoption Trends"
            
        if button_id == "btn-expand-network" and ele_net:
            # Reconstruct classes since Dash Cytoscape State serialization drops them
            max_cent = max([n.get('data', {}).get('centrality', 0) for n in ele_net if 'source' not in n.get('data', {})] + [0])
            threshold = max_cent * 0.5
            for n in ele_net:
                if 'source' not in n.get('data', {}):
                    if max_cent > 0 and n.get('data', {}).get('centrality', 0) >= threshold:
                        n['classes'] = 'top-contributor'
                        
            return modal_visible_style, html.Div([
                cyto.Cytoscape(
                    id='modal-contributor-network',
                    layout={'name': 'cose'},
                    style={'width': '100%', 'height': '95%'},
                    elements=ele_net,
                    stylesheet=[
                        {'selector': 'node', 'style': {'font-size': '10px', 'width': '16px', 'height': '16px', 'background-color': '#4C78A8', 'color': '#333'}},
                        {'selector': '.top-contributor', 'style': {'label': 'data(label)', 'background-color': '#ef4444', 'width': '28px', 'height': '28px', 'font-size': '12px', 'font-weight': 'bold'}},
                        {'selector': 'edge', 'style': {'width': 'mapData(weight, 1, 30, 1, 6)', 'line-color': '#cccccc', 'opacity': 0.6}}
                    ]
                ),
                html.Div(id="modal-hover-info", style={'minHeight': '20px', 'fontSize': '14px', 'color': 'var(--text-primary)', 'fontWeight': 'bold', 'marginTop': '10px', 'textAlign': 'center'})
            ], style={'width': '100%', 'height': '100%', 'display': 'flex', 'flexDirection': 'column'}), f"Contributor Network - {network_repo}" if network_repo else "Contributor Network"
            
        if button_id == "btn-expand-sankey" and fig_sankey:
            sankey_title = "PR Lifecycle & Latency - All Selected Repos" if sankey_repo == 'ALL' else f"PR Lifecycle & Latency - {sankey_repo}"
            return modal_visible_style, dcc.Graph(figure=fig_sankey, style={"height": "100%", "width": "100%"}), sankey_title
            
        if button_id == "btn-expand-heatmap" and fig_hm:
            return modal_visible_style, dcc.Graph(figure=fig_hm, style={"height": "100%", "width": "100%"}), "Issue Responsiveness"
            
        if button_id == "btn-expand-botbar" and fig_bot:
            return modal_visible_style, dcc.Graph(figure=fig_bot, style={"height": "100%", "width": "100%"}), "Bot vs Human Activity"
            
        if button_id == "btn-expand-dashboard" and fig_dash:
            return modal_visible_style, dcc.Graph(figure=fig_dash, style={"height": "100%", "width": "100%"}), "Health Dashboard Overview"
            
        return modal_hidden_style, None, "Detailed View"

