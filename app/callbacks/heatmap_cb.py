from dash import Input, Output
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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
        
        if not selected_repos:
            return go.Figure(layout=dict(title="Select at least one repository to view the issue heatmap"))
            
        # Apply Miller's Law: limit to 7 repos for readability
        if len(selected_repos) > 7:
            effective_repos = selected_repos[:7]
        else:
            effective_repos = selected_repos
        
        df = load_events(repos=effective_repos, start_month=start_month, end_month=end_month, include_bots=bool(include_bots))
        if df.empty:
            return go.Figure(layout=dict(title="No data found matching filters"))
            
        daily_counts = compute_daily_issue_activity(df)
        if daily_counts.empty:
            return go.Figure(layout=dict(title="No issue activity found in selected month range"))

        # Global Z_MAX for shared color scale
        zmax = daily_counts['count'].max()
        if pd.isna(zmax) or zmax == 0:
            zmax = 1

        # Make sure we have all days
        start_date = pd.to_datetime(start_month + '-01')
        end_date = pd.to_datetime(end_month + '-01') + pd.offsets.MonthEnd(0)
        all_days = pd.date_range(start=start_date, end=end_date, freq='D')
        
        days_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        start_monday = start_date - pd.to_timedelta(start_date.dayofweek, unit='D')
        
        subplot_titles = []
        for repo in effective_repos:
            repo_df = daily_counts[daily_counts['repo'] == repo].copy()
            repo_df = repo_df.set_index('date').reindex(all_days).fillna(0).reset_index()
            
            avg = repo_df['count'].mean()
            is_zero = repo_df['count'] == 0
            streak = is_zero.groupby((~is_zero).cumsum()).sum()
            longest_silence = int(streak.max()) if not streak.empty else 0
            
            subtitle = f"{repo}<br><sup style='color: gray'>avg {avg:.1f}/day &middot; longest silence: {longest_silence} days</sup>"
            subplot_titles.append(subtitle)
            
        import plotly.express as px
        viridis_colors = px.colors.sequential.Viridis
        threshold = 0.5 / zmax
        custom_scale = [
            [0.0, '#e2e8f0'],
            [threshold, '#e2e8f0'],
            [threshold, viridis_colors[0]],
        ]
        for i in range(1, len(viridis_colors)):
            custom_scale.append([
                threshold + (1 - threshold) * (i / (len(viridis_colors) - 1)), 
                viridis_colors[i]
            ])
        
        fig = make_subplots(rows=len(effective_repos), cols=1, 
                            shared_xaxes=True, 
                            vertical_spacing=0.08,
                            subplot_titles=subplot_titles)
                            
        # Common layout preparation
        dummy_df = pd.DataFrame({'date': all_days})
        dummy_df['week_index'] = (dummy_df['date'] - start_monday).dt.days // 7
        monthly_ticks = dummy_df.groupby(dummy_df['date'].dt.to_period('M')).first().reset_index(drop=True)

        for i, repo in enumerate(effective_repos):
            repo_df = daily_counts[daily_counts['repo'] == repo].copy()
            repo_df = repo_df.set_index('date').reindex(all_days).fillna(0).reset_index()
            repo_df.rename(columns={'index': 'date'}, inplace=True)
            
            repo_df['day_of_week'] = repo_df['date'].dt.dayofweek
            repo_df['week_index'] = (repo_df['date'] - start_monday).dt.days // 7
            
            pivot_df = repo_df.pivot(index='day_of_week', columns='week_index', values='count').fillna(0)
            pivot_df = pivot_df.reindex(range(7), fill_value=0)
            
            repo_df['date_str'] = repo_df['date'].dt.strftime('%Y-%m-%d')
            customdata_dates = repo_df.pivot(index='day_of_week', columns='week_index', values='date_str').reindex(range(7)).values
            
            fig.add_trace(go.Heatmap(
                z=pivot_df.values, x=pivot_df.columns, y=days_names, colorscale=custom_scale, xgap=2, ygap=2,
                hovertemplate=f'Repo: {repo}<br>Date: %{{customdata}}<br>Issues Opened: %{{z}}<extra></extra>', customdata=customdata_dates,
                zmin=0, zmax=zmax, showscale=(i == 0), colorbar=dict(title="Issues Opened") if i == 0 else None
            ), row=i+1, col=1)
            
            fig.update_yaxes(autorange='reversed', showgrid=False, row=i+1, col=1)

        template = 'plotly_white'
        
        fig.update_layout(
            margin=dict(t=40, b=20, l=10, r=10), 
            height=200 * len(effective_repos) + 50,
            template=template
        )
        
        # Update shared x-axis
        fig.update_xaxes(
            tickmode='array', 
            tickvals=monthly_ticks['week_index'], 
            ticktext=monthly_ticks['date'].dt.strftime('%b %Y'), 
            showgrid=False,
            row=len(effective_repos), col=1
        )

        return fig
