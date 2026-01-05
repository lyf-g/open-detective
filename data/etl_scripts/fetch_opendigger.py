import requests
import sqlite3
import os
import json

# Configuration
DB_PATH = os.path.join(os.path.dirname(__file__), '../../open_detective.db')
BASE_URL = "https://oss.x-lab.info/open_digger/github"

# Target repositories to track (add more as needed)
TARGET_REPOS = [
    "vuejs/core",
    "facebook/react",
    "fastapi/fastapi",
    "tensorflow/tensorflow",
    "microsoft/vscode",
    "kubernetes/kubernetes"
]

METRICS = [
    "stars",
    "activity",
    "openrank"
]

def fetch_metric(repo, metric):
    """Fetch metric JSON from OpenDigger GitHub raw content."""
    url = f"{BASE_URL}/{repo}/{metric}.json"
    print(f"Fetching {metric} for {repo} from {url}...")
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"⚠️ Failed to fetch {url}: Status {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error fetching {url}: {e}")
        return None

def transform_and_load(repo, metric, data):
    """Parse OpenDigger JSON format and insert into DB."""
    if not data:
        return

    records = []
    
    # OpenDigger data format is typically: { "2023-01": 123, "2023-02": 456, ... }
    # Sometimes it's nested, but for stars/activity/openrank simple keys are YYYY-MM
    
    for month, value in data.items():
        # Simple validation for YYYY-MM format
        if not (len(month) == 7 and month[4] == '-'):
            continue
            
        records.append((repo, metric, month, value))

    if not records:
        return

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        # Remove old data for this repo+metric to avoid duplicates
        cursor.execute(
            "DELETE FROM open_digger_metrics WHERE repo_name = ? AND metric_type = ?",
            (repo, metric)
        )
        
        cursor.executemany(
            "INSERT INTO open_digger_metrics (repo_name, metric_type, month, value) VALUES (?, ?, ?, ?)",
            records
        )
        conn.commit()
    
    print(f"✅ Saved {len(records)} records for {repo} - {metric}")

def run_etl():
    print("🚀 Starting OpenDigger ETL...")
    
    # Ensure DB exists
    if not os.path.exists(DB_PATH):
        print("Database not found. Please run mock_data.py first to init schema.")
        return

    for repo in TARGET_REPOS:
        for metric in METRICS:
            data = fetch_metric(repo, metric)
            if data:
                transform_and_load(repo, metric, data)
    
    print("🎉 ETL Complete!")

if __name__ == "__main__":
    run_etl()
