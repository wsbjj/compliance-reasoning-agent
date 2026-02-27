"""
Agent 状态定义 (AgentState)
LangGraph StateGraph 的状态字典

注意：patents/trends/trend_summaries/search_keywords 使用 Annotated[list, operator.add]
      是因为 plan → patents 和 plan → trends 并行执行，两个节点都可能更新列表字段，
      LangGraph 需要一个 reducer 函数（此处为 add，即合并列表）来避免并发冲突。
"""
from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict


class AgentState(TypedDict, total=False):
    """合规推理智能体的全局状态"""

    # ---- 输入 ----
    # 用户输入的产品关键词（如 "Smart Ring"）
    # Annotated + lambda：若多个节点同时写入，取后者（新值），防止并发冲突
    query: Annotated[str, lambda a, b: b]
    # 用户提供的额外上下文信息（如 "AI API 成本下降 80%"）
    extra_context: Annotated[str, lambda a, b: b]

    # ---- Node_Plan 输出 ----
    # 任务规划描述
    plan: str
    # 需要搜索的关键词列表（Annotated：并行节点写入时自动合并，不冲突）
    search_keywords: Annotated[list[str], operator.add]

    # ---- Node_Fetch_Patents 输出 ----
    # 专利原始数据列表（Annotated：并行节点写入时自动合并）
    patents: Annotated[list[dict[str, Any]], operator.add]
    # LLM 专利分析结果
    patent_analysis: str

    # ---- Node_Fetch_Trends 输出 ----
    # 趋势原始数据（Annotated：并行节点写入时自动合并）
    trends: Annotated[list[dict[str, Any]], operator.add]
    # CAGR 计算结果（Annotated：并行节点写入时自动合并）
    trend_summaries: Annotated[list[dict[str, Any]], operator.add]
    # 趋势分析文本
    trend_analysis: str

    # ---- Node_Synthesize 输出 ----
    # 初稿报告 (Markdown)
    draft_report: str

    # ---- Node_Review 输出 ----
    # 终稿报告 (Markdown)
    final_report: str
    # 审核是否通过
    review_passed: bool
    # 审核反馈
    review_feedback: str
    # 当前迭代次数
    iteration_count: int

    # ---- Memory ----
    # 历史记忆上下文
    memory_context: str

    # ---- 元数据 ----
    # 报告 ID (关联数据库)
    report_id: str
    # 用户 ID
    user_id: str
    # 错误信息
    error: str | None
