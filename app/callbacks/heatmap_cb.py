import pandas as pd
from dash import Input, Output
import plotly.graph_objects as go
from src.data_loader import load_issue_response

# Generate the 24 months locally to bypass the globals.py database issue
ALL_MONTHS = [f"{y}-{m:02d}" for y in [2023, 2024] for m in range(1, 13)]

def register(app):
    @app.callback(
        Output('issue-heatmap', 'figure'),
        [Input('repo-filter', 'value'),
         Input('month-slider', 'value')]
    )
    def update_issue_heatmap(selected_repos, month_range):
        # 1. Resolve date range from the slider indices
        if month_range and len(month_range) == 2:
            start_month = ALL_MONTHS[month_range[0]]
            end_month = ALL_MONTHS[month_range[1]]
        else:
            start_month = '2023-01'
            end_month = '2024-12'
        
        # Load issue response data (filters by repos internally)
        df = load_issue_response(selected_repos)
        
        if df.empty:
            return go.Figure(layout=dict(title="No issue activity found matching filters"))
            
        # 2. Filter by month range in memory
        df = df[(df['year_month'] >= start_month) & (df['year_month'] <= end_month)]
        
        if df.empty:
            return go.Figure(layout=dict(title="No issue activity found in selected month range"))
            
        # 3. Standardize dates and count daily openings
        df['opened_date'] = pd.to_datetime(df['opened_date'])
        daily_counts = df.groupby('opened_date').size().reset_index(name='count')
        
        # Populate missing calendar dates to display empty grids
        start_date = pd.to_datetime(start_month + '-01')
        end_date = pd.to_datetime(end_month + '-01') + pd.offsets.MonthEnd(0)
        all_days = pd.date_range(start=start_date, end=end_date, freq='D')
        
        daily_counts = daily_counts.set_index('opened_date').reindex(all_days, fill_value=0).reset_index()
        daily_counts.rename(columns={'index': 'date'}, inplace=True)
        
        # 4. Generate calendar coordinates
        daily_counts['day_of_week'] = daily_counts['date'].dt.dayofweek
        days_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        daily_counts['day_name'] = daily_counts['day_of_week'].map(lambda d: days_names[d])
        
        # Calculate sequential week index relative to start Monday
        start_monday = start_date - pd.to_timedelta(start_date.dayofweek, unit='D')
        daily_counts['week_index'] = (daily_counts['date'] - start_monday).dt.days // 7
        
        # Generate month tick label positions
        monthly_ticks = daily_counts.groupby(daily_counts['date'].dt.to_period('M')).first().reset_index()
        
        # Pivot date matrix into a grid
        pivot_df = daily_counts.pivot(index='day_of_week', columns='week_index', values='count').fillna(0)
        pivot_df = pivot_df.reindex(range(7), fill_value=0)
        
        # Pivot dates to align hover details accurately
        customdata_dates = daily_counts.pivot(index='day_of_week', columns='week_index', values='date').dt.strftime('%Y-%m-%d').reindex(range(7)).values
        
        # 5. Build Heatmap
        fig = go.Figure(data=go.Heatmap(
            z=pivot_df.values,
            x=pivot_df.columns,
            y=days_names,
            colorscale='Viridis',
            xgap=2,
            ygap=2,
            hovertemplate='Date: %{customdata}<br>Issues Opened: %{z}<extra></extra>',
            customdata=customdata_dates
        ))
        
        fig.update_layout(
            title='Issue Creation Frequency',
            xaxis=dict(
                tickmode='array',
                tickvals=monthly_ticks['week_index'],
                ticktext=monthly_ticks['date'].astype(str),
                showgrid=False
            ),
            yaxis=dict(
                autorange='reversed',  # Monday at top, Sunday at bottom
                showgrid=False
            ),
            template='plotly_white',
            height=280
        )
        return fig
