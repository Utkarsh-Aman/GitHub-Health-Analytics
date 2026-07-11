from dash import Input, Output
import plotly.graph_objects as go
import pandas as pd
from src.data_loader import load_pr_latency, load_issue_response, load_bot_activity, load_bus_factor
from src.analytics import compute_health_summary, apply_millers_law
from app.components.filters import get_month_range

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
        
        if len(selected_repos) > 7:
            effective_repos = selected_repos[:7] + ['Other (aggregate)']
        else:
            effective_repos = selected_repos
            
        pr_df = apply_millers_law(load_pr_latency(selected_repos, start_month=start_month, end_month=end_month), selected_repos)
        issue_df = apply_millers_law(load_issue_response(selected_repos, start_month=start_month, end_month=end_month), selected_repos)
        bot_df = apply_millers_law(load_bot_activity(selected_repos, start_month=start_month, end_month=end_month), selected_repos)
        bf_df = apply_millers_law(load_bus_factor(selected_repos), selected_repos)
        
        summary = compute_health_summary(effective_repos, pr_df, issue_df, bot_df, bf_df)
        
        if summary.empty:
            return go.Figure(layout=dict(title="No data found for the selected repositories"))

        import plotly.express as px
        
        # Ensure numeric types
        for col in ['median_merge_hours', 'median_response_hours', 'bus_factor', 'bot_percentage']:
            summary[col] = pd.to_numeric(summary[col], errors='coerce').fillna(0)
        
        # Max values for normalization
        max_merge = summary['median_merge_hours'].max() or 1
        max_resp = summary['median_response_hours'].max() or 1
        max_bus = summary['bus_factor'].max() or 1
        max_bot = summary['bot_percentage'].max() or 1
        
        fig = go.Figure()
        colors = px.colors.qualitative.Plotly
        
        for i, row in summary.iterrows():
            repo = row['repo']
            # Normalize to 0-100 scale for plotting shape
            norm_r = [
                (row['median_merge_hours'] / max_merge) * 100,
                (row['median_response_hours'] / max_resp) * 100,
                (row['bus_factor'] / max_bus) * 100,
                (row['bot_percentage'] / max_bot) * 100
            ]
            
            # Hover text with real values
            hover_text = [
                f"Merge Latency: {row['median_merge_hours']:.1f} hrs",
                f"Issue Response: {row['median_response_hours']:.1f} hrs",
                f"Bus Factor: {row['bus_factor']}",
                f"Bot Activity: {row['bot_percentage']:.1f}%"
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

        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=False, range=[0, 100]),
            ),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5, font=dict(size=10)),
            margin=dict(t=25, b=20, l=25, r=25),
            template='plotly_white'
        )
        return fig
