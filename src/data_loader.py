import pandas as pd
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.globals import get_connection, FEATURES_DIR


# Main events table — queried from SQLite
def load_events(repos=None, ecosystem=None,
                start_month=None, end_month=None,
                include_bots=False):
    """
    Load events from SQLite database with filters.

    Parameters:
        repos         : list of repo names
        ecosystem     : 'Frontend', 'ML/Data', 'Backend/DevOps'
        start_month   : '2023-01'
        end_month     : '2024-12'
        include_bots  : False by default

    Returns: pandas DataFrame
    """
    conn = get_connection()
    conditions = ["1=1"]
    params = []

    if not include_bots:
        conditions.append("is_bot = 0")

    if repos:
        placeholders = ','.join(['?' for _ in repos])
        conditions.append(f"repo IN ({placeholders})")
        params.extend(repos)

    if ecosystem:
        conditions.append("ecosystem = ?")
        params.append(ecosystem)

    if start_month:
        conditions.append("year_month >= ?")
        params.append(start_month)

    if end_month:
        conditions.append("year_month <= ?")
        params.append(end_month)

    query = "SELECT * FROM events WHERE " + " AND ".join(conditions)
    df = pd.read_sql(query, conn, params=params)
    conn.close()
    return df


# Feature tables — read directly from CSV files
def load_pr_latency(repos=None):
    """
    Load precomputed PR latency data.
    Columns: repo, pr_number, opened_at, merged_at, latency_hours
    """
    df = pd.read_csv(os.path.join(FEATURES_DIR, 'pr_latency.csv'))
    if repos:
        df = df[df['repo'].isin(repos)]
    return df


def load_issue_response(repos=None):
    """
    Load precomputed issue response time data.
    Columns: repo, issue_number, opened_at, 
             first_comment_at, response_time_hours
    """
    df = pd.read_csv(os.path.join(FEATURES_DIR, 'issue_response.csv'))
    if repos:
        df = df[df['repo'].isin(repos)]
    return df


def load_bot_activity(repos=None):
    """
    Load precomputed bot vs human activity data.
    Columns: repo, year_month, bot_events, human_events
    """
    df = pd.read_csv(os.path.join(FEATURES_DIR, 'bot_activity.csv'))
    if repos:
        df = df[df['repo'].isin(repos)]
    return df


def load_bus_factor(repos=None):
    """
    Load precomputed bus factor scores.
    Columns: repo, bus_factor, total_contributors, 
             total_activity, top_contributors
    """
    df = pd.read_csv(os.path.join(FEATURES_DIR, 'bus_factor.csv'))
    if repos:
        df = df[df['repo'].isin(repos)]
    return df


def load_contributor_network(repo):
    """
    Load contributor network edges for a specific repo.
    Columns: actor_1, actor_2, repo, weight
    Returns top 500 edges by weight for performance.
    """
    df = pd.read_csv(
        os.path.join(FEATURES_DIR, 'contributor_network.csv')
    )
    df = df[df['repo'] == repo]
    return df.nlargest(500, 'weight')


# Quick test — run this file directly to verify
# python3 src/data_loader.py
if __name__ == '__main__':
    print("Testing data_loader...")

    print("\n1. load_pr_latency:")
    pr = load_pr_latency(repos=['facebook/react'])
    print(pr.head(3))
    print("Rows:", len(pr))

    print("\n2. load_issue_response:")
    issue = load_issue_response(repos=['pytorch/pytorch'])
    print(issue.head(3))
    print("Rows:", len(issue))

    print("\n3. load_bot_activity:")
    bot = load_bot_activity(repos=['kubernetes/kubernetes'])
    print(bot.head(3))

    print("\n4. load_bus_factor:")
    bf = load_bus_factor()
    print(bf.head(5))

    print("\n5. load_contributor_network:")
    net = load_contributor_network('facebook/react')
    print(net.head(3))
    print("Edges:", len(net))

    print("\nAll tests passed.")