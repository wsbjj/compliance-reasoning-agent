"""
LangGraph StateGraph 构建
编排智能体工作流:
  START → Node_Plan → [Node_Fetch_Patents, Node_Fetch_Trends]
       → Node_Synthesize → Node_Review
            ↓ review_passed=True  → Node_Update_Memory → END
            ↓ review_passed=False → Node_Synthesize (重写)
"""
from __future__ import annotations

import logging

from langgraph.graph import StateGraph, END

from app.agent.state import AgentState
from app.agent.nodes.plan_node import plan_node
from app.agent.nodes.patent_node import patent_node
from app.agent.nodes.trend_node import trend_node
from app.agent.nodes.synthesize_node import synthesize_node
from app.agent.nodes.review_node import review_node
from app.agent.nodes.memory_node import memory_node

logger = logging.getLogger(__name__)


def _should_continue(state: AgentState) -> str:
    """
    条件边: 检查审核是否通过
    - 通过 → memory (存储记忆，然后结束)
    - 不通过 → synthesize (重写报告)
    """
    if state.get("review_passed", False):
        return "memory"
    else:
        return "synthesize"


def build_graph() -> StateGraph:
    """
    构建合规推理智能体的 LangGraph StateGraph

    工作流:
    1. plan: 任务规划 (Reflect 1)
    2. patents: 专利搜索 (Tools)
    3. trends: 趋势分析 (Tools)
    4. synthesize: 报告生成 (Action)
    5. review: 报告审核 (Reflect 2)
    6. memory: 记忆更新
    """
    graph = StateGraph(AgentState)

    # ---- 添加节点 ----
    graph.add_node("plan", plan_node)
    graph.add_node("patents", patent_node)
    graph.add_node("trends", trend_node)
    graph.add_node("synthesize", synthesize_node)
    graph.add_node("review", review_node)
    graph.add_node("memory", memory_node)

    # ---- 添加边 ----
    # START → plan
    graph.set_entry_point("plan")

    # plan → patents & trends (并行)
    graph.add_edge("plan", "patents")
    graph.add_edge("plan", "trends")

    # patents → synthesize
    graph.add_edge("patents", "synthesize")

    # trends → synthesize
    graph.add_edge("trends", "synthesize")

    # synthesize → review
    graph.add_edge("synthesize", "review")

    # review → 条件分支
    graph.add_conditional_edges(
        "review",
        _should_continue,
        {
            "memory": "memory",
            "synthesize": "synthesize",
        },
    )

    # memory → END
    graph.add_edge("memory", END)

    logger.info("LangGraph StateGraph built successfully")
    return graph


def compile_graph():
    """编译 StateGraph 为可执行的 Runnable"""
    graph = build_graph()
    return graph.compile()


async def run_agent(
    query: str,
    extra_context: str = "",
    user_id: str = "default",
) -> AgentState:
    """
    执行合规推理智能体

    Args:
        query: 产品核心关键词
        extra_context: 额外上下文信息
        user_id: 用户 ID

    Returns:
        最终的 AgentState
    """
    app = compile_graph()

    initial_state: AgentState = {
        "query": query,
        "extra_context": extra_context,
        "user_id": user_id,
        "plan": "",
        "search_keywords": [],
        "patents": [],
        "patent_analysis": "",
        "trends": [],
        "trend_summaries": [],
        "trend_analysis": "",
        "draft_report": "",
        "final_report": "",
        "review_passed": False,
        "review_feedback": "",
        "iteration_count": 0,
        "memory_context": "",
        "report_id": "",
        "error": None,
    }

    logger.info(f"Running agent for query: '{query}'")

    try:
        final_state = await app.ainvoke(initial_state)
        logger.info("Agent execution completed successfully")
        return final_state
    except Exception as e:
        logger.error(f"Agent execution failed: {e}")
        initial_state["error"] = str(e)
        return initial_state
