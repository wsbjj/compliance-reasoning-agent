# Compliance Reasoning Agent — 智能体架构文档

## 系统概览

本系统是基于 **LangGraph** 的合规推理智能体，用于自动化的产品专利排查、市场趋势分析和窗口期预警简报生成。
采用类 Spring Boot 的**三层分离架构** (Controller → Service → Repository)，集成 **MCP 协议**标准化工具调用，
使用 **Mem0** 实现长短期记忆管理。

---

## 技术栈

| 层级 | 技术 |
|------|------|
| **智能体框架** | LangGraph (StateGraph) |
| **后端服务** | FastAPI + Uvicorn |
| **前端看板** | Streamlit |
| **数据处理** | pandas + Plotly |
| **大模型** | OpenAI 格式 (硅基流动等) |
| **记忆系统** | Mem0 |
| **工具协议** | MCP (Model Context Protocol) |
| **数据库** | PostgreSQL (asyncpg) |
| **缓存** | Redis |
| **配置管理** | pydantic-settings (.env) + PyYAML (config.yaml) |

---

## 核心架构: Memory / Tools / Action / Reflect

```
┌─────────────────────────────────────────────────────────────────┐
│                     合规推理智能体 (LangGraph)                    │
│                                                                  │
│  ┌───────────┐    ┌───────────┐    ┌───────────┐    ┌──────────┐ │
│  │  Memory    │    │  Reflect  │    │   Tools   │    │  Action  │ │
│  │  (Mem0)    │◄──►│  (LLM)    │◄──►│  (MCP)    │◄──►│ (Output) │ │
│  └───────────┘    └───────────┘    └───────────┘    └──────────┘ │
│       │                │                │                │       │
│       ▼                ▼                ▼                ▼       │
│  长短期记忆       任务规划/审核      专利/趋势API      报告生成    │
│  对话摘要衰减     ReAct推理模式      标准化JSON-RPC    Markdown   │
└─────────────────────────────────────────────────────────────────┘
```

### 1. Memory (记忆机制) — Mem0

- **短期记忆**: 当前对话的多轮上下文（StateGraph 状态字典）
- **长期记忆**: 基于 Mem0 + Redis 的历史分析记录
- **摘要衰减**: 近期上下文 → 长摘要 (≤500字)；远期上下文 → 短摘要 (≤100字)
- **过期淘汰**: 超过 retention_days (默认90天) 的记忆自动跳过

### 2. Tools (工具调用) — MCP 协议

通过 MCP Server 标准化所有外部 API 调用:

| MCP Server | 工具 | 底层 API |
|-----------|------|---------|
| patent-search-server | `search_patents` | SerpApi / USPTO |
| patent-search-server | `analyze_patent_landscape` | LLM |
| trend-data-server | `fetch_google_trends` | pytrends |
| trend-data-server | `fetch_amazon_trends` | Rainforest / Keepa |
| trend-data-server | `calculate_cagr` | 内置计算 |

**解耦优势**: 替换底层 API (如 SerpApi → USPTO) 只需修改 config.yaml，无需改动 Agent 逻辑。

### 3. Action (执行与输出)

- 生成 Markdown 格式的《窗口期预警简报》
- 构建 Pandas DataFrame 的专利布局矩阵
- 输出 Plotly 交互式趋势图表

### 4. Reflect (反思与推理) — ReAct 模式

- **Reflect 1 (plan_node)**: 分析查询意图，制定数据采集计划
- **Reflect 2 (review_node)**: 自审报告质量，不达标则循环重写
- **安全阀**: 最大迭代次数限制 (默认 3 次)

---

## LangGraph 工作流

```
 ┌───────┐
 │ START │
 └───┬───┘
     ▼
┌──────────┐
│ Node_Plan│  ← Reflect 1: 任务规划
└────┬─────┘
     ├──────────────┐
     ▼              ▼
┌──────────┐  ┌──────────┐
│ Patents  │  │  Trends  │  ← Tools: 并行数据获取
└────┬─────┘  └────┬─────┘
     ├──────────────┘
     ▼
┌──────────────┐
│ Synthesize   │  ← Action: 报告生成
└──────┬───────┘
       ▼
┌──────────────┐
│   Review     │  ← Reflect 2: 质量审核
└──────┬───────┘
       │
  ┌────┴─────┐
  │          │
  ▼          ▼
PASS       FAIL ──→ 回到 Synthesize (重写)
  │
  ▼
┌──────────────┐
│   Memory     │  ← 记忆更新
└──────┬───────┘
       ▼
 ┌─────┐
 │ END │
 └─────┘
```

---

## 三层分离架构

```
┌──────────────────────────────────┐
│       Controller 层 (FastAPI)      │  ← API 端点, 请求验证
├──────────────────────────────────┤
│       Service 层 (Business)        │  ← 业务逻辑, LLM, 记忆
├──────────────────────────────────┤
│       Repository 层 (Data)         │  ← ORM CRUD, 数据访问
├──────────────────────────────────┤
│       Infrastructure               │  ← PostgreSQL, Redis
└──────────────────────────────────┘
```

---

## 双配置驱动

### .env — 敏感信息

```
LLM_API_KEY=sk-xxx
SERPAPI_API_KEY=xxx
DATABASE_URL=postgresql+asyncpg://...
REDIS_URL=redis://localhost:6379/0
```

### config.yaml — 业务逻辑

```yaml
data_sources:
  patent_provider: "serpapi"    # 切换: serpapi | uspto
  trend_provider: "pytrends"   # 切换: pytrends | rainforest | keepa
agent:
  max_review_iterations: 3
  patent_search_limit: 50
```

**工厂模式**: 系统启动时根据 config.yaml 的 provider 字段初始化对应的 Service 实现。

---

## CAGR 计算公式

$$CAGR = \left( \frac{Ending\ Value}{Beginning\ Value} \right)^{\frac{1}{n}} - 1$$

- 在 `TrendService.calculate_cagr()` 中实现
- 通过 MCP Server 暴露为 `calculate_cagr` 工具

---

## 快速启动

```bash
# 1. 安装依赖
pip install -e .

# 2. 复制并配置环境变量
cp .env.example .env
# 编辑 .env 填入 API Keys

# 3. 启动 FastAPI 后端
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 4. 启动 Streamlit 前端
streamlit run frontend/app.py --server.port 8501
```
