from dash import Input, Output
import plotly.graph_objects as go
import plotly.express as px
from src.data_loader import load_events
from src.analytics import compute_ecosystem_monthly
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
        [Input("repo-filter", "value"), Input("ecosystem-filter", "value"), Input("month-slider", "value"), Input("bot-toggle", "value")]
    )
    def update_streamgraph(selected_repos, selected_ecosystem, month_range, include_bots):
        start_month, end_month = get_month_range(month_range)
        include_bots_bool = bool(include_bots)
        
        df = load_events(repos=selected_repos, ecosystem=selected_ecosystem, start_month=start_month, end_month=end_month, include_bots=include_bots_bool)
        if df.empty:
            return _empty_figure("No activity data for the current filters.")
            
        monthly = compute_ecosystem_monthly(df)
        if monthly.empty:
            return _empty_figure("No data after aggregation.")
            
        pivot = monthly.pivot(index='year_month', columns='ecosystem', values='event_count').fillna(0)
        
        ecosystems = [eco for eco in ECOSYSTEM_COLORS if eco in pivot.columns]
        ecosystems += [eco for eco in pivot.columns if eco not in ecosystems]
        
        totals = pivot[ecosystems].sum(axis=1)
        baseline = -totals / 2.0
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=pivot.index, y=baseline, mode="lines", line=dict(width=0), hoverinfo="skip", showlegend=False))
        
        running = baseline.copy()
        palette = px.colors.qualitative.Set2
        for i, eco in enumerate(ecosystems):
            running = running + pivot[eco]
            color = ECOSYSTEM_COLORS.get(eco, palette[i % len(palette)])
            fig.add_trace(go.Scatter(
                x=pivot.index, y=running, mode="lines", name=eco, line=dict(width=0.5, color=color),
                fill="tonexty", fillcolor=color, opacity=0.85,
                hovertemplate=f"<b>{eco}</b><br>%{{x}}<br>Events: " + pivot[eco].astype(str) + "<extra></extra>"
            ))
            
        fig.update_layout(
            xaxis=dict(title=None), yaxis=dict(showticklabels=False, title=None), template="plotly_white",
            hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), margin=dict(t=25, b=20, l=10, r=10)
        )
        return fig
