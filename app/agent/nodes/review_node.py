"""
Node_Review — 报告审核节点 (Reflect 2)

检查生成的报告是否达标，决定通过或打回重写。
"""
from __future__ import annotations

import logging

from app.agent.state import AgentState
from app.core.config import get_yaml_config
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)


async def review_node(state: AgentState) -> AgentState:
    """
    Reflect 2: 报告质量审核
    - LLM 自审报告质量
    - 检查必要章节是否齐全
    - 决定通过或重写（受最大迭代次数限制）
    """
    draft = state.get("draft_report", "")
    iteration = state.get("iteration_count", 0)
    max_iterations = get_yaml_config().agent.max_review_iterations

    logger.info(
        f"[Node_Review] Reviewing report (iteration {iteration}/{max_iterations})"
    )

    # 超过最大迭代次数，强制通过
    if iteration >= max_iterations:
        logger.warning(
            f"[Node_Review] Max iterations ({max_iterations}) reached, force passing"
        )
        return {
            "final_report": draft,
            "review_passed": True,
            "review_feedback": "已达最大迭代次数，自动通过。",
        }

    # LLM 审核
    llm_service = LLMService()
    review_result = await llm_service.review_report(draft)

    passed = review_result.get("passed", False)
    feedback = review_result.get("feedback", "")

    logger.info(f"[Node_Review] Review {'PASSED' if passed else 'FAILED'}")

    return {
        "final_report": draft if passed else state.get("final_report", ""),
        "review_passed": passed,
        "review_feedback": feedback,
    }
