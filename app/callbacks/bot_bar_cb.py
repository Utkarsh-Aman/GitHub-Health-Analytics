from dash import Input, Output
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from src.data_loader import load_bot_activity
from src.analytics import apply_millers_law
from app.components.filters import get_month_range

def register(app):
    @app.callback(
        Output('bot-bar', 'figure'),
        [Input('repo-filter', 'value'),
         Input('ecosystem-filter', 'value'),
         Input('month-slider', 'value'),
         Input('bot-toggle', 'value')]
    )
    def update_bot_bar(selected_repos, selected_ecosystem, month_range, include_bots):
        start_month, end_month = get_month_range(month_range)
        
        # If no repos selected, group by ecosystem to allow comparing across ecosystems
        group_by_eco = not selected_repos
        
        df = load_bot_activity(selected_repos, ecosystem=selected_ecosystem, start_month=start_month, end_month=end_month)
        if df.empty:
            return go.Figure(layout=dict(title="No data found matching filters"))
            
        if group_by_eco:
            group_col = 'ecosystem'
        else:
            df = apply_millers_law(df, selected_repos)
            group_col = 'repo'
            
        grouped = df.groupby([group_col, 'is_bot'])['event_count'].sum().reset_index()
        pivot_df = grouped.pivot(index=group_col, columns='is_bot', values='event_count').fillna(0)
        
        human_col = bot_col = None
        for col in pivot_df.columns:
            if str(col) in ['0', 'False', '0.0', 'false']: human_col = col
            elif str(col) in ['1', 'True', '1.0', 'true']: bot_col = col
            
        human_events = pivot_df[human_col] if human_col is not None else pd.Series(0, index=pivot_df.index)
        bot_events = pivot_df[bot_col] if bot_col is not None else pd.Series(0, index=pivot_df.index)
        
        total = human_events + bot_events
        total = total.replace(0, 1) # Prevent division by zero
        
        human_pct = (human_events / total) * 100
        bot_pct = (bot_events / total) * 100
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=pivot_df.index, 
            y=human_pct, 
            name='Human Activity', 
            marker_color='#1f77b4',
            customdata=human_events,
            hovertemplate='%{y:.1f}%<br>Count: %{customdata:,}<extra></extra>'
        ))
        fig.add_trace(go.Bar(
            x=pivot_df.index, 
            y=bot_pct, 
            name='Bot Activity', 
            marker_color='#d62728',
            customdata=bot_events,
            hovertemplate='%{y:.1f}%<br>Count: %{customdata:,}<extra></extra>'
        ))
        
        template = 'plotly_white'
        
        fig.update_layout(
            margin=dict(t=40, b=20, l=10, r=10), 
            barmode='stack', 
            template=template, 
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            yaxis=dict(title='Percentage (%)', range=[0, 100], ticksuffix='%')
        )
        return fig
