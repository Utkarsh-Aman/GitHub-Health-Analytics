import pandas as pd
from dash import Input, Output
import plotly.graph_objects as go
from src.data_loader import (
    load_pr_latency,
    load_issue_response,
    load_bot_activity,
    load_bus_factor,
)


def _get_bot_percentage(bot_df: pd.DataFrame) -> pd.Series:
    """Given bot_activity rows (repo, is_bot, event_count, ...), return
    % of events that are bot-driven per repo. Robust to is_bot being
    stored as bool, int, or string."""
    if bot_df.empty:
        return pd.Series(dtype=float)

    grouped = bot_df.groupby(['repo', 'is_bot'])['event_count'].sum().reset_index()
    pivot = grouped.pivot(index='repo', columns='is_bot', values='event_count').fillna(0)

    human_col = bot_col = None
    for col in pivot.columns:
        col_str = str(col).lower()
        if col_str in ['false', '0', '0.0']:
            human_col = col
        elif col_str in ['true', '1', '1.0']:
            bot_col = col

    human = pivot[human_col] if human_col is not None else pd.Series(0, index=pivot.index)
    bot = pivot[bot_col] if bot_col is not None else pd.Series(0, index=pivot.index)
    total = (human + bot).replace(0, pd.NA)
    pct = (bot / total * 100).fillna(0)
    return pct.round(1)


def _fmt(val, suffix=''):
    return 'N/A' if pd.isna(val) else f"{val}{suffix}"


def register(app):
    @app.callback(
        Output('health-dashboard', 'figure'),
        Input('repo-filter', 'value')
    )
    def update_health_dashboard(selected_repos):
        if not selected_repos:
            return go.Figure(layout=dict(
                title="Select at least one repository to view its health summary"
            ))

        # 1. Load all four feature sets, scoped to the selected repos
        pr_df = load_pr_latency(selected_repos)
        issue_df = load_issue_response(selected_repos)
        bot_df = load_bot_activity(selected_repos)
        bf_df = load_bus_factor(selected_repos)

        if pr_df.empty and issue_df.empty and bot_df.empty and bf_df.empty:
            return go.Figure(layout=dict(
                title="No data found for the selected repositories"
            ))

        # 2. Median PR merge time per repo (hours)
        merge_time = (
            pr_df.groupby('repo')['latency_hours'].median()
            if not pr_df.empty else pd.Series(dtype=float)
        )

        # 3. Median issue response time per repo (hours) — only issues
        #    that actually got a response, if that flag is available
        if not issue_df.empty:
            if 'has_response' in issue_df.columns:
                responded = issue_df[issue_df['has_response'] == True]  # noqa: E712
            else:
                responded = issue_df
            response_time = responded.groupby('repo')['response_hours'].median()
        else:
            response_time = pd.Series(dtype=float)

        # 4. Bus factor — already one row per repo
        bus_factor = (
            bf_df.set_index('repo')['bus_factor'] if not bf_df.empty else pd.Series(dtype=float)
        )

        # 5. Bot activity percentage per repo
        bot_pct = _get_bot_percentage(bot_df)

        # 6. Assemble one row per selected repo, filling gaps with N/A
        summary = pd.DataFrame(index=selected_repos)
        summary['median_merge_hours'] = merge_time.reindex(selected_repos)
        summary['median_response_hours'] = response_time.reindex(selected_repos)
        summary['bus_factor'] = bus_factor.reindex(selected_repos)
        summary['bot_pct'] = bot_pct.reindex(selected_repos)
        summary = summary.round(1)

        col_values = [
            list(summary.index),
            [_fmt(v) for v in summary['median_merge_hours']],
            [_fmt(v) for v in summary['median_response_hours']],
            [_fmt(v) for v in summary['bus_factor']],
            [_fmt(v, '%') for v in summary['bot_pct']],
        ]

        n_rows = len(summary)
        row_colors = ['#f9fafb' if i % 2 == 0 else '#ffffff' for i in range(n_rows)]

        fig = go.Figure(data=[go.Table(
            header=dict(
                values=['Repository', 'Median Merge Time (hrs)',
                        'Median Issue Response (hrs)', 'Bus Factor',
                        'Bot Activity %'],
                fill_color='#1f2937',
                font=dict(color='white', size=12),
                align='left'
            ),
            cells=dict(
                values=col_values,
                fill_color=[row_colors] * len(col_values),
                align='left'
            )
        )])

        fig.update_layout(
            title='Repository Health Summary',
            template='plotly_white',
            margin=dict(t=50, b=20, l=20, r=20)
        )
        return fig