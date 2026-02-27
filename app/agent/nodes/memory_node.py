"""
Node_Update_Memory — 记忆更新节点

在工作流结束前，将本次分析的上下文摘要存入 Mem0，
同时将最终报告持久化到 PostgreSQL analysis_reports 表。
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime

from app.agent.state import AgentState
from app.services.llm_service import LLMService
from app.services.memory_service import MemoryService

logger = logging.getLogger(__name__)


async def memory_node(state: AgentState) -> AgentState:
    """
    Memory Update: 对话摘要存储
    - 利用 LLM 压缩上下文
    - 写入 Mem0 长期记忆
    - 将最终报告持久化到数据库
    """
    query = state.get("query", "")
    final_report = state.get("final_report", state.get("draft_report", ""))
    user_id = state.get("user_id", "default")
    patent_count = len(state.get("patents", []))
    trend_count = len(state.get("trend_summaries", []))
    report_id_str = state.get("report_id", "")

    logger.info(f"[Node_Update_Memory] Updating memory for user '{user_id}'")

    # 1. 使用 LLM 生成摘要
    context_to_summarize = f"""
查询关键词: {query}
搜索到 {patent_count} 篇专利
分析了 {trend_count} 个趋势关键词
报告关键结论: {final_report[:500] if final_report else '无报告'}
"""

    llm_service = LLMService()
    summary = await llm_service.summarize_for_memory(context_to_summarize)

    # 2. 写入 Mem0
    memory_service = MemoryService()
    await memory_service.add_memory(
        content=summary,
        user_id=user_id,
        metadata={
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "patent_count": patent_count,
            "trend_count": trend_count,
            "type": "analysis_session",
        },
    )

    logger.info("[Node_Update_Memory] Memory updated successfully")

    # 3. 持久化最终报告到数据库
    await _save_report_to_db(
        report_id_str=report_id_str,
        query=query,
        full_report=final_report,
        patent_summary=state.get("patent_analysis"),
        trend_summary=state.get("trend_analysis"),
        extra_context=state.get("extra_context"),
        iteration_count=state.get("iteration_count", 0),
        patent_count=patent_count,
        trend_count=trend_count,
    )

    return state


async def _save_report_to_db(
    report_id_str: str,
    query: str,
    full_report: str,
    patent_summary: str | None,
    trend_summary: str | None,
    extra_context: str | None,
    iteration_count: int,
    patent_count: int,
    trend_count: int,
) -> None:
    """将最终报告更新到数据库（状态: completed）"""
    try:
        from app.core.database import get_session_factory
        from app.repositories.report_repo import ReportRepository

        factory = get_session_factory()
        async with factory() as session:
            repo = ReportRepository(session)

            if report_id_str:
                # 更新已有记录（由 API 层创建 pending 记录）
                try:
                    report_id = uuid.UUID(report_id_str)
                    await repo.update_report(
                        report_id=report_id,
                        full_report=full_report,
                        patent_summary=patent_summary,
                        trend_summary=trend_summary,
                        metadata_json={
                            "iteration_count": iteration_count,
                            "patent_count": patent_count,
                            "trend_count": trend_count,
                        },
                    )
                    logger.info(
                        f"[Node_Update_Memory → DB] Report {report_id_str} marked completed"
                    )
                except ValueError:
                    logger.warning(
                        f"[Node_Update_Memory → DB] Invalid report_id: {report_id_str}"
                    )
            else:
                logger.warning(
                    "[Node_Update_Memory → DB] No report_id in state, skipping DB update"
                )
    except Exception as e:
        logger.warning(f"[Node_Update_Memory → DB] Failed to save report: {e}")
