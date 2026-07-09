# Project Progress Log
## GitHub Repository Health Analytics | CS661 | Group __

This document tracks everything we have done so far, 
every decision we made, and why we made it. 
Anyone reading this should be able to understand 
the full project without asking anyone.

---

## Table of Contents
1. [Project Idea and Motivation](#1-project-idea-and-motivation)
2. [Data Source Decision](#2-data-source-decision)
3. [Data Extraction](#3-data-extraction)
4. [Data Overview](#4-data-overview)
5. [Data Cleaning](#5-data-cleaning)
6. [Project Structure](#6-project-structure)
7. [Feature Engineering](#7-feature-engineering)
8. [Tech Stack Decisions](#8-tech-stack-decisions)
9. [Current Status](#9-current-status)
10. [What Comes Next](#10-what-comes-next)

---

## 1. Project Idea and Motivation

### What problem are we solving?
Every developer at some point has to decide whether to 
use an open-source library in their project. To make 
that decision, they visit the GitHub page and try to 
judge the project health manually:
- Is it still being maintained?
- How fast do they fix bugs?
- Is only one person doing everything?
- Is the project growing or dying?

Right now this requires checking each repository one 
by one with no structured way to compare across projects.

### What we are building
An interactive web-based visual analytics system that 
lets users explore the health of open-source GitHub 
repositories across multiple dimensions — contributor 
activity, code review efficiency, issue responsiveness, 
technology adoption trends — all in one place with 
cross-filtering between panels.

### Who is it for?
- Open-source maintainers
- Engineering managers evaluating libraries
- Developers deciding which tools to adopt

### Why this topic?
- We are CS students — we already understand every 
  concept in this domain (PRs, issues, contributors). 
  No domain learning curve.
- The data is free and publicly available.
- The questions we are answering are real questions 
  that real engineering teams ask every day.
- Every visualization choice is naturally justified 
  by the question it answers.

---

## 2. Data Source Decision

### What we chose
**GH Archive** (https://gharchive.org)

GH Archive records every public GitHub event since 
2011 in structured JSON format with hourly granularity. 
Google hosts this entire dataset as a public BigQuery 
dataset (`githubarchive.*`), which allows SQL queries 
at no cost (up to 1TB/month free).

### Why not other sources?
- Kaggle datasets are static and often outdated
- GitHub REST API has rate limits (5000 requests/hour) 
  which makes large scale analysis impractical
- GH Archive gives us the complete event stream with 
  no rate limits

### How we verified it works
Before finalizing the data source, we ran a test query 
on Google BigQuery:

```sql
SELECT
  repo.name,
  type,
  COUNT(*) as event_count
FROM `githubarchive.day.20240101`
WHERE repo.name IN (
  'facebook/react',
  'vuejs/vue',
  'tensorflow/tensorflow'
)
GROUP BY repo.name, type
ORDER BY event_count DESC
```

This returned real GitHub data immediately, confirming 
the dataset is accessible and well-structured.

---

## 3. Data Extraction

### What we extracted
We queried the BigQuery public dataset filtering to:
- 30 specific repositories across 3 ecosystems
- 2 year window: January 2023 to December 2024
- 6 event types only

### Event types we kept and why

| Event Type | Why We Need It |
|------------|---------------|
| PullRequestEvent | PR lifecycle, review latency |
| IssuesEvent | Issue responsiveness analysis |
| IssueCommentEvent | Response time, contributor network |
| PushEvent | Commit activity, bus factor |
| WatchEvent | Technology adoption trends |
| ReleaseEvent | Release patterns |

### Repositories selected

**Frontend Ecosystem (9 repos)**
- facebook/react
- facebook/react-native
- vuejs/vue
- sveltejs/svelte
- angular/angular
- vercel/next.js
- tailwindlabs/tailwindcss
- mui/material-ui
- twbs/bootstrap

**ML/Data Ecosystem (9 repos)**
- pytorch/pytorch
- tensorflow/tensorflow
- keras-team/keras
- huggingface/transformers
- microsoft/DeepSpeed
- ray-project/ray
- scikit-learn/scikit-learn
- pandas-dev/pandas
- numpy/numpy

**Backend/DevOps Ecosystem (11 repos)**
- microsoft/vscode
- kubernetes/kubernetes
- golang/go
- elastic/elasticsearch
- apache/spark
- hashicorp/terraform
- ansible/ansible
- tiangolo/fastapi
- django/django
- pallets/flask
- docker/compose
- flutter/flutter

### Output
Raw data saved as `gh_archive_data.csv`

---

## 4. Data Overview

### Basic Statistics

| Property | Value |
|----------|-------|
| Total rows | 3,448,426 |
| Total columns | 10 |
| File size | 485.3 MB |
| Date range | Jan 1 2023 to Dec 31 2024 |
| Unique actors | 520,041 |
| Unique human actors | 519,233 |
| Unique bot actors | 808 |

### Column Descriptions

| Column | Type | Description |
|--------|------|-------------|
| repo | string | Full repo name e.g. facebook/react |
| date | datetime | When the event occurred (UTC) |
| event_type | string | Type of GitHub event |
| actor | string | GitHub username who triggered event |
| action | string | Specific action within event type |
| pr_or_issue_number | integer | PR or issue number |
| closed_at | datetime | When PR/issue was closed |
| merged_at | datetime | When PR was merged |
| state | string | open, closed, or none |
| author_association | string | Actor's relationship to the repo |

### Event Distribution

| Event Type | Count | Percentage |
|------------|-------|------------|
| IssueCommentEvent | 1,555,472 | 45.1% |
| PushEvent | 582,564 | 16.9% |
| WatchEvent | 573,744 | 16.6% |
| PullRequestEvent | 411,496 | 11.9% |
| IssuesEvent | 323,307 | 9.4% |
| ReleaseEvent | 1,843 | 0.1% |

### Events per Ecosystem

| Ecosystem | Repos | Events |
|-----------|-------|--------|
| ML/Data | 9 | 1,345,003 |
| Backend/DevOps | 11 | 1,160,021 |
| Frontend | 9 | 651,205 |

### Top 5 Repos by Activity

| Repository | Events |
|------------|--------|
| pytorch/pytorch | 686,671 |
| microsoft/vscode | 321,380 |
| kubernetes/kubernetes | 300,200 |
| flutter/flutter | 292,197 |
| tensorflow/tensorflow | 177,584 |

### Bot Activity

| Property | Value |
|----------|-------|
| Bot events | 848,909 |
| Human events | 2,599,517 |
| Bot percentage | 24.62% |

Top bots: k8s-ci-robot (148,901), pytorchmergebot 
(126,308), github-actions[bot] (105,592)

### PR Statistics

| Property | Value |
|----------|-------|
| Total PR events | 411,496 |
| Unique PRs | 140,024 |
| Matched open-to-merge pairs | 98,518 |
| Median merge time | 11.5 hours |
| Mean merge time | 149.8 hours |

### Issue Statistics

| Property | Value |
|----------|-------|
| Total issue events | 323,307 |
| Issues opened | 157,887 |
| Issues closed | 152,908 |
| Issues with response data | 134,101 |
| Median response time | 3.9 hours |
| Mean response time | 235.5 hours |

---

## 5. Data Cleaning

### Why cleaning was needed
1. `merged_at` and `closed_at` use `1970-01-01` as a 
   placeholder when the value is null. This breaks any 
   time-based calculation.
2. 24.62% of events are from bot accounts which inflate 
   all activity metrics unfairly.
3. Each row only knows its repo name, not which 
   ecosystem it belongs to. This needs to be added.
4. Date columns are stored as strings in CSV format 
   and need to be parsed as datetime objects.

### What we did

**Step 1 — Parse all date columns**
```python
df['date'] = pd.to_datetime(df['date'])
df['merged_at'] = pd.to_datetime(df['merged_at'])
df['closed_at'] = pd.to_datetime(df['closed_at'])
```

**Step 2 — Fix 1970 placeholder dates**
```python
df.loc[df['merged_at'].dt.year == 1970, 'merged_at'] = None
df.loc[df['closed_at'].dt.year == 1970, 'closed_at'] = None
```

**Step 3 — Flag bot accounts**
```python
df['is_bot'] = df['actor'].str.contains(
    'bot|Bot|\[bot\]|robot|mirror', regex=True, na=False
)
```

**Step 4 — Add ecosystem labels**
Each repo mapped to Frontend, ML/Data, or 
Backend/DevOps ecosystem.

**Step 5 — Add year_month column**
```python
df['year_month'] = df['date'].dt.to_period('M').astype(str)
```

**Step 6 — Save to SQLite database**
```python
conn = sqlite3.connect('github_analytics.db')
df.to_sql('events', conn, if_exists='replace', index=False)
```

### Output
`github_analytics.db` — 500MB SQLite database with 
clean data ready to query.

### Script
See `preprocessing/clean_data.py`

---

## 6. Project Structure
GitHub-Health-Analytics-CS661/
├── app/
│   └── app.py                    # Main Dash application
├── features/
│   ├── feature_engineering.py    # Feature computation scripts
│   ├── bus_factor.csv            # Bus factor per repo
│   ├── pr_latency.csv            # PR merge latency
│   ├── issue_response.csv        # Issue response times
│   ├── contributor_network.csv   # Contributor edges
│   └── bot_activity.csv          # Bot vs human monthly
├── preprocessing/
│   └── clean_data.py             # Data cleaning script
├── requirements.txt
├── README.md
└── PROGRESS.md                   # This file





## 7. Feature Engineering

### Why we need feature engineering
The raw events table does not directly contain what 
we want to visualize. We need to derive higher level 
metrics from it.

### Features being computed

**PR Latency** (`pr_latency.csv`)
- Match PullRequestEvent with action=opened to 
  PullRequestEvent with action=closed and merged_at set
- Compute difference in hours
- Filter out negative or zero values

**Issue Response Time** (`issue_response.csv`)
- Match IssuesEvent action=opened with earliest 
  IssueCommentEvent on same issue number
- Compute difference in hours

**Bot vs Human Activity** (`bot_activity.csv`)
- Group by repo and year_month
- Separate bot rows from human rows
- Count each separately

**Contributor Network** (`contributor_network.csv`)
- Find all actors who commented on the same PR
- Connect them with an edge
- Weight = number of times they co-collaborated

**Bus Factor** (`bus_factor.csv`)
- Count total push and PR activity per actor per repo
- Sort contributors by activity descending
- Bus factor = minimum people whose removal costs 
  the project 50% of its activity
---

## 7a. Bus Factor — Explained

### What is "bus factor"?
It's a way to measure how risky a project is in terms of 
people. It answers: "If the top contributors got hit by a 
bus tomorrow, how much trouble would this project be in?"

A **low bus factor** (like 1 or 2) means the project depends 
heavily on a tiny number of people. If they left, the project 
would struggle to keep going.

A **high bus factor** means contribution is spread across many 
people, so the project is more resilient — losing a few people 
doesn't hurt much.

### How we calculated it

**Step 1 — Decide what counts as "activity"**
We used two event types as a proxy for real contribution work:
- `PushEvent` (someone pushed code)
- `PullRequestEvent` (someone opened/worked on a PR)

We did NOT include comments, issues, or watches here — those 
measure discussion/interest, not code contribution.

**Step 2 — Remove bots**
Every repo has automated accounts (CI bots, merge bots, release 
bots) that generate huge amounts of fake "activity." We already 
had an `is_bot` column from data cleaning, so we filtered these 
out. Without this step, bots would completely hide the real 
human bus factor.

**Step 3 — Count activity per person, per repo**
For each repo, we counted how many push/PR events each human 
contributor made.

**Step 4 — Sort and find the tipping point**
We sorted contributors from most active to least active, then 
added them up one by one until we crossed 50% of the repo's 
total activity. The number of people it took to cross that 
line is the bus factor.

Example: if a repo's top 3 contributors together made 50%+ of 
all push/PR activity, the bus factor is 3.

### The code

```python
import pandas as pd
import sqlite3

conn = sqlite3.connect('github_analytics.db')

# Pull only push + PR activity, excluding bots
query = """
SELECT repo, actor
FROM events
WHERE event_type IN ('PushEvent', 'PullRequestEvent')
  AND is_bot = 0
"""
df = pd.read_sql(query, conn)
conn.close()

# Count activity per actor per repo
activity = (
    df.groupby(['repo', 'actor'])
      .size()
      .reset_index(name='activity_count')
)

# For each repo, find minimum contributors covering 50% of activity
def compute_bus_factor(group):
    sorted_group = group.sort_values('activity_count', ascending=False).reset_index(drop=True)
    total = sorted_group['activity_count'].sum()
    threshold = total * 0.5

    cumulative = 0
    for i, row in sorted_group.iterrows():
        cumulative += row['activity_count']
        if cumulative >= threshold:
            return i + 1  # people needed, 1-indexed
    return len(sorted_group)

bus_factor_results = []
for repo, group in activity.groupby('repo'):
    bf = compute_bus_factor(group)
    bus_factor_results.append({
        'repo': repo,
        'bus_factor': bf,
        'total_contributors': group['actor'].nunique(),
        'total_activity': group['activity_count'].sum()
    })

bus_factor_df = pd.DataFrame(bus_factor_results).sort_values('bus_factor')
bus_factor_df.to_csv('bus_factor.csv', index=False)
```

### Output
`features/bus_factor.csv` — one row per repo, with:

| Column | Meaning |
|---|---|
| repo | repo name |
| bus_factor | min. people whose removal would cost 50%+ of push/PR activity |
| total_contributors | how many unique humans contributed |
| total_activity | total push/PR events (bots excluded) |

### Validation — did we trust the numbers?
Two repos initially looked suspicious: `kubernetes/kubernetes` 
(bus_factor 56) and `tensorflow/tensorflow` (bus_factor 13) — 
both had surprisingly low total activity for their size.

We manually queried the top contributors for both repos and 
found the real explanation: both are dominated by merge bots 
(`k8s-ci-robot`, `copybara-service[bot]`) that were correctly 
excluded by our bot filter. What's left is real human activity, 
which happens to be spread very thin across many contributors — 
a real finding, not a bug.

**Known limitation:** our bot-detection regex catches most 
automated accounts (`bot`, `[bot]`, `robot`, `mirror`) but 
missed `tensorflow-jenkins`, which is likely also automated. 
Impact is small (573 events, doesn't change the result 
meaningfully) so we left it as-is. Worth tightening the regex 
in a future pass if time allows.

### Interesting findings for the presentation
- `kubernetes/kubernetes`: bus_factor 56 — extremely well 
  distributed human contribution, almost everything else is bots
- `pytorch/pytorch`: bus_factor 29 out of 2266 contributors — 
  large base but still fairly concentrated at the top
- `vuejs/vue`: bus_factor 22 out of only 190 contributors — 
  unusually concentrated for a smaller project
- `tiangolo/fastapi`, `keras-team/keras`, `pallets/flask`: 
  bus_factor 1 — classic "one maintainer holds it together" risk

---

### Scripts
See `features/feature_engineering.py`

---

## 8. Tech Stack Decisions

### Why Plotly Dash and not React + D3
- Entire app in Python — no JavaScript needed
- Everyone on the team knows Python
- Dash has built-in cross-filtering support
- Plotly charts are interactive by default
- Dash-Cytoscape handles network graphs in Python

### Why SQLite and not PostgreSQL
- No server setup needed
- Single file database
- Fast enough for 3.4 million rows
- Works on every laptop without configuration

### Why BigQuery for extraction
- GH Archive is already hosted there as a public dataset
- Free up to 1TB/month
- SQL interface — easy to filter exactly what we need
- No scraping, no API limits

### Full stack

| Component | Technology | Reason |
|-----------|------------|--------|
| Data extraction | Google BigQuery | Free, fast, SQL |
| Data processing | Python, Pandas, NumPy | Everyone knows it |
| Graph metrics | NetworkX | Best Python graph library |
| Database | SQLite | Simple, no setup |
| App and charts | Plotly Dash | Python only, interactive |
| Network graph | Dash-Cytoscape | Force directed in Python |

---



