import pandas as pd
import sqlite3

import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
conn = sqlite3.connect(os.path.join(BASE_DIR, 'github_analytics.db'))

# Step 1: Pull only push + PR activity, excluding bots
query = """
SELECT repo, actor
FROM events
WHERE event_type IN ('PushEvent', 'PullRequestEvent')
  AND is_bot = 0
"""
df = pd.read_sql(query, conn)
conn.close()

print("Rows pulled:", len(df))

# Step 2: Count activity per actor per repo
activity = (
    df.groupby(['repo', 'actor'])
      .size()
      .reset_index(name='activity_count')
)

# Step 3: Compute bus factor per repo
def compute_bus_factor(group):
    sorted_group = group.sort_values('activity_count', ascending=False).reset_index(drop=True)
    total = sorted_group['activity_count'].sum()
    threshold = total * 0.5

    cumulative = 0
    for i, row in sorted_group.iterrows():
        cumulative += row['activity_count']
        if cumulative >= threshold:
            return i + 1  # number of people needed (1-indexed)
    return len(sorted_group)  # fallback, shouldn't hit this

bus_factor_results = []
for repo, group in activity.groupby('repo'):
    bf = compute_bus_factor(group)
    total_contributors = group['actor'].nunique()
    total_activity = group['activity_count'].sum()
    bus_factor_results.append({
        'repo': repo,
        'bus_factor': bf,
        'total_contributors': total_contributors,
        'total_activity': total_activity
    })

bus_factor_df = pd.DataFrame(bus_factor_results).sort_values('bus_factor')

bus_factor_df.to_csv('bus_factor.csv', index=False)
print(bus_factor_df)
print("Saved to features/bus_factor.csv")