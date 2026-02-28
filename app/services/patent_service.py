"""
专利查询服务 (Patent Service)
业务逻辑层 — 工厂模式选择 SerpApi 或 USPTO 数据源
"""

from __future__ import annotations

import logging
from typing import Any

from app.core.config import get_settings, get_yaml_config
from app.models.patent import Patent

logger = logging.getLogger(__name__)


class PatentService:
    """专利查询业务服务"""

    def __init__(self):
        self.settings = get_settings()
        self.yaml_config = get_yaml_config()
        self.provider = self.yaml_config.data_sources.patent_provider

    async def search_patents(
        self,
        query: str,
        max_results: int | None = None,
        countries: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """
        搜索专利 — 根据 config.yaml 中的 provider 路由到对应实现
        返回标准化的专利数据列表

        Args:
            query: 搜索关键词
            max_results: 最大结果数
            countries: 国家筛选列表，如 ["US", "CN"]；None 或空列表表示不限
        """
        if max_results is None:
            max_results = self.yaml_config.agent.patent_search_limit

        # 空列表视为不限
        effective_countries = countries if countries else None

        if self.provider == "serpapi":
            return await self._search_serpapi(
                query, max_results, countries=effective_countries
            )
        elif self.provider == "uspto":
            return await self._search_uspto(query, max_results)
        else:
            raise ValueError(f"Unsupported patent provider: {self.provider}")

    async def _search_serpapi(
        self,
        query: str,
        max_results: int,
        countries: list[str] | None = None,
        status: str | None = None,
        sort: str | None = None,
        dups: str | None = None,
        before: str | None = None,
        after: str | None = None,
        patent_type: str | None = None,
        language: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        通过 SerpApi 搜索 Google Patents（google-search-results 包）

        分页：page 为 1-indexed（第一页=1），num 每页最多 100 条
        国家筛选：独立 country 参数，逗号分隔（如 "US,CN,WO"）
        排序：sort=new（最新）/ old（最旧）
        去重分组：dups 不传=Family同族去重；dups=language=显示全部公开文本
        其他过滤：status / before / after / type / language
        """
        api_key = self.settings.serpapi_api_key
        if not api_key:
            logger.warning("SerpApi API key not configured, returning mock data")
            return self._mock_patents(query)

        try:
            from serpapi import GoogleSearch  # google-search-results 包

            # 每页最多 100 条，max_results <= 100 时只需 1 次请求
            num_per_page = min(max_results, 100)
            results: list[dict[str, Any]] = []
            # ⚠️ SerpApi Google Patents 的 page 参数是 1-indexed，page=1 为第一页
            page_num = 1

            while len(results) < max_results:
                params: dict[str, Any] = {
                    "engine": "google_patents",
                    "q": query,
                    "api_key": api_key,
                    "num": num_per_page,  # 每页条数（10-100）
                    "page": page_num,  # 1-indexed 页码（文档默认值为 1）
                }

                # 国家筛选：专用 country 参数，逗号分隔
                if countries:
                    params["country"] = ",".join(countries)

                # 排序：new=最新 / old=最旧（注意：不是 Newest/Oldest）
                if sort:
                    params["sort"] = sort

                # 去重分组：不传=Family同族去重；"language"=显示全部公开文本
                if dups:
                    params["dups"] = dups

                # 日期范围
                if before:
                    params["before"] = before  # e.g. "publication:20240101"
                if after:
                    params["after"] = after  # e.g. "filing:20200101"

                # 法律状态 / 专利类型 / 语言
                if status:
                    params["status"] = status  # GRANT / APPLICATION
                if patent_type:
                    params["type"] = patent_type  # PATENT / DESIGN
                if language:
                    params["language"] = language  # ENGLISH / CHINESE / ...

                search = GoogleSearch(params)
                data = search.get_dict()
                organic_results = data.get("organic_results", [])

                if not organic_results:
                    break  # 无更多结果

                for item in organic_results:
                    if len(results) >= max_results:
                        break

                    figures = []
                    for fig in item.get("figures", []):
                        if isinstance(fig, dict) and fig.get("thumbnail"):
                            figures.append(fig["thumbnail"])
                        elif isinstance(fig, str):
                            figures.append(fig)

                    results.append(
                        {
                            "title": item.get("title", ""),
                            "assignee": item.get("assignee", ""),
                            "abstract": item.get("snippet", ""),
                            "patent_id": item.get("patent_id", ""),
                            "filing_date": item.get("filing_date", ""),
                            "priority_date": item.get("priority_date", ""),
                            "publication_date": item.get("publication_date", ""),
                            "inventor": item.get("inventor", ""),
                            "pdf_url": item.get("pdf", ""),
                            "thumbnail_url": item.get("thumbnail", ""),
                            "figures": figures,
                            "country_status": item.get("country_status", {}),
                            "publication_number": item.get("publication_number", ""),
                            "source": "serpapi",
                            "raw_data": item,
                        }
                    )

                # 本页不足 num_per_page → 已到最后一页
                if len(organic_results) < num_per_page:
                    break

                # SerpApi 无下一页标记 → 停止
                pagination = data.get("serpapi_pagination", {})
                if not pagination.get("next"):
                    break

                page_num += 1

            logger.info(
                f"SerpApi returned {len(results)} patents for q='{query}' "
                f"country={countries} status={status} sort={sort} dups={dups}"
            )
            return results

        except Exception as e:
            logger.error(f"SerpApi search failed: {e}")
            return self._mock_patents(query)

    async def _search_uspto(self, query: str, max_results: int) -> list[dict[str, Any]]:
        """
        通过 USPTO API 搜索美国专利
        """
        api_key = self.settings.uspto_api_key
        if not api_key:
            logger.warning("USPTO API key not configured, returning mock data")
            return self._mock_patents(query)

        try:
            import httpx

            async with httpx.AsyncClient(timeout=30.0) as client:
                url = "https://developer.uspto.gov/ibd-api/v1/application/publications"
                params = {
                    "searchText": query,
                    "rows": str(max_results),
                    "start": "0",
                }

                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()

                results = []
                for item in data.get("results", [])[:max_results]:
                    results.append(
                        {
                            "title": item.get("inventionTitle", ""),
                            "assignee": ", ".join(item.get("applicants", []))
                            if isinstance(item.get("applicants"), list)
                            else str(item.get("applicants", "")),
                            "abstract": item.get("abstractText", [None])[0]
                            if isinstance(item.get("abstractText"), list)
                            else item.get("abstractText", ""),
                            "patent_id": item.get("publicationDocumentIdentifier", ""),
                            "filing_date": item.get("filingDate", ""),
                            "source": "uspto",
                            "raw_data": item,
                        }
                    )

                logger.info(f"USPTO returned {len(results)} patents for '{query}'")
                return results

        except Exception as e:
            logger.error(f"USPTO search failed: {e}")
            return self._mock_patents(query)

    @staticmethod
    def _mock_patents(query: str) -> list[dict[str, Any]]:
        """降级模式 — 返回模拟数据供开发测试"""
        return [
            {
                "title": f"Smart {query} Patent #{i + 1}",
                "assignee": f"Company {chr(65 + i)}",
                "abstract": f"A novel approach to {query} technology involving advanced sensing and AI.",
                "patent_id": f"US2024{i:04d}",
                "filing_date": f"2024-0{(i % 9) + 1}-15",
                "source": "mock",
                "raw_data": {},
            }
            for i in range(10)
        ]

    @staticmethod
    def patents_to_dicts(patents: list[Patent]) -> list[dict[str, Any]]:
        """将 ORM Patent 对象转为字典列表（供 DataFrame）"""
        return [
            {
                "title": p.title,
                "assignee": p.assignee,
                "abstract": p.abstract,
                "patent_id": p.patent_id,
                "filing_date": p.filing_date,
                "category": p.category,
                "tech_points": p.tech_points or [],
                "source": p.source,
            }
            for p in patents
        ]
