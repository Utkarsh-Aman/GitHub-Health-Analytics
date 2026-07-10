"""
app/callbacks/streamgraph_cb.py

Drives the "Tech Adoption Streamgraph" panel (id='streamgraph' in app.py).

Shows monthly human event volume per ecosystem (Frontend / ML-Data /
Backend-DevOps) as a symmetric (wiggle-centered) streamgraph, so relative
growth/decline in ecosystem activity over 2023-2024 is easy to read.

Data source: features/bot_activity.csv, via src.data_loader.load_bot_activity.
Bot events (is_bot == 1) are excluded since this panel is about human
adoption/engagement, not automation volume (that's covered by bot_bar_cb).
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from dash import Input, Output

from src.data_loader import load_bot_activity

ECOSYSTEM_COLORS = {
    "Frontend": "#4C78A8",
    "ML/Data": "#F58518",
    "Backend/DevOps": "#54A24B",
}


def _empty_figure(message: str) -> go.Figure:
    """Blank figure with a centered message, used when there's no data to show."""
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=14, color="gray"),
    )
    fig.update_layout(
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        template="plotly_white",
    )
    return fig


def build_streamgraph_figure(df: pd.DataFrame) -> go.Figure:
    """
    Build a symmetric (centered/"wiggle") streamgraph from event-count data.

    df columns expected: repo, ecosystem, year_month, is_bot, event_count
    """
    if df.empty:
        return _empty_figure("No activity data for the current filters.")

    human_df = df[df["is_bot"] == 0]
    if human_df.empty:
        return _empty_figure("No human activity data for the current filters.")

    pivot = (
        human_df
        .groupby(["year_month", "ecosystem"])["event_count"]
        .sum()
        .unstack(fill_value=0)
        .sort_index()
    )

    ecosystems = [eco for eco in ECOSYSTEM_COLORS if eco in pivot.columns]
    # include any ecosystem not in the known palette (defensive, shouldn't happen)
    ecosystems += [eco for eco in pivot.columns if eco not in ecosystems]

    totals = pivot[ecosystems].sum(axis=1)
    baseline = -totals / 2.0

    fig = go.Figure()

    # invisible baseline trace establishes the lower envelope for the first fill
    fig.add_trace(go.Scatter(
        x=pivot.index, y=baseline,
        mode="lines", line=dict(width=0),
        hoverinfo="skip", showlegend=False,
    ))

    running = baseline.copy()
    palette = px.colors.qualitative.Set2
    for i, eco in enumerate(ecosystems):
        running = running + pivot[eco]
        color = ECOSYSTEM_COLORS.get(eco, palette[i % len(palette)])
        fig.add_trace(go.Scatter(
            x=pivot.index,
            y=running,
            mode="lines",
            name=eco,
            line=dict(width=0.5, color=color),
            fill="tonexty",
            fillcolor=color,
            opacity=0.85,
            hovertemplate=(
                f"<b>{eco}</b><br>%{{x}}<br>Events: "
                + pivot[eco].astype(str)
                + "<extra></extra>"
            ),
        ))

    fig.update_layout(
        title="Technology Adoption Streamgraph — Human Activity by Ecosystem",
        xaxis_title="Month",
        yaxis=dict(showticklabels=False, title=None),
        template="plotly_white",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(t=60, b=40, l=20, r=20),
    )
    return fig


def register(app):
    @app.callback(
        Output("streamgraph", "figure"),
        Input("repo-filter", "value"),
        Input("ecosystem-filter", "value"),
    )
    def update_streamgraph(selected_repos, selected_ecosystem):
        """
        Rebuilds the streamgraph whenever the global repo or ecosystem filters change.
        """
        df = load_bot_activity(repos=selected_repos if selected_repos else None)

        if selected_ecosystem:
            df = df[df["ecosystem"] == selected_ecosystem]

        return build_streamgraph_figure(df)