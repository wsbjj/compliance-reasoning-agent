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
    """单条专利数据（来自数据库）"""
    id: str
    title: str
    assignee: str | None = None
    abstract: str | None = None
    patent_id: str | None = None
    publication_number: str | None = None
    filing_date: str | None = None
    priority_date: str | None = None
    publication_date: str | None = None
    inventor: str | None = None
    pdf_url: str | None = None
    thumbnail_url: str | None = None
    figures: list[str] = []
    country_status: dict = {}
    search_query: str
    source: str
    category: str | None = None
    tech_points: Any = None
    created_at: str


class PatentSearchItem(BaseModel):
    """实时搜索结果（来自 SerpApi，写库后返回）"""
    patent_id: str | None = None
    publication_number: str | None = None
    title: str = ""
    assignee: str | None = None
    inventor: str | None = None
    abstract: str | None = None
    filing_date: str | None = None
    priority_date: str | None = None
    publication_date: str | None = None
    pdf_url: str | None = None
    thumbnail_url: str | None = None
    figures: list[str] = []
    country_status: dict = {}


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

    result = []
    for p in patents:
        # figures 字段：若为 JSONB list，直接用；否则尝试从 raw_data 取
        figs = p.figures or []
        if not figs and isinstance(p.raw_data, dict):
            raw_figs = p.raw_data.get("figures", [])
            figs = [f["thumbnail"] if isinstance(f, dict) else str(f) for f in raw_figs if f]

        result.append(PatentItem(
            id=str(p.id),
            title=p.title,
            assignee=p.assignee,
            abstract=p.abstract,
            patent_id=p.patent_id,
            publication_number=p.publication_number,
            filing_date=p.filing_date,
            priority_date=p.priority_date,
            publication_date=p.publication_date,
            inventor=p.inventor,
            pdf_url=p.pdf_url,
            thumbnail_url=p.thumbnail_url,
            figures=figs,
            country_status=p.country_status or {},
            search_query=p.search_query,
            source=p.source or "serpapi",
            category=p.category,
            tech_points=p.tech_points,
            created_at=p.created_at.isoformat() if p.created_at else "",
        ))

    return result


@router.get("/search", response_model=list[PatentSearchItem])
async def search_patents_live(
    q: str,
    countries: str | None = None,
    session: AsyncSession = Depends(get_db_session),
):
    """
    实时调用 SerpApi 进行专利搜索，同时将结果写入数据库。
    支持国家筛选：countries=US,CN,JP（逗号分隔）
    search_query 使用"关键词 [US,CN]"格式（方案B）
    """
    from app.services.patent_service import PatentService
    from app.models.patent import Patent

    country_list = [c.strip().upper() for c in countries.split(",") if c.strip()] if countries else []

    service = PatentService()
    # 调用服务层（使用旧版 from serpapi import GoogleSearch）
    raw_results = await service._search_serpapi(
        q, max_results=200, countries=country_list or None
    )

    # 构建 search_query 标签（方案B：关键词 + 国家后缀）
    if country_list:
        search_query_label = f"{q} [{','.join(country_list)}]"[:200]
    else:
        search_query_label = q[:200]

    # 写入数据库
    if raw_results:
        try:
            repo = PatentRepository(session)
            patent_records = [
                Patent(
                    title=r.get("title", "Unknown")[:500],
                    assignee=(r.get("assignee") or "")[:300] or None,
                    abstract=r.get("abstract"),
                    patent_id=(r.get("patent_id") or "")[:50] or None,
                    publication_number=(r.get("publication_number") or "")[:100] or None,
                    filing_date=(r.get("filing_date") or "")[:30] or None,
                    priority_date=(r.get("priority_date") or "")[:30] or None,
                    publication_date=(r.get("publication_date") or "")[:30] or None,
                    inventor=(r.get("inventor") or "")[:500] or None,
                    pdf_url=r.get("pdf_url") or None,
                    thumbnail_url=r.get("thumbnail_url") or None,
                    figures=r.get("figures") or [],
                    country_status=r.get("country_status") or {},
                    search_query=search_query_label,
                    source="serpapi",
                    raw_data=r,
                )
                for r in raw_results
            ]
            await repo.bulk_create(patent_records)
            logger.info(
                f"[/api/patents/search] Saved {len(patent_records)} patents "
                f"for query='{search_query_label}'"
            )
        except Exception as e:
            logger.warning(f"[/api/patents/search] DB save failed: {e}")

    return [
        PatentSearchItem(
            patent_id=r.get("patent_id"),
            publication_number=r.get("publication_number"),
            title=r.get("title", ""),
            assignee=r.get("assignee"),
            inventor=r.get("inventor"),
            abstract=r.get("abstract"),
            filing_date=r.get("filing_date"),
            priority_date=r.get("priority_date"),
            publication_date=r.get("publication_date"),
            pdf_url=r.get("pdf_url"),
            thumbnail_url=r.get("thumbnail_url"),
            figures=r.get("figures", []),
            country_status=r.get("country_status", {}),
        )
        for r in raw_results
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
