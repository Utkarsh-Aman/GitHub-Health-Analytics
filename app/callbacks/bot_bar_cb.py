import pandas as pd
from dash import Input, Output
import plotly.graph_objects as go
from src.data_loader import load_bot_activity

# Generate the 24 months locally to bypass the globals.py database issue
ALL_MONTHS = [f"{y}-{m:02d}" for y in [2023, 2024] for m in range(1, 13)]

def register(app):
    @app.callback(
        Output('bot-bar', 'figure'),
        [Input('repo-filter', 'value'),
         Input('month-slider', 'value')]
    )
    def update_bot_bar(selected_repos, month_range):
        # 1. Resolve start and end months from slider range indices
        if month_range and len(month_range) == 2:
            start_month = ALL_MONTHS[month_range[0]]
            end_month = ALL_MONTHS[month_range[1]]
        else:
            start_month = '2023-01'
            end_month = '2024-12'
        
        # Load activity data (filters by repos internally)
        df = load_bot_activity(selected_repos)
        
        if df.empty:
            return go.Figure(layout=dict(title="No activity data found matching filters"))
            
        # 2. Filter by month range in memory
        df = df[(df['year_month'] >= start_month) & (df['year_month'] <= end_month)]
        
        if df.empty:
            return go.Figure(layout=dict(title="No activity data found in selected month range"))
            
        # 3. Pivot the dataset to aggregate counts for bot vs human
        grouped = df.groupby(['repo', 'is_bot'])['event_count'].sum().reset_index()
        pivot_df = grouped.pivot(index='repo', columns='is_bot', values='event_count').fillna(0)
        
        # Robust lookup to match boolean keys (True/False, 1/0, or "True"/"False" strings)
        human_col = None
        bot_col = None
        for col in pivot_df.columns:
            col_str = str(col).lower()
            if col_str in ['false', '0', '0.0']:
                human_col = col
            elif col_str in ['true', '1', '1.0']:
                bot_col = col
        
        human_events = pivot_df[human_col] if human_col is not None else pd.Series(0, index=pivot_df.index)
        bot_events = pivot_df[bot_col] if bot_col is not None else pd.Series(0, index=pivot_df.index)
        
        # 4. Generate Plotly stacked bar trace
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=pivot_df.index,
            y=human_events,
            name='Human Activity',
            marker_color='#1f77b4'
        ))
        fig.add_trace(go.Bar(
            x=pivot_df.index,
            y=bot_events,
            name='Bot Activity',
            marker_color='#d62728'
        ))
        
        fig.update_layout(
            barmode='stack',
            title='Bot vs. Human Activity Volume',
            xaxis_title='Repository',
            yaxis_title='Total Event Count',
            template='plotly_white',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        return fig
