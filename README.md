# 🕵️‍♂️ Open-Detective (开源神探)

> **Don't just query. Investigate.**
>
> Open-Detective 是一个基于 **Text-to-SQL** 技术和 **OpenDigger** 生态的开源社区洞察工具。它将传统的“被动看报表”转变为“主动查风险”，帮助 OSPO 和开发者像侦探一样审视开源项目的健康状况。

## ✨ Core Features (核心功能)

- **🔍 自然语言侦查 (SQLBot Powered)**
  - 像聊天一样查询数据：“Vue 的活跃度怎么样？”，“查询 VS Code 的 Bus Factor”。
  - 集成官方指定的 **DataEase SQLBot** 引擎，实现精准的语义理解与 SQL 生成。

- **📊 沉浸式数据大屏**
  - **赛博朋克/自定义风格 UI**：支持多种主题切换（Cyberpunk, Minimalist, Ocean）及自定义强调色。
  - **动态可视化**：基于 ECharts 自动渲染折线图、柱状图，图表主题随系统实时同步。
  - **多维度指标**：支持 Stars, Activity, OpenRank, **Bus Factor** (人才风险), **Issues New/Closed** (维护效率) 等 50+ 全球顶级项目数据。

- **🚨 异常检测 (Anomaly Detection)**
  - **智能风控**：内置 Z-score 算法自动识别数据异常点（如 Star 数突增、Issue 积压暴涨）。
  - **即时分析**：在图表界面一键点击 "Find Anomalies" 即可高亮显示异常波动。

- **💾 企业级数据引擎**
  - 使用 **MySQL 8.0** 存储海量 OpenDigger 真实历史指标。
  - **Redis 缓存**：高频查询毫秒级响应。
  - 内置高性能 ETL 管道，直连官方 OSS CDN 数据源。

- **📂 案件卷宗导出**
  - 一键将当前的侦查对话、SQL 证据和数据快照导出为 Markdown 格式的案件报告。

## 🛠️ Tech Stack (技术栈)

- **Frontend**: Vue 3, TypeScript, Vite, ECharts
- **Backend**: Python, FastAPI (Async), MySQL 8.0, Redis
- **AI Engine**: DataEase SQLBot (Text-to-SQL + RAG)
- **Deployment**: Docker, Docker Compose

## 🚀 Quick Start (快速启动)

### Prerequisites (前置要求)
- Docker & Docker Compose
- (可选) Python 3.8+ (用于本地开发)

### 1. 启动全栈环境 (一键启动)
项目已高度集成化，使用 Docker Compose 即可拉起所有服务。

```bash
# 构建并启动容器
docker-compose up --build -d
```

### 2. 初始化数据 (Data Setup)
在容器启动后，需要将 OpenDigger 数据灌入 MySQL。

```bash
# 初始化表结构并填充基础数据
docker-compose exec backend python data/etl_scripts/mock_data.py

# (推荐) 拉取 50 个全球顶级项目的真实历史数据
docker-compose exec backend python data/etl_scripts/fetch_opendigger.py
```

### 3. 配置 SQLBot (智能配置)
系统支持自动配置 SQLBot。
1.  **自动配置**: 在 `.env` 中设置 `SQLBOT_AUTO_CONFIG=true` 并填写 LLM 相关信息，后端启动时会自动尝试配置数据源和模型。
2.  **手动配置**:
    *   **访问后台**: [http://localhost:8000](http://localhost:8000)
    *   **登录凭据**: User: `admin` | Pass: `SQLBot@123456`
    *   **添加数据源**: MySQL (`mysql` : `3306` / `open_detective`)
    *   **生成 Token**: 填入 `.env` 的 `SQLBOT_API_KEY` (支持热加载)。

## 🌐 Service Portal (服务入口)

| 服务名称 | 访问地址 | 说明 |
| :--- | :--- | :--- |
| **神探指挥中心 (Web)** | [http://localhost:8082](http://localhost:8082) | 用户主界面 |
| **SQLBot 管理后台** | [http://localhost:8000](http://localhost:8000) | 配置数据源与 LLM |
| **后端 API 文档** | [http://localhost:8081/docs](http://localhost:8081/docs) | FastAPI Swagger UI |

## 📄 License
MIT License
