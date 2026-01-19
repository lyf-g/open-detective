# 🕵️‍♂️ Open-Detective (开源侦探)

<p align="center">
  <img src="https://img.shields.io/badge/Vue.js-3.0-4FC08D?style=for-the-badge&logo=vue.js&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-0.128-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/MySQL-8.0-4479A1?style=for-the-badge&logo=mysql&logoColor=white" />
  <img src="https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white" />
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge" />
</p>

> **Don't just query. Investigate.**
>
> Open-Detective is a next-generation Open Source insight platform powered by **Text-to-SQL** and **OpenDigger**. It transforms passive reporting into active investigation, helping OSPOs and developers uncover hidden risks and trends like a detective.

---

## 🔍 Why Open-Detective?

Traditional dashboards show you **What** happened. Open-Detective tells you **Why**.
- **Human-Centric**: Speak to your data in natural language.
- **Root Cause Oriented**: Go beyond spikes; find the events that triggered them.
- **Production Ready**: Built with self-healing protocols and asynchronous high-concurrency architecture.

---

## ✨ Advanced Detective Skills (核心亮点)

### 🧠 Neural Deduction Engine (神经演绎引擎)
*   **Dual-Engine Switching**: Millisecond response for high-frequency metrics (Stars, Activity) + Deep LLM reasoning for complex comparisons.
*   **Self-Healing SQL Protocol**: Automatically detects SQL errors, injects Schema context, and repairs queries in real-time.
*   **Intelligent Fallback**: Seamlessly generates structured Markdown audit reports even when upstream LLM services are unavailable.

### 🚨 Anomaly & Root Cause Analysis (根因溯源)
*   **Automated Anomaly Detection**: Built-in **Z-Score algorithm** highlights statistical outliers (spikes/drops) on interactive charts.
*   **Probabilistic Causal Graph**: Interactive **Bayesian Inference Chain** (Root -> Trigger -> Outcome) to explain *why* data fluctuated.

### 🎨 Cyber-Detective UI
*   **Immersive Analytics**: Dark-themed, cyberpunk-inspired dashboard with dynamic ECharts.
*   **Multilingual Support**: One-click switch between English and Chinese.
*   **Case Export**: Export your entire investigation journey (SQL, Data, Analysis) as a professional Markdown dossier.

---

## 🛠️ Tech Stack (技术栈)

- **Frontend**: Vue 3 (Composition API), TypeScript, Vite, ECharts 5
- **Backend**: Python 3.10+, FastAPI (Asynchronous), MySQL 8.0, Redis
- **Security**: Token-based Auth, RSA Encryption for SQLBot Credentials
- **Infrastructure**: Docker Multi-stage Builds, GitHub Actions CI/CD

---

## 🚀 Quick Start (快速启动)

### 1. Configure Environment
Copy the example environment file and customize it:
```bash
cp .env.example .env
```

### 2. Boot up the Command Center
Launch the entire stack with a single command:
```bash
docker-compose up --build -d
```

### 3. Initialize Evidence Data
Populate your database with real-world history from 50+ top-tier open source projects:
```bash
# Wait 10s for DB to be ready, then:
docker-compose exec backend python data/etl_scripts/fetch_opendigger.py
```

### 4. Start Investigating
Visit [http://localhost:8082](http://localhost:8082) and start your first inquiry!

---

## 🌐 Service Portal (服务入口)

| Portal | URL | Description |
| :--- | :--- | :--- |
| **Detective Command Center (Web)** | [http://localhost:8082](http://localhost:8082) | Main User Interface |
| **SQLBot Management** | [http://localhost:8000](http://localhost:8000) | Data source & LLM Config |
| **Backend API Docs** | [http://localhost:8081/docs](http://localhost:8081/docs) | FastAPI Swagger UI |

---

## 📄 License
Distributed under the MIT License. See `LICENSE` for more information.

---
<p align="center">
  Built with ❤️ for the 2026 DataEase & OpenDigger Competition.
</p>