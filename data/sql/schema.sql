-- Open-Detective Schema Definition
-- Database: SQLite (Development) / MySQL 8.0 (Production)

-- Table: open_digger_metrics (Example placeholder)
CREATE TABLE IF NOT EXISTS open_digger_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repo_name TEXT NOT NULL,
    metric_type TEXT NOT NULL, -- e.g., 'stars', 'openrank', 'activity'
    month TEXT NOT NULL,       -- Format: YYYY-MM
    value REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: users (Example placeholder)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    role TEXT DEFAULT 'user'
);
