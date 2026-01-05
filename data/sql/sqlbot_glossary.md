# Open-Detective: OpenDigger Business Semantics

## Table: open_digger_metrics
This table stores time-series metrics for open source repositories.

### Columns:
- `repo_name`: The full name of the GitHub repository (e.g., 'vuejs/core').
- `metric_type`: The type of metric being measured. Supported types:
    - `stars`: Monthly count of GitHub stars.
    - `activity`: A composite score of repository development activity.
    - `openrank`: The influence score of the project within the OSS ecosystem.
    - `bus_factor`: The minimum number of contributors who leave before a project stalls. (Lower means higher risk).
    - `issues_new`: Number of new issues opened during the month.
    - `issues_closed`: Number of issues resolved during the month.
- `month`: The time period in YYYY-MM format.
- `value`: The numerical value of the specific metric.

## Common Queries:
- "Which project has the highest risk?" -> Check for lowest `bus_factor`.
- "Analyze the growth of [repo]" -> Trend of `stars` over `month`.
- "Maintenance efficiency" -> Ratio of `issues_closed` / `issues_new`.
