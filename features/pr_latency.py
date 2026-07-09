"""
Feature: PR Latency
Computes time-to-merge (in hours) for every merged pull request,
per repo, per ecosystem, per month.

Input : github_analytics.db  (table: events)
Output: features/pr_latency.csv
"""

import sqlite3
import pandas as pd
from pathlib import Path

# Resolve paths relative to this script's own location, not the current
# working directory, so it works no matter which folder you run it from.
SCRIPT_DIR = Path(__file__).resolve().parent
DB_PATH = SCRIPT_DIR / ".." / "data" / "github_analytics.db"
OUT_PATH = SCRIPT_DIR / "pr_latency.csv"

def load_pr_events(conn):
    """Pull only PullRequestEvent rows, only the columns we need."""
    query = """
        SELECT repo, ecosystem, pr_or_issue_number, action, date, merged_at
        FROM events
        WHERE event_type = 'PullRequestEvent'
    """
    df = pd.read_sql(query, conn, parse_dates=["date", "merged_at"])
    return df


def compute_pr_latency(pr_df):
    # 1. The "opened" row for each PR
    opened = (
        pr_df[pr_df["action"] == "opened"]
        [["repo", "ecosystem", "pr_or_issue_number", "date"]]
        .rename(columns={"date": "opened_at"})
    )

    # 2. The "closed" row, but only where merged_at is actually set
    #    (closed + merged_at NULL == rejected/closed-without-merge -> excluded)
    merged = (
        pr_df[(pr_df["action"] == "closed") & (pr_df["merged_at"].notna())]
        [["repo", "pr_or_issue_number", "merged_at"]]
    )

    # 3. Join opened -> merged on the same repo + PR number
    pr_latency = opened.merge(merged, on=["repo", "pr_or_issue_number"], how="inner")

    # 4. Compute latency in hours
    pr_latency["latency_hours"] = (
        (pr_latency["merged_at"] - pr_latency["opened_at"]).dt.total_seconds() / 3600
    )

    # 5. Sanity filtering
    #    - drop negative latency (bad data / out-of-order events)
    #    - drop PRs open longer than 180 days (treated as stale outliers,
    #      these would otherwise blow up the mean and squash the chart scale)
    before = len(pr_latency)
    pr_latency = pr_latency[pr_latency["latency_hours"] >= 0]
    pr_latency = pr_latency[pr_latency["latency_hours"] <= 180 * 24]
    after = len(pr_latency)
    print(f"Filtered {before - after} outlier/invalid rows ({before} -> {after})")

    # 6. Add a month column for time-based aggregation in the streamgraph / sankey
    pr_latency["month"] = pr_latency["opened_at"].dt.to_period("M").astype(str)

    return pr_latency.sort_values(["repo", "opened_at"]).reset_index(drop=True)


def main():
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Could not find database at: {DB_PATH.resolve()}\n"
            f"Check that github_analytics.db is actually there, or update "
            f"DB_PATH at the top of this script to the correct location."
        )
    conn = sqlite3.connect(DB_PATH)
    pr_df = load_pr_events(conn)
    conn.close()

    print(f"Loaded {len(pr_df)} PullRequestEvent rows")
    print(f"  - opened: {(pr_df['action']=='opened').sum()}")
    print(f"  - closed: {(pr_df['action']=='closed').sum()}")
    print(f"  - reopened: {(pr_df['action']=='reopened').sum()}")

    pr_latency = compute_pr_latency(pr_df)

    print(f"\nMatched {len(pr_latency)} opened->merged PR pairs")
    print(f"Median latency: {pr_latency['latency_hours'].median():.1f} hours")
    print(f"Mean latency:   {pr_latency['latency_hours'].mean():.1f} hours")

    pr_latency.to_csv(OUT_PATH, index=False)
    print(f"\nSaved to {OUT_PATH}")


if __name__ == "__main__":
    main()