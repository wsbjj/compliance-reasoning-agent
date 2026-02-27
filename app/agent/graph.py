"""
LangGraph StateGraph 构建
编排智能体工作流:
  START → Node_Plan → [Node_Fetch_Patents, Node_Fetch_Trends]
       → Node_Synthesize → Node_Review
            ↓ review_passed=True  → Node_Update_Memory → END
            ↓ review_passed=False → Node_Synthesize (重写)

终端节点调用路径追踪 (astream):
  每个节点执行完后，自动打印调用路径和耗时到终端。
"""
from __future__ import annotations

import logging
import time

from langgraph.graph import StateGraph, END

from app.agent.state import AgentState
from app.agent.nodes.plan_node import plan_node
from app.agent.nodes.patent_node import patent_node
from app.agent.nodes.trend_node import trend_node
from app.agent.nodes.synthesize_node import synthesize_node
from app.agent.nodes.review_node import review_node
from app.agent.nodes.memory_node import memory_node

logger = logging.getLogger(__name__)

# 节点执行顺序（用于打印路径追踪）
_NODE_ORDER = ["plan", "patents", "trends", "synthesize", "review", "memory"]
_NODE_LABELS = {
    "plan":       "任务规划 (Reflect 1)",
    "patents":    "专利搜索 + DB写入 (Tools, 并行)",
    "trends":     "趋势分析 + DB写入 (Tools, 并行)",
    "synthesize": "报告生成 (Action)",
    "review":     "质量审核 (Reflect 2)",
    "memory":     "记忆更新 + 报告持久化 (Memory)",
}


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
    report_id: str = "",
) -> AgentState:
    """
    执行合规推理智能体

    Args:
        query: 产品核心关键词
        extra_context: 额外上下文信息
        user_id: 用户 ID
        report_id: 数据库报告 ID（由 API 层创建后传入）

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
        "report_id": report_id,
        "error": None,
    }

    logger.info(f"Running agent for query: '{query}', report_id: '{report_id}'")

    # ---- 节点调用路径追踪头 ----
    _print_trace_header(query)

    visited_nodes: list[str] = []
    start_time = time.monotonic()
    node_start_time = start_time
    final_state = initial_state

    try:
        async for event in app.astream(initial_state):
            for node_name, node_output in event.items():
                elapsed = time.monotonic() - node_start_time
                node_start_time = time.monotonic()
                visited_nodes.append(node_name)
                _print_node_trace(node_name, elapsed, node_output)
                # 更新 final_state（astream 每步返回当前节点的输出）
                if isinstance(node_output, dict):
                    final_state = {**final_state, **node_output}

        total_elapsed = time.monotonic() - start_time
        _print_trace_footer(visited_nodes, total_elapsed)
        logger.info("Agent execution completed successfully")
        return final_state

    except Exception as e:
        total_elapsed = time.monotonic() - start_time
        _print_trace_error(e, total_elapsed)
        logger.error(f"Agent execution failed: {e}")
        initial_state["error"] = str(e)
        return initial_state


# ---- 路径追踪辅助函数 ----

def _print_trace_header(query: str) -> None:
    print("\n" + "═" * 60)
    print("  🤖 Agent Execution Path Trace")
    print(f"  📦 Query: {query}")
    print("═" * 60)


def _print_node_trace(node_name: str, elapsed: float, output: dict) -> None:
    label = _NODE_LABELS.get(node_name, node_name)
    # 从输出中提取关键指标做简单摘要
    summary_parts = []
    if isinstance(output, dict):
        if "patents" in output:
            summary_parts.append(f"{len(output['patents'])} patents")
        if "trends" in output:
            summary_parts.append(f"{len(output['trends'])} trend pts")
        if "trend_summaries" in output:
            summary_parts.append(f"{len(output['trend_summaries'])} summaries")
        if "review_passed" in output:
            passed = output["review_passed"]
            summary_parts.append("✅ PASSED" if passed else "❌ RETRY")
        if "search_keywords" in output:
            kws = output["search_keywords"]
            summary_parts.append(f"keywords={kws}")
    summary = "  " + ", ".join(summary_parts) if summary_parts else ""
    print(f"  ▶ [{node_name:12s}]  {label:<40s}  ({elapsed:.1f}s){summary}")


def _print_trace_footer(visited: list[str], total: float) -> None:
    path = " → ".join(visited)
    print("─" * 60)
    print(f"  路径: {path}")
    print(f"  ✅ Agent completed in {total:.1f}s")
    print("═" * 60 + "\n")


def _print_trace_error(e: Exception, total: float) -> None:
    print("─" * 60)
    print(f"  ❌ Agent FAILED after {total:.1f}s: {e}")
    print("═" * 60 + "\n")
