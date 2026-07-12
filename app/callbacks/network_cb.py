"""
app/callbacks/network_cb.py

Drives the "Contributor Collaboration Network" panel:
  - cyto.Cytoscape(id='contributor-network')
  - html.Div(id='network-bus-factor-info')

Unlike the other panels, this graph can become a messy hairball with multiple repos, so it listens to its own single-select 'network-repo-filter' to show one repo at a time.

Data sources:
  - SQLite database, via src.data_loader.load_events
    Processed via src.analytics.compute_dynamic_network
    columns: source, target, weight, source_centrality, target_centrality
  - features/bus_factor.csv, via src.data_loader.load_bus_factor
    columns: repo, bus_factor, total_contributors, total_activity

Node sizing/coloring is driven by source_centrality / target_centrality
(whichever role the contributor appears in); nodes among the top 50% most
central contributors for the repo are tagged with the 'top-contributor'
class so the stylesheet in app.py can highlight them (these are the
people whose departure would most hurt the project — tying visually back
to the bus-factor score).
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import pandas as pd
from dash import Input, Output, html

from src.data_loader import load_events, load_bus_factor
from src.analytics import compute_dynamic_network
from app.components.filters import get_month_range


def _node_centrality_map(edges_df: pd.DataFrame) -> dict:
    """
    Each contributor can appear as either 'source' or 'target' across
    different edges; take the max centrality value seen for that person.
    """
    centrality = {}
    for _, row in edges_df.iterrows():
        for actor, cent in (
            (row["source"], row["source_centrality"]),
            (row["target"], row["target_centrality"]),
        ):
            centrality[actor] = max(centrality.get(actor, 0.0), float(cent))
    return centrality


def build_network_elements(edges_df: pd.DataFrame) -> list:
    """Convert an edge-list DataFrame into Cytoscape elements (nodes + edges)."""
    if edges_df.empty:
        return []

    centrality = _node_centrality_map(edges_df)
    max_centrality = max(centrality.values()) if centrality else 0.0
    threshold = max_centrality * 0.5

    elements = []
    for actor, cent in centrality.items():
        elements.append({
            "data": {
                "id": actor,
                "label": actor,
                "tooltip": f"{actor} (Centrality: {round(cent, 3)})",
                "centrality": round(cent, 4),
            },
            "classes": "top-contributor" if max_centrality and cent >= threshold else "",
        })

    for _, row in edges_df.iterrows():
        elements.append({
            "data": {
                "source": row["source"],
                "target": row["target"],
                "weight": float(row["weight"]),
            }
        })

    return elements


def build_bus_factor_summary(repos: list, edges_df: pd.DataFrame) -> html.Div:
    """Small text summary shown alongside the network graph."""
    bus_df = load_bus_factor(repos)

    if bus_df.empty:
        bus_factor_text = "Bus factor: N/A"
        contributors_text = ""
    else:
        avg_bf = int(bus_df['bus_factor'].mean())
        tot_c = int(bus_df['total_contributors'].sum())
        bus_factor_text = f"Avg Bus factor: {avg_bf}"
        contributors_text = f"Total contributors: {tot_c}"

    edges_text = f"Showing top {len(edges_df)} strongest collaboration edges"

    return html.Div([
        html.Div([
            html.Span(bus_factor_text, style={"marginRight": "16px", "fontWeight": "bold"}),
            html.Span(contributors_text, style={"marginRight": "16px"}),
            html.Span(edges_text),
        ], style={"whiteSpace": "nowrap", "overflow": "hidden", "textOverflow": "ellipsis"}),
        html.Div([
            html.Span("🔴 Top contributor (bus factor risk)", style={"marginRight": "15px"}),
            html.Span("🔵 Regular contributor")
        ], style={"marginTop": "6px", "fontSize": "10px", "color": "gray"})
    ])


def register(app):
    @app.callback(
        Output("contributor-network", "elements"),
        Output("network-bus-factor-info", "children"),
        Output("contributor-network", "stylesheet"),
        [Input("network-repo-filter", "value"),
         Input("month-slider", "value"),
         Input("bot-toggle", "value")]
    )
    def update_network(selected_repo, month_range, include_bots):
        """
        Rebuilds the contributor collaboration network when filters change.
        """
        base_stylesheet = [
            {'selector': 'node', 'style': {'font-size': '7px', 'width': '12px', 'height': '12px', 'background-color': '#4C78A8', 'color': '#333'}},
            {'selector': '.top-contributor', 'style': {'label': 'data(label)', 'background-color': '#ef4444', 'width': '18px', 'height': '18px', 'font-size': '8px', 'font-weight': 'bold'}},
            {'selector': 'edge', 'style': {'width': 'mapData(weight, 1, 30, 0.5, 4)', 'line-color': '#cccccc', 'opacity': 0.6}}
        ]

        if not selected_repo:
            return [], html.Div(
                "Select a repository above to view its contributor network.",
                style={"color": "gray"},
            ), base_stylesheet
            
        selected_repos = [selected_repo]

        start_month, end_month = get_month_range(month_range)
        events_df = load_events(repos=selected_repos, start_month=start_month, end_month=end_month, include_bots=bool(include_bots))

        if events_df.empty:
            return [], html.Div(
                f"No collaboration data available for {selected_repo}.",
                style={"color": "gray"},
            ), base_stylesheet

        edges_df = compute_dynamic_network(events_df)

        if edges_df.empty:
            return [], html.Div(
                f"Not enough collaborations to build a network.",
                style={"color": "gray"},
            ), base_stylesheet

        elements = build_network_elements(edges_df)
        summary = build_bus_factor_summary(selected_repos, edges_df)
        return elements, summary, base_stylesheet

    @app.callback(
        Output("network-hover-info", "children"),
        [Input("contributor-network", "mouseoverNodeData")]
    )
    def display_hover_data(data):
        if data:
            return f"{data.get('id', 'Unknown')} (Centrality: {data.get('centrality', 0)})"
        return "Hover over a node to see details"
        
    @app.callback(
        Output("modal-hover-info", "children"),
        [Input("modal-contributor-network", "mouseoverNodeData")]
    )
    def display_modal_hover_data(data):
        if data:
            return f"{data.get('id', 'Unknown')} (Centrality: {data.get('centrality', 0)})"
        return "Hover over a node to see details"