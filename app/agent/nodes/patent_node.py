"""
Node_Fetch_Patents — 专利搜索节点 (Tools)

通过 MCP 适配器调用专利搜索工具，获取专利数据并进行 LLM 分析。
完成后将专利数据持久化到 PostgreSQL patents 表。
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
    - 持久化到数据库
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

    # 3. 持久化到数据库
    await _save_patents_to_db(unique_patents, query)

    return {
        "patents": unique_patents,
        "patent_analysis": analysis_result.get("tech_analysis", ""),
    }


async def _save_patents_to_db(patents: list[dict], search_query: str) -> None:
    """将专利数据批量写入数据库（完整字段）"""
    if not patents:
        return

    try:
        from app.core.database import get_session_factory
        from app.repositories.patent_repo import PatentRepository
        from app.models.patent import Patent

        factory = get_session_factory()
        async with factory() as session:
            repo = PatentRepository(session)
            patent_records = [
                Patent(
                    title=p.get("title", "Unknown")[:500],
                    assignee=(p.get("assignee") or "")[:300] or None,
                    abstract=p.get("abstract"),
                    patent_id=(p.get("patent_id") or "")[:50] or None,
                    publication_number=(p.get("publication_number") or "")[:100] or None,
                    filing_date=(p.get("filing_date") or "")[:30] or None,
                    priority_date=(p.get("priority_date") or "")[:30] or None,
                    publication_date=(p.get("publication_date") or "")[:30] or None,
                    inventor=(p.get("inventor") or "")[:500] or None,
                    pdf_url=p.get("pdf_url") or None,
                    thumbnail_url=p.get("thumbnail_url") or None,
                    figures=p.get("figures") or [],
                    country_status=p.get("country_status") or {},
                    search_query=search_query[:200],
                    source=p.get("source", "serpapi")[:20],
                    tech_points=p.get("tech_points"),
                    raw_data=p,
                )
                for p in patents
            ]
            await repo.bulk_create(patent_records)
            logger.info(
                f"[Node_Fetch_Patents → DB] Saved {len(patent_records)} patents "
                f"for query='{search_query}'"
            )
    except Exception as e:
        # DB 写入失败不中断主流程
        logger.warning(f"[Node_Fetch_Patents → DB] Failed to save patents: {e}")

