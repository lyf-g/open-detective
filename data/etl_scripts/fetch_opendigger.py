import requests
import mysql.connector
import os
import json

# Configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "open_detective")

BASE_URL = "https://oss.x-lab.info/open_digger/github"
CONFIG_PATH = os.path.join(os.path.dirname(__file__), '../repos.json')

def get_db_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

def load_repos():
    try:
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"⚠️ Config file not found at {CONFIG_PATH}, utilizing defaults.")
        return ["vuejs/core"]

METRICS = ["stars", "activity", "openrank", "bus_factor", "issues_new", "issues_closed"]

def fetch_metric(repo, metric):
    url = f"{BASE_URL}/{repo}/{metric}.json"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"❌ Error fetching {url}: {e}")
    return None

def transform_and_load(repo, metric, data):
    if not data: return
    records = []
    for month, value in data.items():
        if not (len(month) == 7 and month[4] == '-'): continue
        records.append((repo, metric, month, float(value)))

    if not records: return

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Delete old data
        cursor.execute(
            "DELETE FROM open_digger_metrics WHERE repo_name = %s AND metric_type = %s",
            (repo, metric)
        )
        # MySQL use %s placeholder
        cursor.executemany(
            "INSERT INTO open_digger_metrics (repo_name, metric_type, month, value) VALUES (%s, %s, %s, %s)",
            records
        )
        conn.commit()
        print(f"✅ Saved {len(records)} records for {repo} - {metric}")
    finally:
        cursor.close()
        conn.close()

def run_etl():
    print("🚀 Starting OpenDigger MySQL ETL...")
    repos = load_repos()
    for repo in repos:
        for metric in METRICS:
            data = fetch_metric(repo, metric)
            if data:
                transform_and_load(repo, metric, data)
    print("🎉 ETL Complete!")

if __name__ == "__main__":
    run_etl()