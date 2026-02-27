"""
趋势分析服务 (Trend Service)
业务逻辑层 — 支持 pytrends / Rainforest / Keepa 多数据源
含 CAGR / CMGR 计算逻辑
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import pandas as pd

from app.core.config import get_settings, get_yaml_config

logger = logging.getLogger(__name__)


class TrendService:
    """趋势分析业务服务"""

    def __init__(self):
        self.settings = get_settings()
        self.yaml_config = get_yaml_config()
        self.provider = self.yaml_config.data_sources.trend_provider

    async def fetch_trends(
        self, keywords: list[str], timeframe_months: int | None = None
    ) -> dict[str, Any]:
        """
        拉取趋势数据 — 根据 config.yaml 路由
        返回: {"data": [...], "summaries": [...]}
        """
        if timeframe_months is None:
            timeframe_months = self.yaml_config.agent.trend_timeframe_months

        if self.provider == "pytrends":
            return await self._fetch_pytrends(keywords, timeframe_months)
        elif self.provider == "rainforest":
            return await self._fetch_rainforest(keywords)
        elif self.provider == "keepa":
            return await self._fetch_keepa(keywords)
        else:
            raise ValueError(f"Unsupported trend provider: {self.provider}")

    async def _fetch_pytrends(
        self, keywords: list[str], timeframe_months: int
    ) -> dict[str, Any]:
        """
        通过 pytrends 拉取 Google Trends 数据
        按月拉取过去 N 个月的搜索指数
        """
        try:
            from pytrends.request import TrendReq

            pytrend = TrendReq(
                hl="en-US",
                tz=360,
                proxies=["http://127.0.0.1:7890"],   # 本地代理
                retries=3,
                backoff_factor=0.5,
                timeout=(10, 25),
            )

            # pytrends 格式: "today 36-m" 或 "2021-01-01 2024-01-01"
            timeframe = f"today {timeframe_months}-m"

            # pytrends 最多一次查 5 个关键词
            all_data = []
            batch_size = 5
            for i in range(0, len(keywords), batch_size):
                batch = keywords[i : i + batch_size]
                pytrend.build_payload(batch, timeframe=timeframe)
                df = pytrend.interest_over_time()

                if not df.empty and "isPartial" in df.columns:
                    df = df.drop(columns=["isPartial"])

                for kw in batch:
                    if kw in df.columns:
                        for date_idx, value in df[kw].items():
                            all_data.append(
                                {
                                    "keyword": kw,
                                    "date": str(date_idx.date()),
                                    "value": float(value),
                                    "source": "pytrends",
                                }
                            )

            # 计算增长率
            summaries = self._calculate_growth_rates(all_data)

            logger.info(
                f"pytrends returned {len(all_data)} data points for {len(keywords)} keywords"
            )
            return {"data": all_data, "summaries": summaries}

        except Exception as e:
            logger.error(f"pytrends fetch failed: {e}")
            return self._mock_trends(keywords, timeframe_months)

    async def _fetch_rainforest(self, keywords: list[str]) -> dict[str, Any]:
        """通过 Rainforest API 拉取亚马逊搜索量"""
        api_key = self.settings.rainforest_api_key
        if not api_key:
            logger.warning("Rainforest API key not configured, returning mock data")
            return self._mock_trends(keywords)

        try:
            import httpx

            all_data = []
            async with httpx.AsyncClient(timeout=30.0) as client:
                for kw in keywords:
                    resp = await client.get(
                        "https://api.rainforestapi.com/request",
                        params={
                            "api_key": api_key,
                            "type": "search",
                            "amazon_domain": "amazon.com",
                            "search_term": kw,
                        },
                    )
                    resp.raise_for_status()
                    data = resp.json()

                    search_results = data.get("search_results", [])
                    all_data.append(
                        {
                            "keyword": kw,
                            "date": datetime.now().strftime("%Y-%m-%d"),
                            "value": float(len(search_results)),
                            "source": "rainforest",
                        }
                    )

            return {"data": all_data, "summaries": []}

        except Exception as e:
            logger.error(f"Rainforest fetch failed: {e}")
            return self._mock_trends(keywords)

    async def _fetch_keepa(self, keywords: list[str]) -> dict[str, Any]:
        """通过 Keepa API 拉取亚马逊关键词数据"""
        api_key = self.settings.keepa_api_key
        if not api_key:
            logger.warning("Keepa API key not configured, returning mock data")
            return self._mock_trends(keywords)

        try:
            import httpx

            all_data = []
            async with httpx.AsyncClient(timeout=30.0) as client:
                for kw in keywords:
                    resp = await client.get(
                        "https://api.keepa.com/search",
                        params={
                            "key": api_key,
                            "domain": "1",  # amazon.com
                            "type": "keyword",
                            "term": kw,
                        },
                    )
                    resp.raise_for_status()
                    data = resp.json()

                    all_data.append(
                        {
                            "keyword": kw,
                            "date": datetime.now().strftime("%Y-%m-%d"),
                            "value": data.get("searchVolume", 0),
                            "source": "keepa",
                        }
                    )

            return {"data": all_data, "summaries": []}

        except Exception as e:
            logger.error(f"Keepa fetch failed: {e}")
            return self._mock_trends(keywords)

    @staticmethod
    def calculate_cagr(
        beginning_value: float, ending_value: float, periods: float
    ) -> float | None:
        """
        计算复合年均增长率 (CAGR)
        CAGR = (Ending Value / Beginning Value) ^ (1/n) - 1
        """
        if beginning_value <= 0 or ending_value <= 0 or periods <= 0:
            return None
        return (ending_value / beginning_value) ** (1.0 / periods) - 1.0

    @staticmethod
    def calculate_cmgr(
        beginning_value: float, ending_value: float, months: int
    ) -> float | None:
        """
        计算复合月均增长率 (CMGR)
        CMGR = (Ending Value / Beginning Value) ^ (1/months) - 1
        """
        if beginning_value <= 0 or ending_value <= 0 or months <= 0:
            return None
        return (ending_value / beginning_value) ** (1.0 / months) - 1.0

    def _calculate_growth_rates(self, all_data: list[dict]) -> list[dict]:
        """为每个关键词计算 CAGR 和 CMGR"""
        if not all_data:
            return []

        df = pd.DataFrame(all_data)
        summaries = []

        for kw in df["keyword"].unique():
            kw_data = df[df["keyword"] == kw].sort_values("date")
            if len(kw_data) < 2:
                continue

            beginning = kw_data.iloc[0]["value"]
            ending = kw_data.iloc[-1]["value"]
            months = len(kw_data)
            years = months / 12.0

            cagr = self.calculate_cagr(beginning, ending, years)
            cmgr = self.calculate_cmgr(beginning, ending, months)

            summaries.append(
                {
                    "keyword": kw,
                    "cagr": round(cagr, 4) if cagr is not None else None,
                    "cmgr": round(cmgr, 4) if cmgr is not None else None,
                    "beginning_value": float(beginning),
                    "ending_value": float(ending),
                    "timeframe_months": months,
                    "source": kw_data.iloc[0]["source"],
                }
            )

        # 按 CAGR 降序排列
        summaries.sort(key=lambda x: x.get("cagr") or -999, reverse=True)
        return summaries

    @staticmethod
    def _mock_trends(
        keywords: list[str], timeframe_months: int = 36
    ) -> dict[str, Any]:
        """降级模式 — 返回模拟趋势数据"""
        import random

        all_data = []
        for kw in keywords:
            base = random.randint(10, 50)
            for m in range(timeframe_months):
                year = 2022 + m // 12
                month = (m % 12) + 1
                value = base + m * random.uniform(0.5, 2.0) + random.gauss(0, 5)
                all_data.append(
                    {
                        "keyword": kw,
                        "date": f"{year}-{month:02d}-01",
                        "value": max(0, round(value, 1)),
                        "source": "mock",
                    }
                )

        # Calculate summaries from mock data
        summaries = []
        df = pd.DataFrame(all_data)
        for kw in df["keyword"].unique():
            kw_data = df[df["keyword"] == kw].sort_values("date")
            beg = kw_data.iloc[0]["value"]
            end = kw_data.iloc[-1]["value"]
            months = len(kw_data)
            years = months / 12.0
            cagr = (end / beg) ** (1 / years) - 1 if beg > 0 and end > 0 else None
            summaries.append(
                {
                    "keyword": kw,
                    "cagr": round(cagr, 4) if cagr else None,
                    "cmgr": None,
                    "beginning_value": beg,
                    "ending_value": end,
                    "timeframe_months": months,
                    "source": "mock",
                }
            )

        return {"data": all_data, "summaries": summaries}
