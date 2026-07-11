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

        col_values = [
            list(summary['repo']),
            [_fmt(v) for v in summary['median_merge_hours']],
            [_fmt(v) for v in summary['median_response_hours']],
            [_fmt(v) for v in summary['bus_factor']],
            [_fmt(v, '%') for v in summary['bot_percentage']],
        ]

        n_rows = len(summary)
        row_colors = ['#f9fafb' if i % 2 == 0 else '#ffffff' for i in range(n_rows)]

        fig = go.Figure(data=[go.Table(
            header=dict(
                values=['Repository', 'Median Merge Time (hrs)', 'Median Issue Response (hrs)', 'Bus Factor', 'Bot Activity %'],
                fill_color='#1f2937', font=dict(color='white', size=12), align='left'
            ),
            cells=dict(values=col_values, fill_color=[row_colors] * len(col_values), align='left')
        )])
        fig.update_layout(template='plotly_white', margin=dict(t=25, b=20, l=10, r=10))
        return fig
