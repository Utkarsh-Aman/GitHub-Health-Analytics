from dash import Input, Output
import plotly.graph_objects as go
import plotly.express as px
from src.data_loader import load_events
from src.analytics import compute_ecosystem_monthly, compute_monthly_activity, apply_millers_law
from app.components.filters import get_month_range

ECOSYSTEM_COLORS = {"Frontend": "#4C78A8", "ML/Data": "#F58518", "Backend/DevOps": "#54A24B"}

def _empty_figure(message: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=message, xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, font=dict(size=14, color="gray"))
    fig.update_layout(xaxis=dict(visible=False), yaxis=dict(visible=False), template="plotly_white")
    return fig

def register(app):
    @app.callback(
        Output("streamgraph", "figure"),
        [Input("repo-filter", "value"), 
         Input("ecosystem-filter", "value"), 
         Input("month-slider", "value"), 
         Input("bot-toggle", "value"),
         Input("streamgraph-group-by", "value")]
    )
    def update_streamgraph(selected_repos, selected_ecosystem, month_range, include_bots, group_by):
        start_month, end_month = get_month_range(month_range)
        include_bots_bool = bool(include_bots)
        
        df = load_events(repos=selected_repos, ecosystem=selected_ecosystem, start_month=start_month, end_month=end_month, include_bots=include_bots_bool)
        if df.empty:
            return _empty_figure("No activity data for the current filters.")
            
        group_col = 'ecosystem' if group_by == 'ecosystem' else 'repo'
        
        if group_by == 'ecosystem':
            monthly = compute_ecosystem_monthly(df)
        else:
            df = apply_millers_law(df, selected_repos)
            monthly = compute_monthly_activity(df)
            if 'Other (aggregate)' in monthly['repo'].values:
                num_other = len(selected_repos) - 7
                if num_other > 0:
                    monthly.loc[monthly['repo'] == 'Other (aggregate)', 'event_count'] //= num_other
                    monthly.loc[monthly['repo'] == 'Other (aggregate)', 'repo'] = 'Other (average)'
                    
        if monthly.empty:
            return _empty_figure("No data after aggregation.")
            
        pivot = monthly.pivot(index='year_month', columns=group_col, values='event_count').fillna(0)
        
        if group_by == 'ecosystem':
            columns_order = [eco for eco in ECOSYSTEM_COLORS if eco in pivot.columns]
            columns_order += [eco for eco in pivot.columns if eco not in columns_order]
        else:
            columns_order = list(pivot.columns)
            if 'Other (average)' in columns_order:
                columns_order.remove('Other (average)')
                columns_order.append('Other (average)')
        
        totals = pivot[columns_order].sum(axis=1)
        baseline = -totals / 2.0
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=pivot.index, y=baseline, mode="lines", line=dict(width=0), hoverinfo="skip", showlegend=False))
        
        running = baseline.copy()
        palette = px.colors.qualitative.Plotly if group_by == 'repo' else px.colors.qualitative.Set2
        
        for i, col_name in enumerate(columns_order):
            running = running + pivot[col_name]
            if group_by == 'ecosystem':
                color = ECOSYSTEM_COLORS.get(col_name, palette[i % len(palette)])
            else:
                color = 'lightgray' if col_name == 'Other (average)' else palette[i % len(palette)]
                
            fig.add_trace(go.Scatter(
                x=pivot.index, y=running, mode="lines", name=col_name, line=dict(width=0.5, color=color),
                fill="tonexty", fillcolor=color, opacity=0.85,
                hovertemplate=f"<b>{col_name}</b><br>%{{x}}<br>Events: " + pivot[col_name].astype(str) + "<extra></extra>"
            ))
            
        template = "plotly_white"
        fig.update_layout(
            xaxis=dict(title=None), yaxis=dict(showticklabels=False, title=None), template=template,
            hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), margin=dict(t=25, b=20, l=10, r=10)
        )
        return fig
