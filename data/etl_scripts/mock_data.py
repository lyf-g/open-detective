import sqlite3
import os
import random

# Configuration
DB_PATH = os.path.join(os.path.dirname(__file__), '../../open_detective.db')
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), '../sql/schema.sql')

def init_db():
    """Initialize the database with schema."""
    print(f"Initializing database at {DB_PATH}...")
    
    with sqlite3.connect(DB_PATH) as conn:
        with open(SCHEMA_PATH, 'r') as f:
            schema_sql = f.read()
        conn.executescript(schema_sql)
    print("Database schema applied.")

def seed_data():
    """Seed the database with mock OpenDigger data."""
    print("Seeding mock data...")
    
    repos = ['vuejs/core', 'fastapi/fastapi', 'tensorflow/tensorflow', 'facebook/react']
    metrics = ['stars', 'openrank', 'activity']
    months = [f'2023-{m:02d}' for m in range(1, 13)] # 2023-01 to 2023-12

    data_to_insert = []
    
    for repo in repos:
        base_stars = random.randint(1000, 5000)
        base_activity = random.randint(50, 200)
        
        for month in months:
            # Simulate growth/fluctuation
            stars = base_stars + random.randint(0, 500)
            activity = base_activity + random.randint(-20, 50)
            openrank = activity * 1.5 + random.randint(0, 10)
            
            data_to_insert.append((repo, 'stars', month, stars))
            data_to_insert.append((repo, 'activity', month, activity))
            data_to_insert.append((repo, 'openrank', month, openrank))
            
            # Cumulative growth for stars
            base_stars = stars

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        # Clear existing data to avoid duplicates on re-run
        cursor.execute("DELETE FROM open_digger_metrics")
        
        cursor.executemany(
            "INSERT INTO open_digger_metrics (repo_name, metric_type, month, value) VALUES (?, ?, ?, ?)",
            data_to_insert
        )
        conn.commit()
    
    print(f"Inserted {len(data_to_insert)} records.")

if __name__ == "__main__":
    try:
        init_db()
        seed_data()
        print("✅ Data setup complete.")
    except Exception as e:
        print(f"❌ Error: {e}")
