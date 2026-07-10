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


# Used by: sankey_cb.py
def get_pr_stage_counts(df):
    """
    Count PRs at each lifecycle stage for Sankey diagram.

    Input:  raw events DataFrame from load_events()
    Output: dict with keys:
            opened | merged | closed_without_merge
    """
    pr_df = df[df['event_type'] == 'PullRequestEvent'].copy()
    pr_df['merged_at'] = pd.to_datetime(
        pr_df['merged_at'], errors='coerce'
    )

    opened = len(pr_df[pr_df['action'] == 'opened'])
    merged = len(pr_df[
        (pr_df['action'] == 'closed') &
        (pr_df['merged_at'].notna())
    ])
    closed_no_merge = len(pr_df[
        (pr_df['action'] == 'closed') &
        (pr_df['merged_at'].isna())
    ])

    return {
        'opened': opened,
        'merged': merged,
        'closed_without_merge': closed_no_merge
    }


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