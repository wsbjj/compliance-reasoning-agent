"""
FastAPI 路由 — 趋势数据端点
供前端「热势仪表盘」子菜单读取数据库中的真实趋势数据
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.repositories.trend_repo import TrendRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/trends", tags=["trends"])


class TrendDataPoint(BaseModel):
    """单条趋势时序数据"""
    keyword: str
    date: str
    value: float | None = None
    source: str
    search_query: str


class TrendSummaryItem(BaseModel):
    """趋势摘要（含 CAGR）"""
    keyword: str
    search_query: str
    cagr: float | None = None
    cmgr: float | None = None
    beginning_value: float | None = None
    ending_value: float | None = None
    source: str
    timeframe_months: int | None = None
    created_at: str


@router.get("/data", response_model=list[TrendDataPoint])
async def get_trend_data(
    search_query: str | None = None,
    keyword: str | None = None,
    session: AsyncSession = Depends(get_db_session),
):
    """
    获取趋势时序数据（用于折线图）
    支持按查询词、关键词筛选
    """
    repo = TrendRepository(session)

    if search_query and keyword:
        records = await repo.get_data_by_keyword(keyword, search_query)
    elif search_query:
        records = await repo.get_data_by_query(search_query)
    else:
        # 未指定则返回所有（限制 500 条）
        from sqlalchemy import select
        from app.models.trend import TrendData
        stmt = select(TrendData).order_by(TrendData.date.asc()).limit(500)
        result = await session.execute(stmt)
        records = result.scalars().all()

    return [
        TrendDataPoint(
            keyword=r.keyword,
            date=r.date,
            value=r.value,
            source=r.source or "pytrends",
            search_query=r.search_query,
        )
        for r in records
    ]


@router.get("/summaries", response_model=list[TrendSummaryItem])
async def get_trend_summaries(
    search_query: str | None = None,
    limit: int = 20,
    session: AsyncSession = Depends(get_db_session),
):
    """
    获取趋势摘要（CAGR 榜单），按 CAGR 降序排列
    用于「高潜力增长词汇榜单」
    """
    from sqlalchemy import select
    from app.models.trend import TrendSummary

    stmt = select(TrendSummary)
    if search_query:
        stmt = stmt.where(TrendSummary.search_query == search_query)
    stmt = stmt.order_by(TrendSummary.cagr.desc().nullslast()).limit(limit)
    result = await session.execute(stmt)
    summaries = result.scalars().all()

    return [
        TrendSummaryItem(
            keyword=s.keyword,
            search_query=s.search_query,
            cagr=s.cagr,
            cmgr=s.cmgr,
            beginning_value=s.beginning_value,
            ending_value=s.ending_value,
            source=s.source or "pytrends",
            timeframe_months=s.timeframe_months,
            created_at=s.created_at.isoformat() if s.created_at else "",
        )
        for s in summaries
    ]


@router.get("/queries", response_model=list[str])
async def get_distinct_queries(
    session: AsyncSession = Depends(get_db_session),
):
    """获取所有已分析过的查询词（去重），供下拉框使用"""
    from sqlalchemy import select
    from app.models.trend import TrendSummary

    result = await session.execute(
        select(TrendSummary.search_query).distinct().limit(30)
    )
    return [r[0] for r in result.fetchall() if r[0]]
