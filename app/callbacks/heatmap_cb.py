from dash import Input, Output
import plotly.graph_objects as go
import pandas as pd
from src.data_loader import load_events
from src.analytics import compute_daily_issue_activity
from app.components.filters import get_month_range

def register(app):
    @app.callback(
        Output('issue-heatmap', 'figure'),
        [Input('repo-filter', 'value'),
         Input('month-slider', 'value'),
         Input('bot-toggle', 'value')]
    )
    def update_issue_heatmap(selected_repos, month_range, include_bots):
        start_month, end_month = get_month_range(month_range)
        
        df = load_events(repos=selected_repos, start_month=start_month, end_month=end_month, include_bots=bool(include_bots))
        if df.empty:
            return go.Figure(layout=dict(title="No data found matching filters"))
            
        daily_counts = compute_daily_issue_activity(df)
        if daily_counts.empty:
            return go.Figure(layout=dict(title="No issue activity found in selected month range"))

        # Make sure we have all days
        start_date = pd.to_datetime(start_month + '-01')
        end_date = pd.to_datetime(end_month + '-01') + pd.offsets.MonthEnd(0)
        all_days = pd.date_range(start=start_date, end=end_date, freq='D')
        
        daily_counts = daily_counts.set_index('date').reindex(all_days).fillna(0).reset_index()
        daily_counts.rename(columns={'index': 'date'}, inplace=True)
        
        daily_counts['day_of_week'] = daily_counts['date'].dt.dayofweek
        days_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        
        start_monday = start_date - pd.to_timedelta(start_date.dayofweek, unit='D')
        daily_counts['week_index'] = (daily_counts['date'] - start_monday).dt.days // 7
        
        monthly_ticks = daily_counts.groupby(daily_counts['date'].dt.to_period('M')).first().reset_index(drop=True)
        
        pivot_df = daily_counts.pivot(index='day_of_week', columns='week_index', values='count').fillna(0)
        pivot_df = pivot_df.reindex(range(7), fill_value=0)
        
        daily_counts['date_str'] = daily_counts['date'].dt.strftime('%Y-%m-%d')
        customdata_dates = daily_counts.pivot(index='day_of_week', columns='week_index', values='date_str').reindex(range(7)).values
        
        fig = go.Figure(data=go.Heatmap(
            z=pivot_df.values, x=pivot_df.columns, y=days_names, colorscale='Viridis', xgap=2, ygap=2,
            hovertemplate='Date: %{customdata}<br>Issues Opened: %{z}<extra></extra>', customdata=customdata_dates
        ))
        
        fig.update_layout(margin=dict(t=25, b=20, l=10, r=10), 
            xaxis=dict(tickmode='array', tickvals=monthly_ticks['week_index'], ticktext=monthly_ticks['date'].dt.strftime('%b %Y'), showgrid=False),
            yaxis=dict(autorange='reversed', showgrid=False),
            template='plotly_white'
        )
        return fig
