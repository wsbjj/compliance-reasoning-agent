"""
Node_Fetch_Trends — 趋势数据获取节点 (Tools)

通过 MCP 适配器调用趋势工具，拉取搜索指数并计算 CAGR。
完成后将趋势数据持久化到 PostgreSQL trend_data / trend_summaries 表。
"""
from __future__ import annotations

import logging

from app.agent.state import AgentState
from app.services.trend_service import TrendService

logger = logging.getLogger(__name__)


async def trend_node(state: AgentState) -> AgentState:
    """
    Tools: 趋势数据获取
    - 拉取 Google Trends / Rainforest / Keepa 数据
    - 计算 CAGR / CMGR
    - 持久化到数据库
    """
    query = state.get("query", "")
    search_keywords = state.get("search_keywords", [query])

    logger.info(f"[Node_Fetch_Trends] Fetching trends for: {search_keywords}")

    trend_service = TrendService()

    # 拉取趋势数据
    result = await trend_service.fetch_trends(search_keywords)

    trends = result.get("data", [])
    summaries = result.get("summaries", [])

    # 格式化趋势分析文本
    trend_text_parts = ["## 趋势数据摘要\n"]

    if summaries:
        trend_text_parts.append("| 关键词 | CAGR | 起始值 | 结束值 | 时间范围(月) |")
        trend_text_parts.append("|--------|------|--------|--------|-------------|")

        for s in summaries:
            cagr_str = (
                f"{s['cagr'] * 100:.2f}%"
                if s.get("cagr") is not None
                else "N/A"
            )
            trend_text_parts.append(
                f"| {s['keyword']} | {cagr_str} | {s.get('beginning_value', 'N/A')} | "
                f"{s.get('ending_value', 'N/A')} | {s.get('timeframe_months', 'N/A')} |"
            )

    trend_analysis = "\n".join(trend_text_parts)

    logger.info(
        f"[Node_Fetch_Trends] Got {len(trends)} data points, {len(summaries)} summaries"
    )

    # 持久化到数据库
    await _save_trends_to_db(trends, summaries, query)

    return {
        "trends": trends,
        "trend_summaries": summaries,
        "trend_analysis": trend_analysis,
    }


async def _save_trends_to_db(
    trends: list[dict],
    summaries: list[dict],
    search_query: str,
) -> None:
    """将趋势原始数据和摘要批量写入数据库"""
    if not trends and not summaries:
        return

    try:
        from app.core.database import get_session_factory
        from app.repositories.trend_repo import TrendRepository
        from app.models.trend import TrendData, TrendSummary

        factory = get_session_factory()
        async with factory() as session:
            repo = TrendRepository(session)

            # 写入原始时序数据
            if trends:
                trend_records = [
                    TrendData(
                        keyword=t.get("keyword", search_query)[:200],
                        date=str(t.get("date", ""))[:30],
                        value=t.get("value"),
                        source=t.get("source", "pytrends")[:20],
                        search_query=search_query[:200],
                    )
                    for t in trends
                ]
                await repo.bulk_create_data(trend_records)
                logger.info(
                    f"[Node_Fetch_Trends → DB] Saved {len(trend_records)} trend data points"
                )

            # 写入 CAGR 摘要
            if summaries:
                summary_records = [
                    TrendSummary(
                        keyword=s.get("keyword", search_query)[:200],
                        search_query=search_query[:200],
                        cagr=s.get("cagr"),
                        cmgr=s.get("cmgr"),
                        beginning_value=s.get("beginning_value"),
                        ending_value=s.get("ending_value"),
                        source=s.get("source", "pytrends")[:20],
                        timeframe_months=s.get("timeframe_months"),
                    )
                    for s in summaries
                ]
                await repo.bulk_create_summaries(summary_records)
                logger.info(
                    f"[Node_Fetch_Trends → DB] Saved {len(summary_records)} trend summaries"
                )

    except Exception as e:
        # DB 写入失败不中断主流程
        logger.warning(f"[Node_Fetch_Trends → DB] Failed to save trends: {e}")
