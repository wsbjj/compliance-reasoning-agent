"""
趋势数据 MCP Server
标准化工具接口 — 通过 FastMCP 暴露趋势搜索和 CAGR 计算功能
"""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP

# 创建 MCP Server 实例
trend_mcp = FastMCP("trend-data-server")


@trend_mcp.tool()
async def fetch_google_trends(keywords: list[str], timeframe_months: int = 36) -> dict:
    """
    拉取 Google Trends 搜索指数

    使用 pytrends 按月拉取过去 N 个月的搜索指数数据。

    Args:
        keywords: 关键词列表，如 ["smart ring", "wearable device"]
        timeframe_months: 时间范围（月），默认 36 个月

    Returns:
        包含时序数据和增长率摘要的字典
    """
    from app.services.trend_service import TrendService

    service = TrendService()
    # 强制使用 pytrends
    original_provider = service.provider
    service.provider = "pytrends"

    result = await service.fetch_trends(keywords, timeframe_months)
    service.provider = original_provider

    return result


@trend_mcp.tool()
async def fetch_amazon_trends(keywords: list[str]) -> dict:
    """
    拉取亚马逊关键词搜索量

    通过 Rainforest API 或 Keepa API 获取亚马逊平台的搜索热度。

    Args:
        keywords: 关键词列表

    Returns:
        包含亚马逊搜索量数据的字典
    """
    from app.services.trend_service import TrendService

    service = TrendService()

    # 尝试 Rainforest 优先，Keepa 备选
    for provider in ["rainforest", "keepa"]:
        original_provider = service.provider
        service.provider = provider
        try:
            result = await service.fetch_trends(keywords)
            service.provider = original_provider
            return result
        except Exception:
            service.provider = original_provider
            continue

    return {"data": [], "summaries": [], "error": "No Amazon keyword API available"}


@trend_mcp.tool()
def calculate_cagr(beginning_value: float, ending_value: float, years: float) -> dict:
    """
    计算复合年均增长率 (CAGR)

    CAGR = (Ending Value / Beginning Value) ^ (1/n) - 1

    Args:
        beginning_value: 起始值
        ending_value: 结束值
        years: 年数 (n)

    Returns:
        包含 CAGR 值和百分比的字典
    """
    from app.services.trend_service import TrendService

    cagr = TrendService.calculate_cagr(beginning_value, ending_value, years)

    return {
        "cagr": cagr,
        "cagr_percent": f"{cagr * 100:.2f}%" if cagr is not None else "N/A",
        "beginning_value": beginning_value,
        "ending_value": ending_value,
        "years": years,
    }


if __name__ == "__main__":
    trend_mcp.run()
