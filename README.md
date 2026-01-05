# 🕵️‍♂️ Open-Detective (开源神探)

> **Don't just query. Investigate.**
>
> Open-Detective 是一个基于 **Text-to-SQL** 技术和 **OpenDigger** 生态的开源社区洞察工具。它将传统的“被动看报表”转变为“主动查风险”，帮助 OSPO 和开发者像侦探一样审视开源项目的健康状况。

## ✨ Core Features (核心功能)

- **🔍 自然语言侦查 (Text-to-SQL)**
  - 像聊天一样查询数据：“Vue 的活跃度怎么样？”，“查询 VS Code 的 Bus Factor”。
  - 自动将自然语言转换为 SQL 并在本地数据库执行。

- **📊 沉浸式数据大屏**
  - **赛博朋克/暗黑风格 UI**：专为长时间分析设计的护眼界面。
  - **动态可视化**：基于 ECharts 自动渲染折线图、柱状图。
  - **多维度指标**：支持 Stars, Activity, OpenRank, **Bus Factor** (人才风险), **Issues New/Closed** (维护效率)。

- **💾 真实数据引擎**
  - 内置 ETL 管道，直连 **OpenDigger** 官方数据源 (OSS CDN)。
  - 支持历史数据回溯与趋势分析。

- **📂 案件卷宗导出**
  - 一键将当前的侦查对话、SQL 证据和数据快照导出为 Markdown 格式的案件报告。

## 🛠️ Tech Stack (技术栈)

- **Frontend**: Vue 3, TypeScript, Vite, ECharts (Dark Mode)
- **Backend**: Python, FastAPI, SQLite
- **Data Source**: OpenDigger (via HTTP API/CDN)

## 🚀 Quick Start (快速启动)

### Prerequisites (前置要求)
- Python 3.8+
- Node.js 16+

### 1. 初始化与数据准备 (Data Setup)
首先，安装后端依赖并拉取 OpenDigger 的真实数据。

```bash
# 进入项目根目录
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装依赖
pip install requests fastapi uvicorn pydantic python-dotenv

# 初始化数据库结构
python3 data/etl_scripts/mock_data.py  # (可选) 初始化 Schema

# [核心] 拉取 OpenDigger 真实数据
python3 data/etl_scripts/fetch_opendigger.py
```

### 2. 启动后端侦探服务 (Backend)
```bash
# 确保还在虚拟环境中
uvicorn src.backend.main:app --reload --port 8081
# 服务将运行在 http://localhost:8081
```

### 3. 启动前端指挥中心 (Frontend)
打开一个新的终端窗口：
```bash
cd src/frontend
npm install
npm run dev
# 访问 http://localhost:5173
```

## 📝 Usage Examples (使用示例)

在聊天框中输入以下指令体验：
- `Show me stars for vuejs/core` (查看 Vue 核心仓库的 Star 趋势)
- `What is the bus factor for tensorflow` (侦查 TensorFlow 的人才风险)
- `Show me new issues for vscode` (查看 VS Code 的 Issue 吞吐量)
- `Compare activity for react` (查看 React 的活跃度)

## 📄 License
MIT License