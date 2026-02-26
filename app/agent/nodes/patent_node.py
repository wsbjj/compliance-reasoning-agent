"""
Node_Fetch_Patents — 专利搜索节点 (Tools)

通过 MCP 适配器调用专利搜索工具，获取专利数据并进行 LLM 分析。
"""
from __future__ import annotations

import logging

from app.agent.state import AgentState
from app.services.patent_service import PatentService
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)


async def patent_node(state: AgentState) -> AgentState:
    """
    Tools: 专利数据获取
    - 搜索 Google Patents / USPTO
    - LLM 提取技术点和竞品分类
    """
    query = state.get("query", "")
    search_keywords = state.get("search_keywords", [query])

    logger.info(f"[Node_Fetch_Patents] Fetching patents for: {search_keywords}")

    patent_service = PatentService()
    llm_service = LLMService()

    # 1. 搜索专利
    all_patents = []
    for kw in search_keywords[:3]:  # 最多取前 3 个关键词避免过多请求
        patents = await patent_service.search_patents(kw)
        all_patents.extend(patents)

    # 去重（按 patent_id）
    seen_ids = set()
    unique_patents = []
    for p in all_patents:
        pid = p.get("patent_id", "")
        if pid and pid not in seen_ids:
            seen_ids.add(pid)
            unique_patents.append(p)
        elif not pid:
            unique_patents.append(p)

    logger.info(
        f"[Node_Fetch_Patents] Found {len(unique_patents)} unique patents"
    )

    # 2. LLM 分析专利格局
    analysis_result = await llm_service.analyze_patents(unique_patents, query)

    return {
        **state,
        "patents": unique_patents,
        "patent_analysis": analysis_result.get("tech_analysis", ""),
    }
