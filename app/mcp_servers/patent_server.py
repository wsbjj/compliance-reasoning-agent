"""
专利搜索 MCP Server
标准化工具接口 — 通过 FastMCP 暴露专利搜索功能
"""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP

# 创建 MCP Server 实例
patent_mcp = FastMCP("patent-search-server")


@patent_mcp.tool()
async def search_patents(query: str, max_results: int = 50) -> dict:
    """
    搜索专利数据库

    根据产品关键词搜索相关专利，返回标准化的专利信息列表。
    数据源通过 config.yaml 配置（支持 SerpApi / USPTO）。

    Args:
        query: 产品核心关键词，如 "Smart Ring"
        max_results: 最大返回结果数，默认 50

    Returns:
        包含专利列表的字典，每篇专利包含 title, assignee, abstract, filing_date 等字段
    """
    from app.services.patent_service import PatentService

    service = PatentService()
    patents = await service.search_patents(query, max_results)

    return {
        "query": query,
        "count": len(patents),
        "patents": patents,
    }


@patent_mcp.tool()
async def analyze_patent_landscape(query: str, patents_data: list[dict]) -> dict:
    """
    分析专利格局

    对搜索到的专利数据进行 LLM 分析，提取核心技术点和竞品分类。

    Args:
        query: 原始查询关键词
        patents_data: 专利数据列表

    Returns:
        包含技术分析和分类的字典
    """
    from app.services.llm_service import LLMService

    llm_service = LLMService()
    result = await llm_service.analyze_patents(patents_data, query)

    return result


if __name__ == "__main__":
    patent_mcp.run()
