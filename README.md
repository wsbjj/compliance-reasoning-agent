# Compliance Reasoning Agent 🛡️

基于 **LangGraph** 的合规推理智能体项目 —— 专注于**专利排查**、**搜索趋势分析**与**商业窗口期预警**的自动化 AI 代理。

本项目通过将大语言模型（LLM）的分析能力与外部数据源（SerpApi、Google Trends）相结合，实现深度的自动化商业环境监测与合规推理分析。所有的分析流程被设计为工作流节点（Nodes），并自带基于 PostgreSQL 的数据持久化和历史记录管理体系。

---

## 🌟 核心功能特性

1. **📋 自动化专利排查 (Patent Analysis)**
   - 自动在多个外部数据源（如 SerpApi / USPTO）进行检索检索分析。
   - 对相关的竞品专利布局及潜在的专利侵权风险进行初步整理和排查。

2. **📈 趋势监测看板 (Trend Dashboard)**
   - 集成 `pytrends` 等工具动态获取关键字的搜索指数和趋势变化。
   - 自动计算复合年均增长率 (CAGR) 及热度周期。
   - 通过 Plotly 提供直观、高度定制化的数据图表可视化。
   - 具备高可用的检索机制（内置代理配置、自动重试和退避策略）。

3. **🔍 智能预警与决策简报 (Early Warning Briefs)**
   - 利用 LLM 分析专利排查结果与趋势数据的交叉点。
   - 智能生成商业窗口期判断、“红海/蓝海”评估以及行动建议简报。

4. **💾 全链路数据持久化 (Database Persistence)**
   - 集成 PostgreSQL 数据库与 SQLAlchemy ORM，实现所有节点生成数据的长效持久化存储。
   - 代理的工作路径、分析态数据（Patent Node、Trend Node、Memory Node）不再随程序重启而丢失。
   - 前端完美支持历史会话分析记录的调取与展示。

5. **🧠 长期记忆库 (Long-term Memory)**
   - 集成 `Mem0` (配合本地 Qdrant 向量库)，保留智能体过去的知识积累和推理上下文，支持多轮次深入推演。

6. **🎯 本地化且优雅的前端交互界面**
   - 采用高度定制的 Streamlit 前端界面。
   - 实现全中文语义的侧边栏导航体系 (`st.page_link`)，告别默认繁杂结构，极简清爽。

---

## 🛠️ 技术栈与依赖

### 🤖 Agent & AI 框架
- [LangGraph](https://python.langchain.com/docs/langgraph) (v0.2+) - 负责驱动核心的 StateGraph 状态代理和节点编排
- [LangChain](https://python.langchain.com/) / LangChain-OpenAI - 大模型交互层
- [Mem0AI](https://github.com/mem0ai/mem0) - 专门的 Agent 记忆管理中间件

### ⚙️ 后端与数据层
- [FastAPI](https://fastapi.tiangolo.com/) - 提供高性能和易扩展的 API 层
- PostgreSQL (asyncpg) + SQLAlchemy 2.0 - 异步数据库驱动与 ORM 操作
- Redis - 用于部分系统级缓存与消息通信
- Qdrant (Local) - 向量数据库，驱动 Mem0 记忆检索

### 🖥️ 前端与可视化
- [Streamlit](https://streamlit.io/) - 快速构建数据面板与应用交互界面
- [Plotly](https://plotly.com/python/) - 图表可视化引擎
- Pandas - 面向数据分析的结构化处理

### 🔌 API 与外部服务
- `google-search-results` (SerpApi) - 提供搜索和专利检索 API 接口
- `pytrends` - Google 趋势非官方 API 包装器

---

## 📂 项目文件结构

```text
compliance-reasoning-agent/
├── app/                        # 🚀 后端应用与 Agent 核心代码包
│   ├── api/                    # FastAPI 路由控制器 (Endpoints)
│   ├── agent/                  # LangGraph 智能体定义层
│   │   ├── graph.py            # StateGraph 核心编排引擎
│   │   └── nodes/              # 图节点：patent_node, trend_node, memory_node 等
│   ├── core/                   # 核心配置 (Config, Database Session, Redis)
│   ├── models/                 # SQLAlchemy 数据库表 ORM 模型
│   ├── repositories/           # 数据库访问层 ( Repository 模式封装 )
│   ├── services/               # 业务逻辑服务层 ( PatentService, TrendService )
│   └── mcp_servers/            # (可选) MCP 工具协议集成服务
├── frontend/                   # 🎨 Streamlit 前端应用包
│   ├── app.py                  # 前端主入口文件
│   └── ...                     # 页面组件与视图文件
├──.agent/                      # AI 助手相关配置与 Skills 存放区
├──.streamlit/                  # Streamlit 主题与界面相关配置文件
├── config.yaml                 # 业务级补充配置文件
├── .env.example                # 环境变量配置模板
├── pyproject.toml              # 项目依赖描述文件 (使用 uv/hatch 构建)
├── agent.md                    # Agent 架构与设计图核心文档
└── frontend-standards.md       # 前端 UI/UX 设计规范
```

---

## 🚀 快速启动指南

建议使用现代 Python 包管理器 [uv](https://docs.astral.sh/uv/) 来运行本项目。要求 **Python 3.12+**。

### 1. 环境准备与依赖安装

通过 `uv` 快速创建虚拟环境并安装依赖：

```bash
# 自动通过 pyproject.toml 安装包及其所有依赖
uv pip install -e .
```

### 2. 环境变量配置

复制环境变量模板，并填入相应的 API 密钥。

```bash
cp .env.example .env
```

**须在 `.env` 中特别关注的几个值：**
- `OPENAI_API_KEY`: 大模型提供商的 API Key，或兼容 OpenAI 格式的三方模型 Key。
- `SERPAPI_API_KEY`: 用户获取专利搜索信息的 SerpApi Key。
- 数据库连接：默认需要本地跑着 PostgreSQL，如 `DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/db_name`。
- 如果请求 Google Trends 失败（由于区域网络问题），需要配置 `HTTP_PROXY` / `HTTPS_PROXY` 或由代码层通过配置项读取代理。

### 3. 快速启动服务

本项目采用**前后端分离机制运行**，请开启两个终端窗口。

**终端 1: 启动 FastAPI 后端 API**
```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**终端 2: 启动 Streamlit 前端面板**
```bash
uv run streamlit run frontend/app.py --server.port 8501
```

启动完毕后，浏览器打开 `http://localhost:8501` 即可体验。

---

## 📖 高阶阅读与资料

- 深入理解智能体的运行图与设计哲学，请阅读：[`agent.md`](agent.md)
- 查看项目制定的前端设计标准与样式准则：[`frontend-standards.md`](frontend-standards.md)
