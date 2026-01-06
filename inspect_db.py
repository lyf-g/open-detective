import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "open_detective")

try:
    conn = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    cursor = conn.cursor()
    
    print("--- Inspecting 'open_digger_metrics' ---")
    
    # Check distinct repo_names
    cursor.execute("SELECT DISTINCT repo_name FROM open_digger_metrics")
    repos = cursor.fetchall()
    print("Repos in DB:", repos)
    
    # Check distinct metric_types
    cursor.execute("SELECT DISTINCT metric_type FROM open_digger_metrics")
    metrics = cursor.fetchall()
    print("Metrics in DB:", metrics)
    
    # Check a sample for facebook/react
    cursor.execute("SELECT * FROM open_digger_metrics WHERE repo_name LIKE '%react%' LIMIT 5")
    samples = cursor.fetchall()
    print("Sample React data:", samples)

    cursor.close()
    conn.close()

except Exception as e:
    print(f"Error: {e}")
