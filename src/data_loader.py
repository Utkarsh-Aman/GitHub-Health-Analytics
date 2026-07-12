import pandas as pd
import os
import sys
from functools import lru_cache
import threading

_events_lock = threading.Lock()
_pr_lock = threading.Lock()
_issue_lock = threading.Lock()
_bot_lock = threading.Lock()

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
    repos_tuple = tuple(repos) if repos else None
    with _events_lock:
        return _load_events_cached(repos_tuple, ecosystem, start_month, end_month, include_bots)

@lru_cache(maxsize=32)
def _load_events_cached(repos, ecosystem, start_month, end_month, include_bots):
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
def load_pr_latency(repos=None, start_month=None, end_month=None, include_bots=True):
    """
    Load precomputed PR latency data with time filtering.
    """
    repos_tuple = tuple(repos) if repos else None
    with _pr_lock:
        return _load_pr_latency_cached(repos_tuple, start_month, end_month, include_bots)

@lru_cache(maxsize=32)
def _load_pr_latency_cached(repos, start_month, end_month, include_bots):
    df = pd.read_csv(os.path.join(FEATURES_DIR, 'pr_latency.csv'))
    if repos:
        df = df[df['repo'].isin(repos)]
    if start_month:
        df = df[df['month'] >= start_month]
    if end_month:
        df = df[df['month'] <= end_month]
    if not include_bots and 'is_bot' in df.columns:
        df = df[df['is_bot'] == 0]
    return df


def load_issue_response(repos=None, start_month=None, end_month=None, include_bots=True):
    """
    Load precomputed issue response time data with time filtering.
    """
    repos_tuple = tuple(repos) if repos else None
    with _issue_lock:
        return _load_issue_response_cached(repos_tuple, start_month, end_month, include_bots)

@lru_cache(maxsize=32)
def _load_issue_response_cached(repos, start_month, end_month, include_bots):
    df = pd.read_csv(os.path.join(FEATURES_DIR, 'issue_response.csv'))
    if repos:
        df = df[df['repo'].isin(repos)]
    if start_month:
        df = df[df['year_month'] >= start_month]
    if end_month:
        df = df[df['year_month'] <= end_month]
    if not include_bots and 'is_bot' in df.columns:
        df = df[df['is_bot'] == 0]
    return df


def load_bot_activity(repos=None, ecosystem=None, start_month=None, end_month=None):
    """
    Load precomputed bot vs human activity data with time filtering.
    """
    repos_tuple = tuple(repos) if repos else None
    with _bot_lock:
        return _load_bot_activity_cached(repos_tuple, ecosystem, start_month, end_month)

@lru_cache(maxsize=32)
def _load_bot_activity_cached(repos, ecosystem, start_month, end_month):
    df = pd.read_csv(os.path.join(FEATURES_DIR, 'bot_activity.csv'))
    if repos:
        df = df[df['repo'].isin(repos)]
    if ecosystem:
        df = df[df['ecosystem'] == ecosystem]
    if start_month:
        df = df[df['year_month'] >= start_month]
    if end_month:
        df = df[df['year_month'] <= end_month]
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