"""
Node_Synthesize — 报告生成节点 (Action)

聚合专利分析 + 趋势数据 + 外部上下文，生成 Markdown 格式的窗口期预警简报。
"""
from __future__ import annotations

import logging

from app.agent.state import AgentState
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)


async def synthesize_node(state: AgentState) -> AgentState:
    """
    Action: 生成窗口期预警简报
    - 聚合所有分析数据
    - 调用 LLM 生成 Markdown 报告
    """
    patent_analysis = state.get("patent_analysis", "无专利数据")
    trend_analysis = state.get("trend_analysis", "无趋势数据")
    extra_context = state.get("extra_context", "")
    review_feedback = state.get("review_feedback", "")
    iteration = state.get("iteration_count", 0)

    logger.info(
        f"[Node_Synthesize] Generating report (iteration {iteration})"
    )

    llm_service = LLMService()

    # 如果是重写（有审核反馈），加入反馈信息
    if review_feedback and iteration > 0:
        extra_context_full = f"""{extra_context}

## 上轮审核反馈（请据此改进）
{review_feedback}
"""
    else:
        extra_context_full = extra_context

    # 生成报告
    report = await llm_service.generate_report(
        patent_analysis=patent_analysis,
        trend_data=trend_analysis,
        extra_context=extra_context_full,
    )

    logger.info(
        f"[Node_Synthesize] Report generated, length: {len(report)} chars"
    )

    return {
        "draft_report": report,
        "iteration_count": iteration + 1,
    }
