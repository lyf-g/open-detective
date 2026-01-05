# Open-Detective Architecture & Design

## 1. Project Overview
**Open-Detective** is an AI-powered Text-to-SQL application designed to investigate open source community health, focusing on fraud detection, contributor health, and compliance.

## 2. Technical Stack

### Backend
- **Framework**: FastAPI (Python)
- **Reasoning**: Native async support for AI tasks, auto-generated Swagger UI for easy testing, high performance.
- **Key Libraries**: `fastapi`, `uvicorn`, `pydantic`.

### Frontend
- **Framework**: Vue.js 3 + Vite
- **Reasoning**: Fast development cycle, component-based architecture ideal for chat interfaces.

### Data Layer
- **Development Database**: SQLite
- **Production Database**: MySQL 8.0
- **Data Source**: OpenDigger (Issue/PR/Event logs)
- **Visualization**: DataEase (Embedded) / Chart.js (Frontend fallback)

### AI Engine
- **Core**: SQLBot (Text-to-SQL)
- **Integration**: Backend proxies requests to SQLBot API, handling context and schema linking.

## 3. Directory Structure
```
open-detective/
├── .github/workflows/         # Automation (CI/CD, simulation scripts)
├── data/                      # Data Engineering
│   ├── raw/                   # Raw OpenDigger data (JSON/CSV)
│   ├── sql/                   # SQL schemas and views (schema.sql)
│   └── etl_scripts/           # Python scripts for data cleaning
├── src/                       # Source Code
│   ├── backend/               # Python API Server
│   │   ├── main.py            # Entry point
│   │   ├── services/          # Business logic (SQLBot client)
│   │   └── api/               # API Routers
│   └── frontend/              # Vue.js Application
├── docs/                      # Documentation
│   └── ARCHITECTURE.md        # This file
├── docker-compose.yml         # Container orchestration
└── README.md                  # Project Entry
```

## 4. Modules Description

### Backend
- **`services/sqlbot_client.py`**: Handles communication with the SQLBot engine.
- **`api/routes.py`**: Defines endpoints for the frontend (e.g., `/chat`, `/query`).

### Data
- **ETL Pipeline**: Fetches data from OpenDigger -> Cleans/Normalizes -> Loads into DB.

## 5. Next Steps
1. Implement basic OpenDigger data fetcher.
2. Set up Vue.js frontend project.
3. Integrate SQLBot API stub.
