import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "open_detective")

def run():
    print("🔄 Applying Session Schema Migration...")
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        cursor = conn.cursor()
        
        with open('data/sql/session_schema.sql', 'r') as f:
            sql_script = f.read()
        
        # Split by ; to execute multiple statements
        statements = sql_script.split(';')
        for stmt in statements:
            if stmt.strip():
                cursor.execute(stmt)
        
        conn.commit()
        cursor.close()
        conn.close()
        print("✅ Session Schema Applied Successfully!")
    except Exception as e:
        print(f"❌ Error applying schema: {e}")

if __name__ == "__main__":
    run()
