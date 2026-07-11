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
9. [File Guide — What to Do in Each File](#9-file-guide--what-to-do-in-each-file)
10. [Current Status](#10-current-status)
11. [What Comes Next](#11-what-comes-next)

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
---

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

query = """
SELECT repo, actor
FROM events
WHERE event_type IN ('PushEvent', 'PullRequestEvent')
  AND is_bot = 0
"""
df = pd.read_sql(query, conn)
conn.close()

activity = (
    df.groupby(['repo', 'actor'])
      .size()
      .reset_index(name='activity_count')
)

def compute_bus_factor(group):
    sorted_group = group.sort_values(
        'activity_count', ascending=False
    ).reset_index(drop=True)
    total = sorted_group['activity_count'].sum()
    threshold = total * 0.5
    cumulative = 0
    for i, row in sorted_group.iterrows():
        cumulative += row['activity_count']
        if cumulative >= threshold:
            return i + 1
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

bus_factor_df = pd.DataFrame(
    bus_factor_results
).sort_values('bus_factor')
bus_factor_df.to_csv('bus_factor.csv', index=False)
```

### Output
`features/bus_factor.csv` — one row per repo, with:

| Column | Meaning |
|--------|---------|
| repo | repo name |
| bus_factor | min people whose removal costs 50%+ activity |
| total_contributors | unique human contributors |
| total_activity | total push/PR events (bots excluded) |

### Interesting findings
- `tiangolo/fastapi`, `keras-team/keras`, `pallets/flask`: 
  bus_factor 1 — one maintainer holds everything together
- `pytorch/pytorch`: bus_factor 29 out of 2266 contributors
- `kubernetes/kubernetes`: bus_factor 56 — very well distributed

## 7b. Contributor Network — Explained

### What is the "contributor network"?
It is a relationship graph that maps out who is collaborating with whom within a repository. It answers: "Is this project a deeply connected community where everyone talks to each other, or is it a group of isolated developers working in silos?"

In this network:
- **Nodes** are individual human contributors.
- **Edges** (connections) are formed when two people collaborate on the same issue or pull request.
- **Weight** represents how many times they collaborated.
- **Centrality** measures how important/connected a specific person is to the rest of the network.

### How we calculated it

**Step 1 — Identify Collaboration Arenas**
We defined a collaboration as two people participating in the same discussion thread. We queried `PullRequestEvent` and `IssueCommentEvent` from our database, ensuring bots were filtered out (`is_bot = 0`). 

**Step 2 — Generate Edges (Connections)**
For every unique issue or PR number, we grabbed the list of actors involved. Using Python's `itertools.combinations`, we created a pairing (an edge) between every single person in that specific thread. 

**Step 3 — Collapse and Filter Noise**
A single thread with 5 people generates many edges. Across millions of events, people might interact once by pure chance. To make the graph meaningful and performant for Dash/Cytoscape, we:
- Grouped identical edges to calculate a `weight` (total interactions between User A and User B).
- Filtered out one-off interactions by enforcing a strict `weight >= 2` rule. 

**Step 4 — Calculate Node Centrality**
Using the `networkx` library, we built a graph for each repository and calculated the **Degree Centrality** for every node. This gives us a metric (between 0 and 1) representing the fraction of the network a single contributor is connected to. 

### The code

```python
import sqlite3
import pandas as pd
import os
from itertools import combinations
import networkx as nx

# Setup paths and connect to DB
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, '..', 'data', 'github_analytics.db')

conn = sqlite3.connect(DB_PATH)

# Pull PR and Issue discussion activity, excluding bots
activity = pd.read_sql_query("""
    SELECT repo, pr_or_issue_number, actor
    FROM events
    WHERE is_bot = 0
      AND event_type IN ('PullRequestEvent', 'IssueCommentEvent')
""", conn)
conn.close()

# Build edges: Connect actors who participated in the same PR/Issue
edges = []
for (repo, number), group in activity.groupby(['repo', 'pr_or_issue_number']):
    actors = group['actor'].unique().tolist()
    if len(actors) >= 2:
        for a, b in combinations(sorted(actors), 2):
            edges.append({'repo': repo, 'source': a, 'target': b})

edge_df = pd.DataFrame(edges)

# Collapse edges to calculate weights and filter out one-off interactions
edge_df = edge_df.groupby(['repo', 'source', 'target']).size().reset_index(name='weight')
edge_df = edge_df[edge_df['weight'] >= 2]

# Calculate Degree Centrality using NetworkX
node_stats = []
for repo, group in edge_df.groupby('repo'):
    G = nx.Graph()
    for _, row in group.iterrows():
        G.add_edge(row['source'], row['target'], weight=row['weight'])
    
    centrality = nx.degree_centrality(G)
    for actor, c in centrality.items():
        node_stats.append({'repo': repo, 'actor': actor, 'centrality': c})

node_df = pd.DataFrame(node_stats)

# Map centrality scores back to the edge list for plotting
node_lookup = node_df.set_index(['repo', 'actor'])['centrality']
edge_df['source_centrality'] = edge_df.set_index(['repo','source']).index.map(node_lookup)
edge_df['target_centrality'] = edge_df.set_index(['repo','target']).index.map(node_lookup)

# Save to CSV
OUTPUT_PATH = os.path.join(SCRIPT_DIR, 'contributor_network.csv')
edge_df.to_csv(OUTPUT_PATH, index=False)
```

### Output
`features/contributor_network.csv` — contains edge list data ready for Dash-Cytoscape mapping, with the following columns:

| Column | Meaning |
|---|---|
| repo | The repository name |
| source | GitHub username of first collaborator |
| target | GitHub username of second collaborator |
| weight | Number of times they collaborated (min. 2) |
| source_centrality | Network importance score of the source user |
| target_centrality | Network importance score of the target user |

### Scripts
See `features/contributer_network.py`

### Interesting findings for the presentation
- **The "Linchpin" Contributors:** Centrality perfectly highlights single-maintainer dependencies. For `pallets/flask`, the user `davidism` has a centrality score of 0.956, meaning they are directly connected to 95.6% of everyone who collaborated in the entire repository. Similarly, `tiangolo` has a centrality of 0.869 in `tiangolo/fastapi`.
- **Massive Developer Ecosystems:** `kubernetes/kubernetes` and `pytorch/pytorch` have the largest raw networks by far, with 7,480 and 6,453 significant edges respectively. However, their maximum centrality scores hover around a much healthier ~0.35, proving these are highly decentralized communities where collaboration is spread out, rather than bottlenecked by one person.
- **Power Duos:** The human contributors who collaborated the most frequently across all repositories analyzed were `ijjk` and `timneutkens` on the `vercel/next.js` repository, racking up an impressive 887 shared interactions.
- **Hidden Bot Detection:** This network analysis inadvertently caught a flaw in our bot filtering! `elastic/elasticsearch` has a user named `elasticsearchmachine` with 1,858 interactions and 0.94 centrality. `huggingface/transformers` has `HuggingFaceDocBuilderDev` with 986 interactions. We missed these with our original `bot|robot` regex, demonstrating how network centrality can be used as an anomaly detection tool to find undeclared automated accounts.

### Scripts
See `features/feature_engineering.py`

--



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

## 9. File Guide — What to Do in Each File

This section tells every team member exactly what 
needs to be written in each file.

---

### `app/globals.py`


This file runs once when the app starts. It sets up 
the shared database connection and loads constants 
that every other file needs.

What to put here:
- Path to `github_analytics.db`
- A `get_connection()` function that returns a SQLite connection
- `REPOS` list — all 30 repo names loaded from the database
- `ECOSYSTEMS` list — ['Frontend', 'ML/Data', 'Backend/DevOps']
- `MONTHS` list — all year_month values from the database

Every other file imports from here. Do not duplicate 
these values anywhere else.

---

### `src/data_loader.py`


This file contains all the functions that query the 
database. No other file should write raw SQL — they 
all call functions from here.

Functions to write:
- `load_events(repos, ecosystem, start_month, end_month, include_bots)`
  → returns filtered rows from the events table
- `load_pr_latency(repos)` 
  → returns rows from pr_latency table
- `load_issue_response(repos)` 
  → returns rows from issue_response table
- `load_bot_activity(repos)` 
  → returns rows from bot_activity table
- `load_bus_factor(repos)` 
  → returns rows from bus_factor table
- `load_contributor_network(repo)` 
  → returns edges from contributor_network table

---

### `src/analytics.py`


This file contains helper functions that compute 
derived metrics from raw DataFrames. These functions 
are called by the callbacks before plotting.

Functions to write:
- `compute_monthly_activity(df)` 
  → group events by repo and month, return counts
- `compute_ecosystem_monthly(df)` 
  → group events by ecosystem and month, return counts
- `compute_health_summary(repos, pr_df, issue_df, bot_df, bf_df)` 
  → compute one-row-per-repo summary table for dashboard
- `get_pr_stage_counts(df)` 
  → count PRs at each stage (opened, merged, closed) for Sankey

---

### `app/components/layout.py`


This file defines the visual structure of the entire 
page. Think of it as the HTML skeleton.

What to write:
- `create_filters()` function
  → Returns the top filter bar with repo dropdown, 
    ecosystem dropdown, date range slider, bot toggle
- `create_panels()` function  
  → Returns the six chart panels arranged in a 3-row 
    2-column grid. Each panel has a title and a 
    `dcc.Graph` with an id that callbacks will target.

Chart IDs that must match callbacks exactly:
- `streamgraph`
- `network-graph`
- `pr-sankey`
- `issue-heatmap`
- `bot-bar`
- `health-dashboard`

---

### `app/components/filters.py`


Small helper functions for processing filter values.

What to write:
- `get_month_range(slider_values)` 
  → converts slider [0, 23] to ('2023-01', '2024-12')

---

### `app/callbacks/streamgraph_cb.py`


Visualization: Technology Adoption Trends  
Chart type: Stacked area chart (streamgraph)  
Why this chart: Shows how relative activity proportions 
shift across ecosystems over time — a line chart cannot 
show this clearly when multiple series are stacked.

What to write:
- One `@app.callback` that reads from repo-filter, 
  ecosystem-filter, month-slider, bot-toggle
- Calls `load_events()` then `compute_ecosystem_monthly()`
- Builds a `go.Scatter` with `stackgroup='one'` for each 
  ecosystem — one trace per ecosystem
- Returns the figure to the `streamgraph` output

---

### `app/callbacks/network_cb.py`


Visualization: Contributor Collaboration Network  
Chart type: Force-directed network graph  
Why this chart: Reveals contributor clusters and central 
nodes organically — no table or bar chart can show network 
structure.

What to write:
- One `@app.callback` that reads from repo-filter
- Calls `load_contributor_network(repo)` for the first 
  selected repo
- Uses NetworkX to compute node positions 
  (`nx.spring_layout`)
- Builds a plotly figure with edges as `go.Scatter` lines 
  and nodes as `go.Scatter` markers
- Node size = how many edges (degree centrality)
- Node color = red if bus_factor risk, green otherwise
- Returns figure to `network-graph` output

---

### `app/callbacks/sankey_cb.py`


Visualization: PR Lifecycle and Review Latency  
Chart type: Sankey diagram + box plots  
Why this chart: Sankey shows where PRs drop off or stall 
at each stage — something a histogram alone cannot show.

What to write:
- One `@app.callback` reading repo-filter, month-slider, 
  bot-toggle
- Calls `load_events()` then `get_pr_stage_counts()`
- Builds `go.Sankey` with three nodes:
  - Opened → Merged
  - Opened → Closed Without Merge
- Also add a box plot of merge latency from 
  `load_pr_latency()` as a second subplot
- Returns figure to `pr-sankey` output

---

### `app/callbacks/heatmap_cb.py`


Visualization: Issue Responsiveness Calendar Heatmap  
Chart type: Calendar heatmap  
Why this chart: Gaps in daily activity immediately signal 
maintainer inactivity — a line chart would hide these gaps.

What to write:
- One `@app.callback` reading repo-filter, month-slider
- Calls `load_events()`, filters to IssuesEvent and 
  IssueCommentEvent only
- Groups by date to get daily counts
- Builds a `go.Heatmap` where:
  - x = week of year
  - y = day of week (Mon-Sun)
  - z = number of issue events that day
- Returns figure to `issue-heatmap` output

---

### `app/callbacks/bot_bar_cb.py`


Visualization: Bot vs Human Activity  
Chart type: Stacked bar chart  
Why this chart: Shows the exact split of automated vs 
real human activity per repo — critical for understanding 
whether activity metrics are honest.

What to write:
- One `@app.callback` reading repo-filter, month-slider
- Calls `load_bot_activity(repos)`
- Aggregates bot_events and human_events per repo
- Builds `go.Bar` with two traces — one for human 
  (blue), one for bot (red) — with `barmode='stack'`
- Returns figure to `bot-bar` output

---

### `app/callbacks/dashboard_cb.py`


Visualization: Repository Health Summary Dashboard  
Chart type: Radar Chart (Spider Chart)  
Why this chart: Synthesizes all metrics into one 
comparable view so users can evaluate repos side by 
side in seconds. A radar chart allows visualizing multiple 
metrics with different scales by normalizing them to a common scale, making it easy to compare repo health at a glance.

Build this LAST — it depends on all other features 
being ready in the database.

What to write:
- One `@app.callback` reading repo-filter
- Calls `load_pr_latency()`, `load_issue_response()`, 
  `load_bot_activity()`, `load_bus_factor()`
- Calls `compute_health_summary()` from analytics.py
- Normalizes metric values to 0-100 scale for plotting
- Builds a `go.Scatterpolar` (Radar chart) per repo with:
  - Median merge time
  - Median issue response time  
  - Bus factor score
  - Bot activity percentage
- Tooltips display the original raw values
- Returns figure to `health-dashboard` output

---

### `app/app.py`


This is the entry point. It should be short and clean.

What to write:
- Initialize the Dash app
- Import layout functions from components/layout.py
- Set `app.layout` using `create_filters()` and 
  `create_panels()`
- Import and call `register(app)` from every callback file
- `if __name__ == '__main__': app.run(debug=True)`

---

### `visualizations/`
**Owner: Everyone**

Put EDA plots and screenshots here as the project progresses.

What goes here:
- EDA plots (event distribution, monthly trends, bot 
  percentages) as PNG files
- Screenshots of the working app panels once built
- These will be used in the final report

---



## 11. Understanding globals.py and data_loader.py

These two files are the foundation of the entire app.
Every visualization file depends on them.
Nobody should need to touch these files once they are written.
Just import from them and use the functions.

---

### `app/globals.py` — What it does

This file runs once when the app starts.
It sets up three things that every other file needs:

**1. The path to the database**
It figures out where `github_analytics.db` is on your laptop
automatically, so you never have to hardcode a path.

**2. A function to connect to the database**
```python
get_connection()
```
Call this whenever you need to query the main events table.
It returns a SQLite connection. Always close it after use.

**3. Three shared lists loaded at startup**
```python
REPOS    # list of all 30 repo names
ECOSYSTEMS  # ['Frontend', 'ML/Data', 'Backend/DevOps']
MONTHS   # ['2023-01', '2023-02', ... '2024-12']
```
These are used by the filter dropdowns and date slider
in the app. They are loaded once and reused everywhere.

**How to use it in your file:**
```python
from app.globals import REPOS, ECOSYSTEMS, MONTHS, get_connection
```

---

### `src/data_loader.py` — What it does

This file has all the functions that fetch data.
No other file should write SQL or read CSVs directly.
You just call the function and get a clean DataFrame back.

Think of it like a menu — you order what you want
and get it served to you ready to use.

---

### The 6 functions and what they return

---

**1. load_events()**

Queries the main events table from the SQLite database.
This is the raw GitHub activity data — 3.4 million rows.
You will rarely need all of it — always pass filters.

```python
from src.data_loader import load_events

# Example — get only React and Vue events, no bots
df = load_events(
    repos=['facebook/react', 'vuejs/vue'],
    start_month='2023-01',
    end_month='2023-12',
    include_bots=False
)
```

Parameters you can pass:
| Parameter | What it does | Example |
|-----------|-------------|---------|
| repos | filter to specific repos | ['facebook/react'] |
| ecosystem | filter to one ecosystem | 'Frontend' |
| start_month | events from this month | '2023-06' |
| end_month | events until this month | '2024-06' |
| include_bots | include bot events or not | False |

Returns a DataFrame with all 10 columns from the events table.

---

**2. load_pr_latency()**

Reads from `features/pr_latency.csv`
Contains how long each PR took to get merged.

```python
from src.data_loader import load_pr_latency

df = load_pr_latency(repos=['facebook/react'])
```

Columns you get back:
| Column | Meaning |
|--------|---------|
| repo | repository name |
| pr_or_issue_number | PR number |
| opened_at | when the PR was opened |
| merged_at | when the PR was merged |
| latency_hours | how many hours it took to merge |
| month | which month this happened in |

Used by: PR Sankey chart, Health Dashboard

---

**3. load_issue_response()**

Reads from `features/issue_response.csv`
Contains how long each issue waited before getting
its first response.

```python
from src.data_loader import load_issue_response

df = load_issue_response(repos=['pytorch/pytorch'])
```

Columns you get back:
| Column | Meaning |
|--------|---------|
| repo | repository name |
| issue_number | issue number |
| opened_at | when issue was opened |
| first_comment_at | when first comment arrived |
| response_hours | how many hours until first response |
| has_response | True if someone responded |
| year_month | month of the issue |

Used by: Issue Heatmap, Health Dashboard

---

**4. load_bot_activity()**

Reads from `features/bot_activity.csv`
Contains monthly breakdown of bot vs human events
per repository.

```python
from src.data_loader import load_bot_activity

df = load_bot_activity(repos=['kubernetes/kubernetes'])
```

Columns you get back:
| Column | Meaning |
|--------|---------|
| repo | repository name |
| ecosystem | which ecosystem |
| year_month | the month |
| is_bot | 0 = human, 1 = bot |
| event_count | number of events that month |

Used by: Bot vs Human Bar Chart, Health Dashboard

---

**5. load_bus_factor()**

Reads from `features/bus_factor.csv`
Contains the bus factor score for each repository.

```python
from src.data_loader import load_bus_factor

df = load_bus_factor()
# or filter to specific repos
df = load_bus_factor(repos=['tiangolo/fastapi'])
```

Columns you get back:
| Column | Meaning |
|--------|---------|
| repo | repository name |
| bus_factor | how many people control 50% of activity |
| total_contributors | total unique human contributors |
| total_activity | total human push/PR events |

Key finding from our data:
- fastapi, flask, keras all have bus_factor = 1
  meaning one person holds each project together
- kubernetes has bus_factor = 56
  meaning contribution is very well distributed

Used by: Contributor Network, Health Dashboard

---

**6. load_contributor_network()**

Reads from `features/contributor_network.csv`
Contains pairs of contributors who worked together,
and how many times they collaborated.

Note: takes a single repo name, not a list.

```python
from src.data_loader import load_contributor_network

df = load_contributor_network('facebook/react')
```

Columns you get back:
| Column | Meaning |
|--------|---------|
| repo | repository name |
| source | first contributor username |
| target | second contributor username |
| weight | how many times they collaborated |
| source_centrality | how central source is in network |
| target_centrality | how central target is in network |

Returns only top 500 edges by weight for performance.

Used by: Contributor Network Graph

---

### Quick Reference — Which function does each chart need?

| Chart | Functions needed |
|-------|-----------------|
| Streamgraph | load_events() |
| Contributor Network | load_contributor_network(), load_bus_factor() |
| PR Sankey | load_events(), load_pr_latency() |
| Issue Heatmap | load_events(), load_issue_response() |
| Bot Bar Chart | load_bot_activity() |
| Health Dashboard | load_pr_latency(), load_issue_response(), load_bot_activity(), load_bus_factor() |

---

### How to verify everything works on your laptop

Run this command from the root project folder:
```bash
python3 src/data_loader.py
```

You should see data printed for all 6 functions.
If you see data — you are ready to start building your chart.
If you see an error — check that github_analytics.db is in 
the root folder and the feature CSVs are in features/ folder.



## 12. Understanding analytics.py and filters.py

These two files contain helper functions that process 
data before it gets passed to the visualization charts.
They sit between data_loader.py and the callback files.

The flow is:
data_loader.py → analytics.py → callback files → chart

---

### `src/analytics.py` — What it does

This file takes raw DataFrames and computes something 
useful from them. Think of it like a calculator —
you give it data, it gives you processed results.

It has 5 functions, each used by a specific chart.

---

**Function 1 — compute_monthly_activity()**

Used by: streamgraph chart

Takes the raw events data and counts how many events 
happened per repo per month.

Example of what you give it:
repo            | date       | event_type
facebook/react  | 2023-01-05 | PushEvent
pytorch/pytorch | 2023-01-07 | IssuesEvent

Example of what you get back:
year_month | repo            | event_count
2023-01    | facebook/react  | 2528
2023-01    | pytorch/pytorch | 15360
2023-02    | facebook/react  | 2945

Why we need this: the streamgraph needs monthly totals 
per repo to draw the stacked area chart. The raw data 
has one row per event which is 3.4 million rows —
we need to summarize it first.

---

**Function 2 — compute_ecosystem_monthly()**

Used by: streamgraph chart

Same as above but groups by ecosystem instead of 
individual repo. So instead of seeing facebook/react 
and vuejs/vue separately, you see "Frontend" as one 
combined number.

Example of what you get back:
year_month | ecosystem | event_count
2023-01    | Frontend  | 2528
2023-01    | ML/Data   | 15360
2023-02    | Frontend  | 2945

Why we need this: when the user selects "show by 
ecosystem" instead of individual repos, this function 
provides the right aggregation.

---

**Function 3 — get_pr_stage_counts()**

Used by: PR Sankey chart

Counts how many PRs are at each stage of their 
lifecycle. Three stages: opened, merged, and closed 
without merging.

Example of what you get back:
```python
{
    'opened': 4074,
    'merged': 293,
    'closed_without_merge': 927
}
```

What this means in plain English:
- 4074 PRs were opened in the selected time period
- 293 of them got merged successfully
- 927 of them were closed without being merged
- The rest are still open

Why we need this: the Sankey diagram needs these 
three numbers to draw the flow from opened to 
merged or closed.

Important finding: only 293 out of 4074 PRs merged 
in a 3 month window for react and pytorch — most 
PRs either stay open or get closed without merging.

---

**Function 4 — compute_daily_issue_activity()**

Used by: Issue Heatmap chart

Counts how many issue events happened each day.
Also computes the week number and day of week for 
each date so the calendar heatmap can be drawn.

Example of what you get back:
date       | count | week | day_of_week | year
2023-01-01 | 35    | 52   | 6           | 2023
2023-01-02 | 104   | 1    | 0           | 2023
2023-01-03 | 255   | 1    | 1           | 2023

Why we need this: the calendar heatmap needs one 
count per day to color each cell. Green = active day, 
white/empty = no activity that day.
Gaps in the heatmap immediately show when maintainers 
went quiet.

---

**Function 5 — compute_health_summary()**

Used by: Health Dashboard

This is the most important function. It takes data 
from all four feature CSVs and computes a single 
summary row for each selected repository.

What you give it:
- list of repos
- pr_latency DataFrame
- issue_response DataFrame  
- bot_activity DataFrame
- bus_factor DataFrame

What you get back:
repo            | median_merge | median_response | bus_factor | bot_pct
facebook/react  | 15.4 hrs     | 12.8 hrs        | 5          | 12.3%
pytorch/pytorch | 19.4 hrs     | 16.4 hrs        | 29         | 34.6%

Why we need this: the health dashboard shows all 
repos side by side with their key metrics. This 
function does all the computation so the dashboard 
callback just needs to display the table.

What these numbers mean for our repos:
- facebook/react: bus_factor 5, 12.3% bots — 
  small core team, mostly real humans working
- pytorch/pytorch: bus_factor 29, 34.6% bots — 
  larger distributed team but heavy automation

---

### `app/components/filters.py` — What it does

This is the simplest file in the whole project.
It has one function that every callback file uses.

The date range in our app is a slider with positions 
0 to 23 (one position per month from Jan 2023 to 
Dec 2024). When a user moves the slider, the callback 
gets numbers like [3, 18] — but the database needs 
actual month strings like '2023-04' and '2024-07'.

This function does that conversion.

**Function — get_month_range()**

```python
from app.components.filters import get_month_range

start, end = get_month_range([0, 23])
# start = '2023-01'
# end   = '2024-12'

start, end = get_month_range([3, 18])
# start = '2023-04'
# end   = '2024-07'
```

Why we put this in a separate file: every single 
callback needs to convert slider values to month 
strings. Instead of writing the same code 6 times 
in 6 different files, we write it once here and 
everyone imports it.

---

### How these files connect to everything else
User moves date slider
↓
Callback receives [3, 18]
↓
filters.py converts to ('2023-04', '2024-07')
↓
data_loader.py queries database with those months
↓
analytics.py computes monthly counts / stage counts / etc
↓
Callback builds the chart with processed data
↓
Chart updates on screen
### Final deliverables
- Working web application
- Project report in LaTeX
- GitHub repository with all code
- Live demo during final exam week

---

## 13. Visualization Files — What Each One Does

This section explains every visualization file in simple 
language so every teammate understands what was built, 
how it works, and what data it uses.

---

### How Visualizations Work in Our App

The flow for every chart is the same:
User changes a filter (repo, date, ecosystem)
↓
Dash automatically calls the callback function
↓
Callback fetches data using data_loader.py
↓
Callback builds a plotly figure
↓
Chart updates on screen instantly

Every callback file has one function called register(app).
This function contains the @app.callback decorator which 
tells Dash which inputs to listen to and which chart to update.

---

### `app/callbacks/bot_bar_cb.py`
**Chart: Bot vs Human Activity**
**Assigned to: [Name]**

#### What question does it answer?
How much of each repository's activity is real humans 
vs automated bots? Is the high activity we see in 
pytorch or kubernetes actually real developer work, 
or mostly CI bots and merge bots?

#### What data does it use?
Reads from `features/bot_activity.csv` using 
`load_bot_activity()` from data_loader.py.

The CSV has one row per repo per month per type (bot/human):
repo            | year_month | is_bot | event_count
facebook/react  | 2023-01    | 0      | 2200
facebook/react  | 2023-01    | 1      | 320
pytorch/pytorch | 2023-01    | 0      | 9800
pytorch/pytorch | 2023-01    | 1      | 5500

#### How it works step by step
1. Gets selected repos and month range from filters
2. Loads bot_activity.csv filtered to selected repos
3. Filters rows to only the selected month range
4. Groups by repo and is_bot, sums event counts
5. Pivots so each repo has one human count and one bot count
6. Builds a stacked bar chart — blue for human, red for bot

#### Why stacked bar chart?
A stacked bar shows both the total height (overall activity) 
and the split (how much is bot vs human) at the same time. 
A pie chart would only show proportions without showing 
which repo has more total activity.

#### Key finding from our data
- kubernetes/kubernetes: bots outnumber humans 
  8954 bot events vs 6826 human events in Jan 2023
- facebook/react: 12.3% bot activity — mostly real humans
- pytorch/pytorch: 34.6% bot activity — heavy automation

#### Inputs it listens to
- `repo-filter` dropdown
- `month-slider` date range

---

### `app/callbacks/heatmap_cb.py`
**Chart: Issue Responsiveness Calendar Heatmap**
**Assigned to: [Name]**

#### What question does it answer?
Is this project actively responding to issues? When did 
maintainers go quiet? Are there obvious gaps in activity 
that suggest the project slowed down or was abandoned?

#### What data does it use?
Reads from the main database using `load_events()` from `data_loader.py`.
Passes the events to `compute_daily_issue_activity()` in `analytics.py`.

#### How it works step by step
1. Gets selected repos and month range from filters
2. Loads raw issue events (IssuesEvent and IssueCommentEvent)
3. Computes daily issue counts using the analytics engine
4. Fills in missing dates with 0 so the calendar is complete
5. Computes week_index and day_of_week for each date
6. Builds a heatmap where:
   - x axis = week number
   - y axis = day of week (Mon to Sun)
   - color = number of issues that day (darker = more)

#### Why calendar heatmap?
A line chart would show a wiggly line that makes gaps 
hard to spot. A calendar heatmap makes silence immediately 
obvious — you literally see white/empty squares where 
maintainers went quiet. This is the most intuitive way 
to show activity patterns over time.

#### Why not a bar chart?
A bar chart per day over 2 years would be 730 bars — 
completely unreadable. The calendar layout compresses 
2 years into a compact visual that fits on screen.

#### Inputs it listens to
- `repo-filter` dropdown
- `month-slider` date range

---

### `app/callbacks/sankey_cb.py`
**Chart: PR Lifecycle and Review Latency**
**Assigned to: [Name]**

#### What question does it answer?
Where do pull requests end up? How many get merged vs 
closed without merging? And how long does it take for 
a PR to get merged in each repository?

#### What data does it use?
Reads from the main database using `load_events()` from `data_loader.py` for the PR lifecycle counts, and `features/pr_latency.csv` using `load_pr_latency()` for the merge latency box plot.
It computes the exact lifecycle counts using `get_pr_stage_counts()` in `analytics.py`.

#### How it works step by step
1. Gets selected repos, month range, and bot toggle from filters
2. Loads raw PR events and latency stats
3. Computes the exact number of opened, merged, and closed-without-merge PRs
4. Builds two charts side by side:
   - Left: Sankey diagram showing PR flow
   - Right: Box plot showing merge time distribution

#### Why Sankey diagram?
The Sankey makes it immediately clear how many PRs 
enter the system (opened) and where they end up 
(merged or closed). The width of each flow line is 
proportional to the number of PRs. A bar chart cannot 
show this directional flow clearly.

#### Why box plot alongside it?
The box plot shows the distribution of merge times —
the median, the spread, and the outliers. It answers 
"most PRs merge in X hours but some take weeks". A 
single average number would hide this distribution.

#### Inputs it listens to
- `repo-filter` dropdown
- `month-slider` date range

---

### `app/callbacks/streamgraph_cb.py`
**Chart: Technology Adoption Streamgraph**
**Assigned to: [Name]**

#### What question does it answer?
Which technology ecosystems are growing or declining 
in developer activity over time? Is ML/Data becoming 
more dominant? Is Frontend activity stable or shrinking?

#### What data does it use?
Reads from the main database using `load_events()` from `data_loader.py`.
It aggregates the events by ecosystem and month using `compute_ecosystem_monthly()` in `analytics.py`.

#### How it works step by step
1. Gets selected repos, ecosystem, date range, and bot toggle from filters
2. Loads all relevant events from the database
3. Aggregates event counts by year_month and ecosystem
4. Pivots the data so each ecosystem is a column
5. Computes a symmetric baseline (centers the streams 
   around zero so it looks like a proper streamgraph)
6. Adds one filled area trace per ecosystem

#### Why streamgraph?
A regular stacked area chart starts all stacks from 
zero at the bottom. A streamgraph centers the stacks 
symmetrically which makes relative growth and decline 
much easier to see. Rising ecosystems visually expand 
outward while shrinking ones compress inward.

#### Why not a line chart?
A line chart with 3 lines would show absolute numbers 
but not relative proportions. The streamgraph shows 
both — how each ecosystem's share of total activity 
changes month by month.

#### Why not pie chart?
A pie chart is a snapshot in time. Our data spans 
24 months — you need a time-based chart to show trends.

#### Inputs it listens to
- `repo-filter` dropdown
- `ecosystem-filter` dropdown

---

### `app/callbacks/network_cb.py`
**Chart: Contributor Collaboration Network**
**Assigned to: [Name]**

#### What question does it answer?
Who are the key contributors in a repository? Who 
collaborates with whom? Is the project dangerously 
concentrated around a few central people? What is 
the bus factor risk?

#### What data does it use?
Two data sources:

1. `features/contributor_network.csv` using 
   `load_contributor_network(repo)`
   Contains pairs of contributors who commented on 
   the same PR, with a weight for how many times they 
   collaborated:
source    | target      | weight | source_centrality | target_centrality
eps1lon   | rickhanlonii| 27     | 0.279             | 0.177
eps1lon   | sebmarkbage | 26     | 0.279             | 0.140

2. `features/bus_factor.csv` using `load_bus_factor()`
   For the summary text showing bus factor score.

#### How it works step by step
1. User selects ONE repo from the network-specific dropdown
2. Loads contributor_network.csv for that repo 
   (top 500 edges by weight)
3. Builds a centrality map — for each contributor, 
   takes the max centrality value across all their edges
4. Marks contributors in the top 50% of centrality 
   as top-contributor (shown in red in the graph)
5. Creates Cytoscape elements — nodes for contributors, 
   edges for collaborations
6. Shows bus factor score as text above the graph

#### Why force-directed network (Cytoscape)?
A network graph is the only chart type that shows 
relationships between people. No table, bar chart, 
or heatmap can show who works with whom. The 
force-directed layout naturally clusters people 
who collaborate frequently — they are pulled 
together by their shared edges.

#### Why separate repo dropdown?
The network is inherently a single-repo visualization.
Showing two repos' networks on the same graph would 
be meaningless — contributors from different repos 
don't collaborate with each other. So instead of 
using the global multi-repo filter, it has its own 
single-repo selector.

#### Node colors
- Blue nodes: regular contributors
- Red nodes: top contributors (top 50% by centrality)
  — these are the people whose departure would hurt 
  the project most (related to bus factor)

#### Edge thickness
Thicker edges = more collaboration between those two 
people. If two contributors reviewed each other's 
PRs 27 times, their edge is thicker than two people 
who co-commented only twice.

#### Inputs it listens to
- `network-repo-filter` dropdown (separate from global filter)

---

### `app/components/layout.py`
**Assigned to: [Name]**

#### What does this file do?
This file defines the visual structure of the entire 
page. It does not contain any data or chart logic — 
it just arranges elements on the page.

Think of it as the HTML skeleton of the app. Every 
chart panel, every filter, every heading is defined 
here.

It has two functions:

**create_filters()**
Creates the global filter bar at the top of the page 
with four controls:

| Control | ID | What it does |
|---------|-----|-------------|
| Repo dropdown | `repo-filter` | Select multiple repos |
| Ecosystem dropdown | `ecosystem-filter` | Filter to one ecosystem |
| Date slider | `month-slider` | Select date range |
| Bot toggle | `bot-toggle` | Include/exclude bots |

**create_panels()**
Creates the six visualization panels in a 3-row 
2-column grid:

| Row | Left Panel | Right Panel |
|-----|-----------|-------------|
| Row 1 | Streamgraph (`streamgraph`) | Network (`contributor-network`) |
| Row 2 | PR Sankey (`pr-sankey`) | Issue Heatmap (`issue-heatmap`) |
| Row 3 | Bot Bar (`bot-bar`) | Health Dashboard (`health-dashboard`) |

#### Important — IDs must match exactly
The IDs in layout.py must exactly match the Output 
IDs in every callback file. If layout.py says 
`id='bot-bar'` then bot_bar_cb.py must say 
`Output('bot-bar', 'figure')`. Any mismatch causes 
the app to crash.

#### Special case — Network panel
The network panel is different from the other five:
- Uses `cyto.Cytoscape` instead of `dcc.Graph`
- Has its own separate dropdown `network-repo-filter`
- Has a text div `network-bus-factor-info` for 
  showing bus factor score
- Uses `dash_cytoscape` library which must be 
  installed separately:
```bash
  pip3 install dash-cytoscape
```

#### Panel IDs reference

| Panel | Component type | ID |
|-------|---------------|-----|
| Streamgraph | dcc.Graph | `streamgraph` |
| Network graph | cyto.Cytoscape | `contributor-network` |
| Network repo selector | dcc.Dropdown | `network-repo-filter` |
| Bus factor text | html.Div | `network-bus-factor-info` |
| PR Sankey | dcc.Graph | `pr-sankey` |
| Issue Heatmap | dcc.Graph | `issue-heatmap` |
| Bot Bar | dcc.Graph | `bot-bar` |
| Health Dashboard | dcc.Graph | `health-dashboard` |

---

### `app/app.py`
**Assigned to: [Name]**

#### What does this file do?
This is the entry point of the entire application. It brings everything together, connecting the visual layout (`components/layout.py`) with all the interactive logic (`callbacks/*.py`), and starts the local web server.

#### How it works step by step
1. Handles complex Python import paths to ensure all modules (`src`, `app`) can discover each other no matter where the script is run from.
2. Initializes the `dash.Dash` application instance.
3. Sets `app.layout` by calling `create_filters()` and `create_panels()` to construct the UI skeleton.
4. Registers all the interactive callbacks by importing each `*_cb.py` file and calling its `register(app)` function.
5. Starts the development server using `app.run(debug=True)` when run directly.

#### The "ModuleNotFoundError" Bug (and how we fixed it)
During development, we encountered a tricky `ModuleNotFoundError: No module named 'app.components'; 'app' is not a package` error when running `python3 app/app.py`. 

This happened because of **Name Shadowing**: the folder was named `app/` and the script was named `app.py`. When Python runs a script, it automatically adds the script's folder to the *front* of its search path (`sys.path[0]`). So when we wrote `from app.components...`, Python looked inside `app.py` (thinking it was the `app` package) and crashed because a script doesn't have a `.components` attribute!

**How we fixed it**: We added code at the very top of `app.py` to actively detect and remove the script's directory from `sys.path`, forcing Python to look at the root directory where it could properly discover the `app/` folder as a real package.

---

## 14. App User Guide & Functionality Overview

This section is a complete, high-level summary of what the final interactive application is, what controls are available, and what each part of the dashboard actually shows to the end-user.

### 🎛️ The Global Filters

At the very top of the dashboard is the control panel. Changing any of these filters instantly updates the entire dashboard (except the network graph, which has its own specific dropdown).

1. **Repository Filter**: A multi-select dropdown containing all 30 tracked repositories. You can select one, several, or all of them to compare them side-by-side. 
2. **Ecosystem Filter**: A dropdown that lets you quickly filter the entire dataset down to just one category: `Frontend`, `ML/Data`, or `Backend/DevOps`.
3. **Date Range Slider**: A two-handled slider covering Jan 2023 through Dec 2024. Sliding the handles restricts all data (PRs, issues, commits) to that specific time window.
4. **Include Bot Activity Toggle**: A simple ON/OFF switch. When turned ON, automated bots (like `dependabot` or `pytorchmergebot`) are included in the activity counts. When OFF, the dashboard filters out bots, showing *only* real human developer activity.

---

### 📊 The Six Visualizations

The dashboard is laid out in a 3-row, 2-column grid. Each panel is designed to answer a specific question about repository health.

#### 1. Technology Adoption Streamgraph (Top Left)
- **What it is**: A flowing, centered area chart ("streamgraph") showing activity volume over time.
- **What it shows**: It aggregates total human activity grouped by Ecosystem. As time progresses from left to right, you can see which ecosystems are expanding (getting thicker) and which are shrinking (getting thinner).
- **Why it matters**: It reveals macro-level trends in the developer community. For example, if ML/Data projects see a massive swell in late 2023 compared to Frontend, this streamgraph makes that industry shift immediately visible.

#### 2. Contributor Collaboration Network (Top Right)
- **What it is**: A force-directed node graph.
- **What it shows**: The nodes (dots) are human developers, and the edges (lines connecting them) represent two people collaborating on the same Pull Request or Issue.
- **Special Controls**: Because a network is specific to a single community, this panel has its own standalone dropdown to select exactly *one* repository.
- **Why it matters**: It exposes the hidden social structure of the project. A healthy project looks like a dense spiderweb (many people collaborating). An at-risk project looks like a star or wheel (hundreds of people only interacting with one central maintainer). This panel also explicitly calculates and displays the **Bus Factor** (how many people control 50% of the project).

#### 3. PR Lifecycle & Latency (Middle Left)
- **What it is**: A split view containing a Sankey flow diagram on the left, and a Box Plot on the right.
- **What it shows**: 
  - *The Sankey*: Shows the flow of Pull Requests. It visually splits the total number of "Opened" PRs into those that successfully "Merged" versus those that were "Closed without Merge".
  - *The Box Plot*: Shows the statistical distribution of how many hours it takes for a PR to get merged.
- **Why it matters**: It tells you how welcoming a project is to contributors. If 80% of PRs are closed without merging, or if the median merge time is 3 weeks, developers will know not to waste their time submitting code to that project.

#### 4. Issue Responsiveness Calendar Heatmap (Middle Right)
- **What it is**: A GitHub-style calendar grid where each square represents a single day in the year.
- **What it shows**: The color intensity of each square represents the number of Issue events (opened, commented, closed) that happened on that specific day. 
- **Why it matters**: It is the best visual tool for spotting "ghosting" or maintainer burnout. If a calendar has consistent dark blocks, the project is highly active. If there are massive stretches of blank white space spanning weeks at a time, it means the maintainers went completely unresponsive.

#### 5. Bot vs. Human Activity Breakdown (Bottom Left)
- **What it is**: A stacked bar chart comparing the selected repositories.
- **What it shows**: For each repository, it stacks the volume of *Human* events (blue) on top of *Automated Bot* events (red).
- **Why it matters**: Open-source metrics can easily be faked or skewed by automation. A project might boast "100,000 events", but this chart will instantly reveal if 90,000 of those events were generated by a CI bot endlessly opening and closing test issues.

#### 6. Repository Health Summary Dashboard (Bottom Right)
- **What it is**: A clean, tabular scorecard.
- **What it shows**: It aggregates all the most critical metrics from the other panels into one scannable list. For each selected repository, it shows:
  - Median Merge Time (hrs)
  - Median Issue Response Time (hrs)
  - Bus Factor
  - Bot Activity %
- **Why it matters**: It serves as the final "Executive Summary". After exploring the nuanced charts, a user can look at this table to quickly rank and compare the final health scores of the repositories they are evaluating.

---
*Last updated: July 2026*  
*Update the status table whenever a task is completed*

---

## 10. Dashboard App Architecture (`app/app.py`)

The main entry point of our dashboard is `app/app.py`. It initializes the Plotly Dash application and ties everything together.
- It loads global configurations and data structures from `app/globals.py`.
- It defines the main web page layout by importing `create_filters()` and `create_panels()` from `app/components/layout.py`.
- It connects the interactive logic by registering the callback functions from `app/callbacks/`.
- It runs the local Flask server to host the dashboard on port 8050.

---

## 11. Performance Optimizations & Filtering

### The Problem
Initially, the dashboard was slow because every time a filter was changed, the app would query the SQLite database and re-calculate all metrics from millions of rows. Additionally, some charts were entirely static and did not respond to the date range slider or bot toggle.

### What We Fixed (And Removed Old Approaches)
We abandoned the idea of changing the timeline slider into dropdowns, keeping the smooth slider interaction intact. Instead, we implemented internal optimizations:
1. **Dynamic Data Functions**: We updated `src/data_loader.py` to natively accept `start_month` and `end_month` parameters for all CSV data (like `pr_latency.csv`, `bot_activity.csv`), filtering them efficiently in memory before they hit the chart callbacks.
2. **Instant Caching**: We wrapped all data loading functions with Python's `@lru_cache`. Now, when the user drags the slider, the data is loaded and filtered exactly once. All 6 charts then instantly retrieve the exact same pre-filtered dataset from memory, completely eliminating lag and redundant disk I/O.
3. **Dynamic Bus Factor**: We threw out the static `bus_factor.csv` entirely. We wrote `compute_dynamic_bus_factor` in `src/analytics.py` which calculates the bus factor instantly in-memory from the raw events data, making it perfectly responsive to the timeline slider and bot toggle.

---

## 12. App User Guide

Here is a clear explanation of how to use our interactive dashboard and what each component represents.

### The Filters (Top Bar)
- **Repositories**: Select one or multiple repositories to compare or aggregate their data.
- **Ecosystem**: Filter repositories by their domain (Frontend, ML/Data, Backend/DevOps).
- **Date Range Slider**: Drag the handles to select a specific time window (from Jan 2023 to Dec 2024). All charts instantly update to reflect only the data from this period.
- **Bots (Include/Exclude)**: Toggle to either hide or show automated bot activity. Excluding bots reveals the true human developer metrics.

### The Visualizations (6 Panels)
1. **Technology Adoption Trends (Streamgraph)**: Shows the relative activity volume of each ecosystem over time. Useful for identifying if a domain (like ML) is suddenly growing faster than others.
2. **Contributor Collaboration Network (Force-Directed Graph)**: Maps out who is talking to whom on PRs and issues. Nodes are contributors; lines are collaborations. Red nodes highlight critical "linchpin" developers (high bus factor risk).
3. **PR Lifecycle and Review Latency (Sankey & Box Plot)**: The Sankey diagram visually tracks the flow of Pull Requests from "Opened" to either "Merged" or "Closed without Merge". The accompanying Box Plot shows the distribution of hours it takes for PRs to get merged, identifying bottlenecks.
4. **Issue Responsiveness (Calendar Heatmap)**: Displays the daily volume of issues opened. Gaps (white squares) indicate days with zero activity, helping you spot maintainer burnout or abandoned periods.
5. **Bot vs Human Activity (Stacked Bar Chart)**: Compares the sheer volume of automated bot events against real human events across the selected repositories.
6. **Repository Health Dashboard (Table)**: A concise scorecard summarizing the median PR merge times, issue response times, bus factor, and bot percentage side-by-side.


## 13. Professor Feedback & Visual Refinements (Checkpoint 10 Updates)

Following feedback from the professor regarding HCI principles and data visualization best practices, we implemented several major refinements to the dashboard:

### 1. Shneiderman's Mantra (Overview first, zoom/filter, details-on-demand)
**The Problem:** The original dashboard required a lot of vertical scrolling, and showing 6 massive charts simultaneously made it hard to focus.
**The Fix:** We completely rebuilt the layout into a compact, single-viewport "Overview" grid. We added an "Expand" button to every single chart. When clicked, it opens a full-screen interactive Modal (using `modal_cb.py`), allowing the user to get "details-on-demand" without cluttering the main screen.

### 2. Miller's Law (7±2) & Chart Junk Prevention
**The Problem:** The global dropdown allowed users to select all 30 repositories at once, causing the charts to become an unreadable mess of overlapping colors and labels (chart junk).
**The Fix:** We implemented `apply_millers_law` in `analytics.py`. Now, if a user selects more than 7 repositories, the dashboard automatically preserves the top 7 and aggregates the rest into an "Other (aggregate)" bucket. This ensures the charts remain cognitively digestible.

### 3. Consistent Visual Encoding (Gestalt Principles)
**The Problem:** The Box Plot for PR latency was assigning a single generic blue color (`#1f77b4`) to every repository, completely violating consistent visual encoding because repositories had specific assigned colors in the Streamgraph and other charts. Furthermore, extreme outliers were causing hundreds of hover tooltips to overlap, making the chart unreadable.
**The Fix:** We refactored `sankey_cb.py` to use Plotly Express, ensuring each repository is automatically assigned a distinct and consistent color. We applied a logarithmic scale (`type='log'`) to the y-axis to handle extreme outliers gracefully, and we configured `hoveron='boxes'` so users get a clean, single summary tooltip instead of hundreds of overlapping labels.

### 4. Contributor Network "Hairball" Fix
**The Problem:** Combining multiple large repositories (like PyTorch and React) into the Cytoscape force-directed graph created a chaotic "hairball" where hundreds of text labels overlapped each other, hiding the true bus factor risk.
**The Fix:** We reduced the maximum edge count from 500 down to 150 to strip away noise. More importantly, we updated `modal_cb.py` to dynamically recalculate degree centrality when the modal opens. We used this to apply the `.top-contributor` CSS class to only the highest-centrality nodes. As a result, only the core maintainers are rendered as giant red nodes with text labels, while the hundreds of minor contributors are rendered as small, anonymous blue dots, instantly clarifying the network structure.
