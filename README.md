# Compliance Reasoning Agent 🛡️

基于 **LangGraph** 的合规推理智能体 — 专利排查 · 趋势分析 · 窗口期预警

## 功能模块

| 模块 | 功能 | 数据源 |
|------|------|--------|
| 📋 专利排查 | 自动搜索并分析竞品专利布局 | SerpApi / USPTO |
| 📈 趋势看板 | 搜索指数趋势 + CAGR 增长率分析 | pytrends / Rainforest / Keepa |
| 🔍 预警简报 | AI 生成窗口期判断和行动建议 | LLM (OpenAI 格式) |

## 技术栈

- **智能体**: LangGraph + MCP 协议 + Mem0
- **后端**: FastAPI + PostgreSQL + Redis
- **前端**: Streamlit + Plotly
- **配置**: pydantic-settings (.env) + PyYAML (config.yaml)

## 快速启动

```bash
# 安装依赖
pip install -e .

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入 API Keys 和数据库连接

# 启动后端
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 启动前端 (新终端)
streamlit run frontend/app.py --server.port 8501
```

## 项目结构

```
├── app/                    # 应用主包
│   ├── core/              # 核心配置 (config, database, redis)
│   ├── models/            # SQLAlchemy ORM 模型
│   ├── repositories/      # 数据访问层 (Repository)
│   ├── services/          # 业务逻辑层 (Service)
│   ├── agent/             # LangGraph 智能体
│   │   ├── graph.py       # StateGraph 编排
│   │   └── nodes/         # 各节点实现
│   ├── mcp_servers/       # MCP 工具服务
│   └── api/               # FastAPI 路由 (Controller)
├── frontend/              # Streamlit 前端
├── config.yaml            # 业务配置
├── .env.example           # 环境变量模板
└── agent.md               # 架构文档
```

详细架构说明请参考 [agent.md](agent.md)。
