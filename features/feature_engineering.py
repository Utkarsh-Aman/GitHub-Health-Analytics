import sqlite3
import pandas as pd
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, '..', 'data', 'github_analytics.db')

print("Looking for db at:", DB_PATH)
print("Exists:", os.path.exists(DB_PATH))


conn = sqlite3.connect(DB_PATH)
activity = pd.read_sql_query("""
    SELECT repo, pr_or_issue_number, actor
    FROM events
    WHERE is_bot = 0
      AND event_type IN ('PullRequestEvent', 'IssueCommentEvent')
""", conn)
conn.close()

print(activity.shape)
print(activity.head())

from itertools import combinations

edges = []
for (repo, number), group in activity.groupby(['repo', 'pr_or_issue_number']):
    actors = group['actor'].unique().tolist()
    if len(actors) >= 2:
        for a, b in combinations(sorted(actors), 2):
            edges.append({'repo': repo, 'source': a, 'target': b})

edge_df = pd.DataFrame(edges)
print("Raw edges:", edge_df.shape)


edge_df = edge_df.groupby(['repo', 'source', 'target']).size().reset_index(name='weight')
print("After collapsing to weights:", edge_df.shape)

edge_df = edge_df[edge_df['weight'] >= 2]
print("After dropping one-off edges:", edge_df.shape)


import networkx as nx

node_stats = []
for repo, group in edge_df.groupby('repo'):
    G = nx.Graph()
    for _, row in group.iterrows():
        G.add_edge(row['source'], row['target'], weight=row['weight'])
    centrality = nx.degree_centrality(G)
    for actor, c in centrality.items():
        node_stats.append({'repo': repo, 'actor': actor, 'centrality': c})

node_df = pd.DataFrame(node_stats)
print("Nodes scored:", node_df.shape)

node_lookup = node_df.set_index(['repo', 'actor'])['centrality']

edge_df['source_centrality'] = edge_df.set_index(['repo','source']).index.map(node_lookup)
edge_df['target_centrality'] = edge_df.set_index(['repo','target']).index.map(node_lookup)

OUTPUT_PATH = os.path.join(SCRIPT_DIR, 'contributor_network.csv')
edge_df.to_csv(OUTPUT_PATH, index=False)
print("Saved to:", OUTPUT_PATH)