import pandas as pd
import numpy as np
import sys, os

sys.path.insert(0, os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))


# Used by: streamgraph_cb.py

def compute_monthly_activity(df):
    """
    Aggregate event counts by repo and month.

    Input:  raw events DataFrame from load_events()
    Output: DataFrame with columns:
            year_month | repo | event_count
    """
    monthly = df.groupby(
        ['year_month', 'repo']
    ).size().reset_index(name='event_count')
    return monthly


def apply_millers_law(df, selected_repos, max_repos=7):
    """
    Implements Miller's Law (7±2) by capping the distinct repos shown in charts to max_repos.
    Any additional selected repos are aggregated into an "Other (aggregate)" bucket.
    """
    if len(selected_repos) <= max_repos or df.empty or 'repo' not in df.columns:
        return df
        
    top_repos = selected_repos[:max_repos]
    df = df.copy()
    df.loc[~df['repo'].isin(top_repos), 'repo'] = 'Other (aggregate)'
    return df

# Used by: streamgraph_cb.py

def compute_ecosystem_monthly(df):
    """
    Aggregate event counts by ecosystem and month.

    Input:  raw events DataFrame from load_events()
    Output: DataFrame with columns:
            year_month | ecosystem | event_count
    """
    monthly = df.groupby(
        ['year_month', 'ecosystem']
    ).size().reset_index(name='event_count')
    return monthly


# Used by: dashboard_cb.py
def compute_health_summary(repos, pr_df,
                            issue_df, bot_df, bf_df):
    """
    Compute one summary row per repo for health dashboard.

    Inputs:
        repos    : list of repo names
        pr_df    : DataFrame from load_pr_latency()
        issue_df : DataFrame from load_issue_response()
        bot_df   : DataFrame from load_bot_activity()
        bf_df    : DataFrame from load_bus_factor()

    Output: DataFrame with columns:
        repo | median_merge_hours | median_response_hours
             | bus_factor | bot_percentage
    """
    results = []

    for repo in repos:
        pr = pr_df[pr_df['repo'] == repo]
        issue = issue_df[issue_df['repo'] == repo]
        bot = bot_df[bot_df['repo'] == repo]
        bf = bf_df[bf_df['repo'] == repo]

        # Median PR merge time
        median_merge = (
            round(pr['latency_hours'].median(), 1)
            if len(pr) > 0 else None
        )

        # Median issue response time
        median_response = (
            round(issue['response_time_hours'].median(), 1)
            if len(issue) > 0 else None
        )

        # Bot percentage
        if len(bot) > 0:
            total = bot['event_count'].sum()
            bot_total = bot[
                bot['is_bot'] == 1
            ]['event_count'].sum()
            bot_pct = (
                round(bot_total / total * 100, 1)
                if total > 0 else 0
            )
        else:
            bot_pct = None

        # Bus factor
        bus = (
            int(bf['bus_factor'].values[0])
            if len(bf) > 0 else None
        )

        results.append({
            'repo': repo,
            'median_merge_hours': median_merge,
            'median_response_hours': median_response,
            'bus_factor': bus,
            'bot_percentage': bot_pct
        })

    return pd.DataFrame(results)


def get_pr_stage_counts(df):
    """
    Count PRs at each lifecycle stage for Sankey diagram.
    """
    if df.empty or 'pr_or_issue_number' not in df.columns:
        return {k: 0 for k in ['opened_to_reviewed', 'opened_to_unreviewed', 'reviewed_to_merged', 'reviewed_to_closed', 'reviewed_to_open', 'unreviewed_to_merged', 'unreviewed_to_closed', 'unreviewed_to_open']}
        
    pr_events = df[df['event_type'] == 'PullRequestEvent']
    opened_prs = pr_events[pr_events['action'] == 'opened']['pr_or_issue_number'].unique()
    
    df_filtered = df[df['pr_or_issue_number'].isin(opened_prs)]
    reviewed_prs = df_filtered[df_filtered['event_type'] == 'IssueCommentEvent']['pr_or_issue_number'].unique()
    
    closed_events = pr_events[(pr_events['action'] == 'closed') & (pr_events['pr_or_issue_number'].isin(opened_prs))].copy()
    closed_events['merged_at'] = pd.to_datetime(closed_events['merged_at'], errors='coerce')
    
    merged_prs = closed_events[closed_events['merged_at'].notna()]['pr_or_issue_number'].unique()
    closed_no_merge_prs = closed_events[closed_events['merged_at'].isna()]['pr_or_issue_number'].unique()
    
    counts = {
        'opened_to_reviewed': 0,
        'opened_to_unreviewed': 0,
        'reviewed_to_merged': 0,
        'reviewed_to_closed': 0,
        'reviewed_to_open': 0,
        'unreviewed_to_merged': 0,
        'unreviewed_to_closed': 0,
        'unreviewed_to_open': 0
    }
    
    for pr in opened_prs:
        is_reviewed = pr in reviewed_prs
        is_merged = pr in merged_prs
        is_closed = pr in closed_no_merge_prs
        is_open = not is_merged and not is_closed
        
        if is_reviewed:
            counts['opened_to_reviewed'] += 1
            if is_merged: counts['reviewed_to_merged'] += 1
            elif is_closed: counts['reviewed_to_closed'] += 1
            else: counts['reviewed_to_open'] += 1
        else:
            counts['opened_to_unreviewed'] += 1
            if is_merged: counts['unreviewed_to_merged'] += 1
            elif is_closed: counts['unreviewed_to_closed'] += 1
            else: counts['unreviewed_to_open'] += 1
            
    return counts


# Used by: heatmap_cb.py
def compute_daily_issue_activity(df):
    """
    Count issue events per day for calendar heatmap.

    Input:  raw events DataFrame from load_events()
    Output: DataFrame with columns:
            date | count | week | day_of_week | year
    """
    issues = df[df['event_type'].isin(
        ['IssuesEvent', 'IssueCommentEvent']
    )].copy()

    issues['date'] = pd.to_datetime(
        issues['date']
    ).dt.date

    daily = issues.groupby(
        'date'
    ).size().reset_index(name='count')

    daily['date'] = pd.to_datetime(daily['date'])
    daily['week'] = daily['date'].dt.isocalendar().week
    daily['day_of_week'] = daily['date'].dt.dayofweek
    daily['year'] = daily['date'].dt.year

    return daily


# Test — run this file directly to verify
# python3 src/analytics.py
if __name__ == '__main__':
    from src.data_loader import (
        load_events, load_pr_latency,
        load_issue_response, load_bot_activity,
        load_bus_factor
    )

    print("Testing analytics.py...")

    df = load_events(
        repos=['facebook/react', 'pytorch/pytorch'],
        start_month='2023-01',
        end_month='2023-03'
    )

    print("\n1. compute_monthly_activity:")
    print(compute_monthly_activity(df))

    print("\n2. compute_ecosystem_monthly:")
    print(compute_ecosystem_monthly(df))

    print("\n3. get_pr_stage_counts:")
    print(get_pr_stage_counts(df))

    print("\n4. compute_daily_issue_activity:")
    print(compute_daily_issue_activity(df).head(5))

    print("\n5. compute_health_summary:")
    repos = ['facebook/react', 'pytorch/pytorch']
    summary = compute_health_summary(
        repos,
        load_pr_latency(repos),
        load_issue_response(repos),
        load_bot_activity(repos),
        load_bus_factor(repos)
    )
    print(summary)

    print("\nAll tests passed.")
import networkx as nx
from itertools import combinations

def compute_dynamic_network(events_df):
    """
    Computes contributor network dynamically from raw events.
    """
    # Filter for PRs and issues only
    activity = events_df[
        (events_df['is_bot'] == 0) & 
        (events_df['event_type'].isin(['PullRequestEvent', 'IssueCommentEvent']))
    ]
    
    if activity.empty:
        return pd.DataFrame()
        
    edges = []
    # Drop rows with null pr_or_issue_number
    activity = activity.dropna(subset=['pr_or_issue_number'])
    
    for _, group in activity.groupby('pr_or_issue_number'):
        actors = group['actor'].unique().tolist()
        if len(actors) >= 2:
            for a, b in combinations(sorted(actors), 2):
                edges.append({'source': a, 'target': b})

    edge_df = pd.DataFrame(edges)
    if edge_df.empty:
        return pd.DataFrame()
        
    edge_df = edge_df.groupby(['source', 'target']).size().reset_index(name='weight')
    edge_df = edge_df[edge_df['weight'] >= 2]
    
    if edge_df.empty:
        return pd.DataFrame()

    G = nx.Graph()
    for _, row in edge_df.iterrows():
        G.add_edge(row['source'], row['target'], weight=row['weight'])

    centrality = nx.degree_centrality(G)
    node_df = pd.DataFrame([{'actor': a, 'centrality': c} for a, c in centrality.items()])

    node_lookup = node_df.set_index('actor')['centrality']
    edge_df['source_centrality'] = edge_df['source'].map(node_lookup)
    edge_df['target_centrality'] = edge_df['target'].map(node_lookup)
    
    return edge_df.nlargest(150, 'weight')

def compute_dynamic_bus_factor(events_df):
    """
    Computes bus factor dynamically from raw events.
    """
    activity = events_df[
        (events_df['is_bot'] == 0) & 
        (events_df['event_type'].isin(['PushEvent', 'PullRequestEvent', 'IssueCommentEvent', 'IssuesEvent']))
    ]
    
    if activity.empty:
        return pd.DataFrame({'repo': [], 'bus_factor': [], 'total_contributors': [], 'total_activity': []})
        
    activity_count = activity.groupby(['repo', 'actor']).size().reset_index(name='count')
    
    results = []
    for repo, group in activity_count.groupby('repo'):
        group = group.sort_values('count', ascending=False)
        total_activity = group['count'].sum()
        total_contributors = len(group)
        
        running_sum = 0
        bus_factor = 0
        for _, row in group.iterrows():
            running_sum += row['count']
            bus_factor += 1
            if running_sum >= total_activity * 0.5:
                break
                
        results.append({
            'repo': repo,
            'bus_factor': bus_factor,
            'total_contributors': total_contributors,
            'total_activity': total_activity
        })
        
    return pd.DataFrame(results)
