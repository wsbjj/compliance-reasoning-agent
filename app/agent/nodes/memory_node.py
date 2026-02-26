"""
Node_Update_Memory — 记忆更新节点

在工作流结束前，将本次分析的上下文摘要存入 Mem0。
"""
from __future__ import annotations

import logging
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
    """
    query = state.get("query", "")
    final_report = state.get("final_report", state.get("draft_report", ""))
    user_id = state.get("user_id", "default")
    patent_count = len(state.get("patents", []))
    trend_count = len(state.get("trend_summaries", []))

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

    return state
