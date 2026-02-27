"""
FastAPI 路由 — 专利数据端点
供前端「专利矩阵」子菜单读取数据库中的真实专利数据
"""
from __future__ import annotations

import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.repositories.patent_repo import PatentRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/patents", tags=["patents"])


class PatentItem(BaseModel):
    """单条专利数据"""
    id: str
    title: str
    assignee: str | None = None
    abstract: str | None = None
    patent_id: str | None = None
    filing_date: str | None = None
    search_query: str
    source: str
    category: str | None = None
    tech_points: Any = None
    created_at: str


class PatentStatsResponse(BaseModel):
    """专利统计数据"""
    total: int
    assignees: list[str]
    queries: list[str]
    sources: list[str]


@router.get("/", response_model=list[PatentItem])
async def list_patents(
    query: str | None = None,
    assignee: str | None = None,
    limit: int = 100,
    session: AsyncSession = Depends(get_db_session),
):
    """
    获取专利列表（用于专利矩阵看板）
    支持按搜索关键词、申请人筛选
    """
    repo = PatentRepository(session)
    patents = await repo.search(query=query, assignee=assignee, limit=limit)

    return [
        PatentItem(
            id=str(p.id),
            title=p.title,
            assignee=p.assignee,
            abstract=p.abstract,
            patent_id=p.patent_id,
            filing_date=p.filing_date,
            search_query=p.search_query,
            source=p.source or "serpapi",
            category=p.category,
            tech_points=p.tech_points,
            created_at=p.created_at.isoformat() if p.created_at else "",
        )
        for p in patents
    ]


@router.get("/stats", response_model=PatentStatsResponse)
async def get_patent_stats(
    session: AsyncSession = Depends(get_db_session),
):
    """获取专利库统计数据（总数、申请人列表、查询词列表）"""
    from sqlalchemy import select, func as sqlfunc
    from app.models.patent import Patent

    # 总数
    total_res = await session.execute(
        select(sqlfunc.count()).select_from(Patent)
    )
    total = total_res.scalar() or 0

    # 申请人列表（去重，排除 None）
    assignee_res = await session.execute(
        select(Patent.assignee).where(Patent.assignee.is_not(None)).distinct().limit(50)
    )
    assignees = [r[0] for r in assignee_res.fetchall() if r[0]]

    # 查询词列表（去重）
    query_res = await session.execute(
        select(Patent.search_query).distinct().limit(30)
    )
    queries = [r[0] for r in query_res.fetchall() if r[0]]

    # 来源列表
    source_res = await session.execute(
        select(Patent.source).distinct()
    )
    sources = [r[0] for r in source_res.fetchall() if r[0]]

    return PatentStatsResponse(
        total=total,
        assignees=assignees,
        queries=queries,
        sources=sources,
    )
