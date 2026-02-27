"""
Node_Fetch_Trends — 趋势数据获取节点 (Tools)

通过 MCP 适配器调用趋势工具，拉取搜索指数并计算 CAGR。
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
    """
    search_keywords = state.get("search_keywords", [state.get("query", "")])

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

    return {
        "trends": trends,
        "trend_summaries": summaries,
        "trend_analysis": trend_analysis,
    }
