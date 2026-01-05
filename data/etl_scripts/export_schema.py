import sqlite3
import os

# Configuration
DB_PATH = os.path.join(os.path.dirname(__file__), '../../open_detective.db')
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), '../sql/current_schema.sql')

def export_schema():
    """Exports the DDL from the existing SQLite database."""
    print(f"Exporting schema from {DB_PATH}...")
    
    if not os.path.exists(DB_PATH):
        print("❌ Database not found.")
        return

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        # Get all table definitions
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        with open(OUTPUT_PATH, 'w') as f:
            f.write("-- Open-Detective Auto-Generated Schema for SQLBot\n\n")
            for table in tables:
                if table[0]:
                    f.write(table[0] + ";\n\n")
    
    print(f"✅ Schema exported to {OUTPUT_PATH}")

if __name__ == "__main__":
    export_schema()
