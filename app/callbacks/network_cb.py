"""
app/callbacks/network_cb.py

Drives the "Contributor Collaboration Network" panel:
  - cyto.Cytoscape(id='contributor-network')
  - html.Div(id='network-bus-factor-info')

Unlike the other panels, this graph is inherently single-repo (edges are
computed per-repo), so it listens to a dedicated 'network-repo-filter'
dropdown rather than the global multi-select 'repo-filter'.

Data sources:
  - features/contributor_network.csv, via src.data_loader.load_contributor_network
    columns: repo, source, target, weight, source_centrality, target_centrality
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

from src.data_loader import load_contributor_network, load_bus_factor


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


def build_bus_factor_summary(repo: str, edges_df: pd.DataFrame) -> html.Div:
    """Small text summary shown alongside the network graph."""
    bus_df = load_bus_factor(repos=[repo])

    if bus_df.empty:
        bus_factor_text = "Bus factor: N/A"
        contributors_text = ""
    else:
        row = bus_df.iloc[0]
        bus_factor_text = f"Bus factor: {int(row['bus_factor'])}"
        contributors_text = f"Total contributors: {int(row['total_contributors'])}"

    edges_text = f"Collaboration edges shown: {len(edges_df)}"

    return html.Div([
        html.Span(bus_factor_text, style={"marginRight": "16px", "fontWeight": "bold"}),
        html.Span(contributors_text, style={"marginRight": "16px"}),
        html.Span(edges_text),
    ])


def register(app):
    @app.callback(
        Output("contributor-network", "elements"),
        Output("network-bus-factor-info", "children"),
        Input("network-repo-filter", "value"),
    )
    def update_network(selected_repo):
        """
        Rebuilds the contributor collaboration network when the single-repo
        network dropdown changes.
        """
        if not selected_repo:
            return [], html.Div(
                "Select a repository above to view its contributor network.",
                style={"color": "gray"},
            )

        edges_df = load_contributor_network(selected_repo)

        if edges_df.empty:
            return [], html.Div(
                f"No collaboration data available for {selected_repo}.",
                style={"color": "gray"},
            )

        elements = build_network_elements(edges_df)
        summary = build_bus_factor_summary(selected_repo, edges_df)
        return elements, summary