-- Open-Detective Schema Definition for MySQL 8.0

CREATE TABLE IF NOT EXISTS open_digger_metrics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    repo_name VARCHAR(255) NOT NULL,
    metric_type VARCHAR(64) NOT NULL, -- e.g., 'stars', 'openrank', 'activity'
    month VARCHAR(7) NOT NULL,       -- Format: YYYY-MM
    value DOUBLE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_repo_metric (repo_name, metric_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    role VARCHAR(20) DEFAULT 'user'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;