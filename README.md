# GitHub Repository Health Analytics
### CS661: Big Data Visual Analytics

An interactive web-based visual analytics system that analyzes the health 
and collaboration patterns of open-source GitHub repositories. The system 
helps developers, engineering managers, and open-source maintainers 
understand project health by visualizing contributor activity, code review 
efficiency, issue responsiveness, and technology adoption trends.

---

## Project Structure

```text
GitHub-Health-Analytics/
├── app/
│   ├── app.py                  # Entry point of the Dash application
│   ├── globals.py              # Shared database connection and global constants
│   ├── callbacks/              # Chart callbacks for interactivity
│   │   ├── bot_bar_cb.py       # Bot vs Human activity bar chart callback
│   │   ├── dashboard_cb.py     # Health dashboard radar chart callback
│   │   ├── heatmap_cb.py       # Issue responsiveness calendar heatmap callback
│   │   ├── modal_cb.py         # Modal zoom expansion overlay callback
│   │   ├── network_cb.py       # Contributor network callback
│   │   ├── sankey_cb.py        # PR lifecycle Sankey and merge latency callback
│   │   └── streamgraph_cb.py   # Technology adoption trends streamgraph callback
│   └── components/             # Layout structure definitions
│       ├── filters.py          # Shared filters layout (top bar)
│       └── layout.py           # Main dashboard panels and modal layout
├── assets/
│   └── theme.css               # Styling definitions for light/dark themes
├── features/                   # Feature extraction scripts and precomputed CSV files
│   ├── bot_activity.csv / .py
│   ├── bus_factor.csv / .py
│   ├── contributor_network.csv / contributer_network.py
│   ├── issue_response.csv / .py
│   ├── pr_latency.csv / .py
│   └── feature_engineering.py  # Orchestrates all feature calculations
├── preprocessing/
│   └── clean_data.py           # Initial data cleaning and SQLite DB creation
├── src/                        # Core backend loaders and analysis helpers
│   ├── analytics.py            # Aggregations, calculations, and Miller's law logic
│   └── data_loader.py          # Cache-supported data load queries
├── requirements.txt
└── README.md
```

---

## Dataset

- **Source:** GH Archive (https://gharchive.org) via Google BigQuery
- **Size:** 485MB, 3.4 million rows
- **Period:** January 2023 – December 2024
- **Repositories:** 30 repos across 3 ecosystems
  - Frontend: React, Vue, Svelte, Angular, Next.js, Tailwind, Material-UI, Bootstrap, React Native, Flutter
  - ML/Data: PyTorch, TensorFlow, Keras, HuggingFace, DeepSpeed, Ray, scikit-learn, pandas, NumPy
  - Backend/DevOps: VSCode, Kubernetes, Go, Elasticsearch, Spark, Terraform, Ansible, FastAPI, Django, Flask, Docker Compose

> The dataset file (`gh_archive_data.csv`) and database (`github_analytics.db`) 
> are not included in this repository due to size limits.  
> Download from: [Google Drive Link](https://drive.google.com/file/d/1HWRU4NNOxjwpM3wobOcTc_8-sYgwZpFD/view?usp=sharing)

---

## Setup and Installation

### 1. Clone the repository
git clone https://github.com/virendrakala/GitHub-Health-Analytics-CS661-.git
cd GitHub-Health-Analytics-CS661

### 2. Install dependencies
pip3 install -r requirements.txt

### 3. Download the data
Download `gh_archive_data.csv` from the Google Drive link above and place 
it in the root project folder.

### 4. Run data cleaning
This will create the cleaned `github_analytics.db` SQLite database.
python3 preprocessing/clean_data.py
Expected output:
Loading CSV... this will take 1-2 minutes
Loaded. Rows: 3448426
Fixed 1970 dates
Bots flagged: 848909
Ecosystem nulls: 0
Saving to SQLite... this will take 2-3 minutes
ALL DONE
Database saved as github_analytics.db

### 5. Run feature engineering
python3 features/feature_engineering.py

### 6. Run the app
python3 app/app.py
Open your browser and go to: `http://127.0.0.1:8050`

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Data Extraction | Google BigQuery |
| Data Processing | Python, Pandas, NumPy, NetworkX |
| Database | SQLite |
| Visualization | Plotly, Dash, Dash-Cytoscape |

---

## Visualizations

1. **Technology Adoption Streamgraph** — Monthly activity volume trends across ecosystems or repositories.
2. **Contributor Collaboration Network** — Cytoscape-rendered force-directed collaboration graph displaying contributor relationships with bus-factor highlights.
3. **PR Lifecycle Sankey + Box Plots** — PR state flows (opened, reviewed, merged, closed) paired with logarithmic distribution box plots.
4. **Issue Responsiveness Heatmap** — Aligned calendar heatmap subplots displaying daily issue creation frequency for selected repositories.
5. **Bot vs Human Activity** — Stacked bar charts showing the proportion of automated vs human event actions.
6. **Repository Health Dashboard** — Comparative radar charts displaying normalized scores across PR latency, response times, bus factors, and bot percentages.

---
## Course Details

- **Course:** CS661 Big Data Visual Analytics
- **Instructor:** Prof. Soumya Dutta
- **Institute:** IIT Kanpur
- **Semester:** 2025-26
