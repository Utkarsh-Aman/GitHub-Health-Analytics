from dash import Input, Output
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from src.data_loader import load_pr_latency, load_issue_response, load_bot_activity, load_bus_factor
from src.analytics import compute_health_summary, apply_millers_law
from app.components.filters import get_month_range
from app.globals import REPOS

# --- Precompute global bounds at startup to ensure consistent normalization scaling ---
try:
    _full_pr = load_pr_latency(REPOS)
    _full_iss = load_issue_response(REPOS)
    _full_bot = load_bot_activity(REPOS)
    _full_bf = load_bus_factor(REPOS)
    
    _global_sum = compute_health_summary(REPOS, _full_pr, _full_iss, _full_bot, _full_bf)
    
    _log_merge = np.log1p(pd.to_numeric(_global_sum['median_merge_hours'], errors='coerce').fillna(0))
    _log_resp = np.log1p(pd.to_numeric(_global_sum['median_response_hours'], errors='coerce').fillna(0))
    _bf = np.log1p(pd.to_numeric(_global_sum['bus_factor'], errors='coerce').fillna(0))
    _bot = pd.to_numeric(_global_sum['bot_percentage'], errors='coerce').fillna(0)
    
    G_MAX_MERGE = _log_merge.max()
    G_MIN_MERGE = _log_merge.min()
    
    G_MAX_RESP = _log_resp.max()
    G_MIN_RESP = _log_resp.min()
    
    G_MAX_BUS = _bf.max()
    G_MIN_BUS = _bf.min()
    
    G_MAX_BOT = _bot.max()
    G_MIN_BOT = _bot.min()
except Exception as e:
    # Fallback bounds just in case data loading fails at startup
    G_MAX_MERGE, G_MIN_MERGE = 10.0, 0.0
    G_MAX_RESP, G_MIN_RESP = 10.0, 0.0
    G_MAX_BUS, G_MIN_BUS = 100.0, 0.0
    G_MAX_BOT, G_MIN_BOT = 100.0, 0.0
# ----------------------------------------------------------------------------------

def _fmt(val, suffix=''):
    return 'N/A' if pd.isna(val) else f"{val}{suffix}"

def register(app):
    @app.callback(
        Output('health-dashboard', 'figure'),
        [Input('repo-filter', 'value'),
         Input('month-slider', 'value'),
         Input('bot-toggle', 'value')]
    )
    def update_health_dashboard(selected_repos, month_range, include_bots):
        if not selected_repos:
            return go.Figure(layout=dict(title="Select at least one repository to view its health summary"))

        start_month, end_month = get_month_range(month_range)
        include_bots_bool = bool(include_bots)
        
        if len(selected_repos) > 7:
            effective_repos = selected_repos[:7] + ['Other (aggregate)']
        else:
            effective_repos = selected_repos
            
        pr_df = apply_millers_law(load_pr_latency(selected_repos, start_month=start_month, end_month=end_month, include_bots=include_bots_bool), selected_repos)
        issue_df = apply_millers_law(load_issue_response(selected_repos, start_month=start_month, end_month=end_month, include_bots=include_bots_bool), selected_repos)
        bot_df = apply_millers_law(load_bot_activity(selected_repos, start_month=start_month, end_month=end_month), selected_repos)
        bf_df = apply_millers_law(load_bus_factor(selected_repos), selected_repos)
        
        summary = compute_health_summary(effective_repos, pr_df, issue_df, bot_df, bf_df)
        
        if summary.empty:
            return go.Figure(layout=dict(title="No data found for the selected repositories"))

        import plotly.express as px
        
        # Ensure numeric types
        for col in ['median_merge_hours', 'median_response_hours', 'bus_factor', 'bot_percentage']:
            summary[col] = pd.to_numeric(summary[col], errors='coerce')
        
        # Remove dynamic min/max calculations as we now use globals
        
        fig = go.Figure()
        colors = px.colors.qualitative.Plotly
        
        for i, row in summary.iterrows():
            repo = row['repo']
            
            if pd.isna(row['median_merge_hours']):
                norm_merge = 0
                hover_merge = "Merge Latency: N/A (no PRs)"
            else:
                log_merge = np.log1p(row['median_merge_hours'])
                merge_range = max(G_MAX_MERGE - G_MIN_MERGE, 0.001)
                norm_merge = 100 * (1 - (log_merge - G_MIN_MERGE) / merge_range)
                hover_merge = f"Merge Latency: {row['median_merge_hours']:.2f} hrs"
                
            if pd.isna(row['median_response_hours']):
                norm_resp = 0
                hover_resp = "Issue Response: N/A (no issues)"
            else:
                log_resp = np.log1p(row['median_response_hours'])
                resp_range = max(G_MAX_RESP - G_MIN_RESP, 0.001)
                norm_resp = 100 * (1 - (log_resp - G_MIN_RESP) / resp_range)
                hover_resp = f"Issue Response: {row['median_response_hours']:.2f} hrs"
                
            if pd.isna(row['bot_percentage']):
                norm_bot = 0
                hover_bot = "Bot Activity: N/A"
            else:
                bot_range = max(G_MAX_BOT - G_MIN_BOT, 0.001)
                norm_bot = 100 * (1 - (row['bot_percentage'] - G_MIN_BOT) / bot_range)
                hover_bot = f"Bot Activity: {row['bot_percentage']:.1f}%"
                
            if pd.isna(row['bus_factor']):
                norm_bus = 0
                hover_bus = "Bus Factor: N/A"
            else:
                bus = np.log1p(row['bus_factor'])
                bus_range = max(G_MAX_BUS - G_MIN_BUS, 0.001)
                norm_bus = 100 * (bus - G_MIN_BUS) / bus_range
                hover_bus = f"Bus Factor: {row['bus_factor']}"
            
            # Clip between 0-100 just in case time-filtered selections go slightly outside global all-time bounds
            norm_r = [
                max(0, min(100, norm_merge)),
                max(0, min(100, norm_resp)),
                max(0, min(100, norm_bus)),
                max(0, min(100, norm_bot))
            ]
            
            # Hover text with real values
            hover_text = [
                hover_merge,
                hover_resp,
                hover_bus,
                hover_bot
            ]
            
            fig.add_trace(go.Scatterpolar(
                r=norm_r,
                theta=['Merge Time', 'Response Time', 'Bus Factor', 'Bot %'],
                fill='toself',
                name=repo,
                hoverinfo="name+text",
                hovertext=hover_text,
                line=dict(color=colors[i % len(colors)])
            ))

        template = 'plotly_white'
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 100], ticksuffix='%', angle=45)
            ),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5, font=dict(size=10)),
            margin=dict(t=25, b=20, l=25, r=25),
            template=template
        )
        return fig
