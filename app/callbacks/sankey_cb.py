from dash import Input, Output
import plotly.graph_objects as go
from src.data_loader import load_events, load_pr_latency
from src.analytics import get_pr_stage_counts, apply_millers_law
from app.components.filters import get_month_range

def register(app):
    @app.callback(
        Output('pr-sankey', 'figure'),
        [Input('repo-filter', 'value'), 
         Input('sankey-repo-filter', 'value'),
         Input('month-slider', 'value'), 
         Input('bot-toggle', 'value')]
    )
    def update_sankey(selected_repos, sankey_repo, month_range, include_bots):
        start_month, end_month = get_month_range(month_range)
        include_bots_bool = bool(include_bots)
        
        sankey_selected_repos = selected_repos if sankey_repo == 'ALL' else [sankey_repo]
        
        df_events = load_events(repos=sankey_selected_repos, start_month=start_month, end_month=end_month, include_bots=include_bots_bool)
        if df_events.empty:
            return go.Figure(layout=dict(title="No data found matching filters"))
            
        stage_counts = get_pr_stage_counts(df_events)
        
        df_latency = load_pr_latency(selected_repos, start_month=start_month, end_month=end_month, include_bots=include_bots_bool)
        df_latency = apply_millers_law(df_latency, selected_repos)
        
        label = ["Opened PRs", "Reviewed", "Unreviewed", "Merged", "Closed w/o Merge", "Still Open"]
        color = ["#94a3b8", "#3b82f6", "#f59e0b", "#10b981", "#ef4444", "#64748b"]
        source = [0, 0, 1, 1, 1, 2, 2, 2]
        target = [1, 2, 3, 4, 5, 3, 4, 5]
        value = [
            stage_counts['opened_to_reviewed'],
            stage_counts['opened_to_unreviewed'],
            stage_counts['reviewed_to_merged'],
            stage_counts['reviewed_to_closed'],
            stage_counts['reviewed_to_open'],
            stage_counts['unreviewed_to_merged'],
            stage_counts['unreviewed_to_closed'],
            stage_counts['unreviewed_to_open']
        ]
        
        # Filter out 0 value links so Sankey doesn't complain or draw empty flows
        valid_indices = [i for i, v in enumerate(value) if v > 0]
        source = [source[i] for i in valid_indices]
        target = [target[i] for i in valid_indices]
        value = [value[i] for i in valid_indices]
        link_colors = [
            "rgba(59, 130, 246, 0.2)", "rgba(245, 158, 11, 0.2)",
            "rgba(16, 185, 129, 0.2)", "rgba(239, 68, 68, 0.2)", "rgba(100, 116, 139, 0.2)",
            "rgba(16, 185, 129, 0.2)", "rgba(239, 68, 68, 0.2)", "rgba(100, 116, 139, 0.2)"
        ]
        link_colors = [link_colors[i] for i in valid_indices]
        
        fig = go.Figure()
        
        fig.add_trace(go.Sankey(
            domain=dict(x=[0, 0.48], y=[0, 1]),
            node=dict(pad=35, thickness=20, line=dict(color="black", width=0.5), label=label, color=color),
            link=dict(source=source, target=target, value=value, color=link_colors),
            textfont=dict(size=10)
        ))
        

        
        if not df_latency.empty:
            # Generate boxes for each selected repo to ensure consistent distinct colors
            import plotly.express as px
            
            if len(selected_repos) > 1:
                box_fig = px.box(df_latency, x='repo', y='latency_hours', color='repo', hover_data={'repo': False})
            else:
                box_fig = px.box(df_latency, y='latency_hours')
                
            for trace in box_fig.data:
                trace.xaxis = 'x2'
                trace.yaxis = 'y2'
                trace.hoveron = 'boxes' # Prevent overlapping outlier tooltips
                trace.boxpoints = 'outliers'
                trace.showlegend = False # Hide boxplot from legend to prioritize Sankey states
                trace.name = ""
                trace.hoverinfo = 'y' # Show only y statistics, hide trace name
                trace.hovertemplate = None
                fig.add_trace(trace)
            
        template = 'plotly_white'
        

        
        fig.update_layout(
            margin=dict(t=35, b=20, l=10, r=10),
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            xaxis2=dict(domain=[0.60, 1.0], title="Repository" if len(selected_repos) > 1 else "", showgrid=True),
            yaxis2=dict(domain=[0, 1], anchor='x2', showgrid=True, type='log', title="Merge Latency (hrs)", side='right', hoverformat=".2f", ticksuffix=" hrs"),
            template=template, showlegend=False
        )
        return fig
