"""
Issue Responsiveness Feature Engineering
GitHub Repository Health Analytics

Run this from inside the `features` folder, with github_analytics.db
also sitting in the `features` folder (same folder as this script).

Produces (in the current folder):
  issue_response.csv          -> one row per issue
  issue_response_summary.csv  -> one row per repo (for KPI cards)
  issue_response_daily.csv    -> repo x date counts (for the calendar heatmap)

Logic:
  Match IssuesEvent(action='opened') with the EARLIEST IssueCommentEvent
  on the same (repo, issue_number). Response time = difference in hours.
  Bot comments are excluded, since we only care about human responsiveness.
"""

import pandas as pd
import sqlite3

conn = sqlite3.connect('github_analytics .db')

# ---------------------------------------------------------
# Step 1 — Pull all issues that were opened
# ---------------------------------------------------------
opened_query = """
SELECT repo, pr_or_issue_number AS issue_number, date AS opened_at
FROM events
WHERE event_type = 'IssuesEvent'
  AND action = 'opened'
"""
opened_df = pd.read_sql(opened_query, conn)
opened_df['opened_at'] = pd.to_datetime(opened_df['opened_at'])

# ---------------------------------------------------------
# Step 2 — Pull all issue comments, excluding bots
# (a bot auto-replying isn't a "human response" for this metric)
# ---------------------------------------------------------
comments_query = """
SELECT repo, pr_or_issue_number AS issue_number, date AS comment_at,
       actor, author_association
FROM events
WHERE event_type = 'IssueCommentEvent'
  AND is_bot = 0
"""
comments_df = pd.read_sql(comments_query, conn)
comments_df['comment_at'] = pd.to_datetime(comments_df['comment_at'])
conn.close()

# ---------------------------------------------------------
# Step 3 — For each (repo, issue_number), keep only the EARLIEST comment
# ---------------------------------------------------------
first_response = (
    comments_df.sort_values('comment_at')
    .groupby(['repo', 'issue_number'], as_index=False)
    .first()
    .rename(columns={
        'comment_at': 'first_response_at',
        'actor': 'responder',
        'author_association': 'responder_association'
    })
)

# ---------------------------------------------------------
# Step 4 — Merge opened issues with their first response (left join,
# so issues that never got a response are kept with NaT/NaN)
# ---------------------------------------------------------
issue_response = opened_df.merge(
    first_response,
    on=['repo', 'issue_number'],
    how='left'
)

# ---------------------------------------------------------
# Step 5 — Compute response time in hours
# ---------------------------------------------------------
issue_response['response_time_hours'] = (
    (issue_response['first_response_at'] - issue_response['opened_at'])
    .dt.total_seconds() / 3600
)

# ---------------------------------------------------------
# Step 6 — Drop bad rows: negative response time means a comment event
# was logged before the open event (duplicate/out-of-order events)
# ---------------------------------------------------------
issue_response = issue_response[
    issue_response['response_time_hours'].isna()
    | (issue_response['response_time_hours'] > 0)
].copy()

# ---------------------------------------------------------
# Step 7 — Convenience columns for the app / visualizations
# ---------------------------------------------------------
issue_response['has_response'] = issue_response['response_time_hours'].notna()
issue_response['year_month'] = issue_response['opened_at'].dt.to_period('M').astype(str)
issue_response['opened_date'] = issue_response['opened_at'].dt.date

# ---------------------------------------------------------
# Step 8 — Save per-issue table (current folder, since we're
# already running this script from inside `features/`)
# ---------------------------------------------------------
issue_response.to_csv('issue_response.csv', index=False)

print(f"Total issues opened:        {len(issue_response)}")
print(f"Issues with a response:     {issue_response['has_response'].sum()}")
print(f"Issues with NO response:    {(~issue_response['has_response']).sum()}")
print(f"Median response time (hrs): {issue_response['response_time_hours'].median():.2f}")
print(f"Mean response time (hrs):   {issue_response['response_time_hours'].mean():.2f}")

# ===========================================================
# Repo-level summary (feeds KPI cards on the dashboard)
# ===========================================================
repo_summary = (
    issue_response.groupby('repo')
    .agg(
        total_issues=('issue_number', 'count'),
        issues_with_response=('has_response', 'sum'),
        median_response_hours=('response_time_hours', 'median'),
        mean_response_hours=('response_time_hours', 'mean'),
    )
    .reset_index()
)
repo_summary['response_rate_pct'] = (
    repo_summary['issues_with_response'] / repo_summary['total_issues'] * 100
).round(2)

repo_summary.to_csv('issue_response_summary.csv', index=False)

# ===========================================================
# Daily counts per repo (feeds the Issue Responsiveness
# calendar heatmap mentioned in the README)
# ===========================================================
daily_heatmap = (
    issue_response.groupby(['repo', 'opened_date'])
    .size()
    .reset_index(name='issues_opened')
)

daily_heatmap.to_csv('issue_response_daily.csv', index=False)

print("\nSaved: issue_response.csv")
print("Saved: issue_response_summary.csv")
print("Saved: issue_response_daily.csv")