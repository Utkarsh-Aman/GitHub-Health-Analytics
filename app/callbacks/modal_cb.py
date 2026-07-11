from dash import Input, Output, State, callback_context, html, dcc
import dash_cytoscape as cyto

def register(app):
    @app.callback(
        Output("detail-modal", "style"),
        Output("modal-content", "children"),
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
        ]
    )
    def toggle_modal(btn_sg, btn_net, btn_sankey, btn_hm, btn_bot, btn_dash, btn_close,
                     fig_sg, ele_net, fig_sankey, fig_hm, fig_bot, fig_dash):
        
        ctx = callback_context
        if not ctx.triggered:
            return {"display": "none"}, None
            
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
            return modal_hidden_style, None
            
        if button_id == "btn-expand-streamgraph" and fig_sg:
            return modal_visible_style, dcc.Graph(figure=fig_sg, style={"height": "100%", "width": "100%"})
            
        if button_id == "btn-expand-network" and ele_net:
            # Reconstruct classes since Dash Cytoscape State serialization drops them
            max_cent = max([n.get('data', {}).get('centrality', 0) for n in ele_net if 'source' not in n.get('data', {})] + [0])
            threshold = max_cent * 0.5
            for n in ele_net:
                if 'source' not in n.get('data', {}):
                    if max_cent > 0 and n.get('data', {}).get('centrality', 0) >= threshold:
                        n['classes'] = 'top-contributor'
                        
            return modal_visible_style, cyto.Cytoscape(
                layout={'name': 'cose'},
                style={'width': '100%', 'height': '100%'},
                elements=ele_net,
                stylesheet=[
                    {'selector': 'node', 'style': {'font-size': '10px', 'width': '16px', 'height': '16px', 'background-color': '#4C78A8', 'color': '#333'}},
                    {'selector': '.top-contributor', 'style': {'label': 'data(label)', 'background-color': '#ef4444', 'width': '28px', 'height': '28px', 'font-size': '12px', 'font-weight': 'bold'}},
                    {'selector': 'edge', 'style': {'width': 'mapData(weight, 1, 30, 1, 6)', 'line-color': '#cccccc', 'opacity': 0.6}}
                ]
            )
            
        if button_id == "btn-expand-sankey" and fig_sankey:
            return modal_visible_style, dcc.Graph(figure=fig_sankey, style={"height": "100%", "width": "100%"})
            
        if button_id == "btn-expand-heatmap" and fig_hm:
            return modal_visible_style, dcc.Graph(figure=fig_hm, style={"height": "100%", "width": "100%"})
            
        if button_id == "btn-expand-botbar" and fig_bot:
            return modal_visible_style, dcc.Graph(figure=fig_bot, style={"height": "100%", "width": "100%"})
            
        if button_id == "btn-expand-dashboard" and fig_dash:
            return modal_visible_style, dcc.Graph(figure=fig_dash, style={"height": "100%", "width": "100%"})
            
        return modal_hidden_style, None
