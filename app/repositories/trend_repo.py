"""
趋势数据仓库 (Trend Repository)
数据访问层 — 趋势数据和摘要 CRUD
"""
from __future__ import annotations

import uuid
from typing import Sequence

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.trend import TrendData, TrendSummary


class TrendRepository:
    """趋势数据仓库"""

    def __init__(self, session: AsyncSession):
        self.session = session

    # --- TrendData ---
    async def bulk_create_data(self, records: list[TrendData]) -> list[TrendData]:
        """批量插入趋势时序数据"""
        self.session.add_all(records)
        await self.session.commit()
        return records

    async def get_data_by_keyword(
        self, keyword: str, search_query: str
    ) -> Sequence[TrendData]:
        """按关键词和查询获取趋势数据"""
        stmt = (
            select(TrendData)
            .where(
                TrendData.keyword == keyword,
                TrendData.search_query == search_query,
            )
            .order_by(TrendData.date.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_data_by_query(self, search_query: str) -> Sequence[TrendData]:
        """按查询获取所有趋势数据"""
        stmt = (
            select(TrendData)
            .where(TrendData.search_query == search_query)
            .order_by(TrendData.keyword, TrendData.date.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    # --- TrendSummary ---
    async def create_summary(self, summary: TrendSummary) -> TrendSummary:
        """创建趋势摘要"""
        self.session.add(summary)
        await self.session.commit()
        await self.session.refresh(summary)
        return summary

    async def bulk_create_summaries(
        self, summaries: list[TrendSummary]
    ) -> list[TrendSummary]:
        """批量创建趋势摘要"""
        self.session.add_all(summaries)
        await self.session.commit()
        return summaries

    async def get_summaries_by_query(
        self, search_query: str
    ) -> Sequence[TrendSummary]:
        """按查询获取趋势摘要"""
        stmt = (
            select(TrendSummary)
            .where(TrendSummary.search_query == search_query)
            .order_by(TrendSummary.cagr.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def delete_by_query(self, search_query: str) -> int:
        """删除某次查询的所有趋势数据"""
        stmt1 = delete(TrendData).where(TrendData.search_query == search_query)
        stmt2 = delete(TrendSummary).where(TrendSummary.search_query == search_query)
        r1 = await self.session.execute(stmt1)
        r2 = await self.session.execute(stmt2)
        await self.session.commit()
        return r1.rowcount + r2.rowcount
