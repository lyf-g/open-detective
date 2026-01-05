import mysql.connector
import os
import random

# Configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "open_detective")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), '../sql/schema.sql')

def get_db_connection(include_db=True):
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME if include_db else None
    )

def init_db():
    """Initialize the MySQL database with schema."""
    print(f"Initializing database {DB_NAME} at {DB_HOST}...")
    
    # Connect without DB to ensure it exists
    conn = get_db_connection(include_db=False)
    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
    cursor.close()
    conn.close()

    # Apply schema
    with get_db_connection() as conn:
        cursor = conn.cursor()
        with open(SCHEMA_PATH, 'r') as f:
            schema_sql = f.read()
        # Execute each statement separated by semicolon
        for statement in schema_sql.split(';'):
            if statement.strip():
                cursor.execute(statement)
        conn.commit()
    print("Database schema applied.")

def seed_data():
    """Seed the database with mock data for testing."""
    print("Seeding mock data...")
    repos = ['vuejs/core', 'fastapi/fastapi']
    metrics = ['stars', 'activity']
    months = [f'2023-{m:02d}' for m in range(1, 13)]

    data_to_insert = []
    for repo in repos:
        for month in months:
            data_to_insert.append((repo, 'stars', month, float(random.randint(1000, 5000))))
            data_to_insert.append((repo, 'activity', month, float(random.randint(50, 200))))

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM open_digger_metrics")
        cursor.executemany(
            "INSERT INTO open_digger_metrics (repo_name, metric_type, month, value) VALUES (%s, %s, %s, %s)",
            data_to_insert
        )
        conn.commit()
    print(f"Inserted {len(data_to_insert)} records.")

if __name__ == "__main__":
    try:
        init_db()
        seed_data()
        print("✅ MySQL Data setup complete.")
    except Exception as e:
        print(f"❌ Error: {e}")