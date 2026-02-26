"""
专利数据仓库 (Patent Repository)
数据访问层 — CRUD + 按关键词/申请人查询
"""
from __future__ import annotations

import uuid
from typing import Sequence

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.patent import Patent


class PatentRepository:
    """专利数据仓库"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, patent: Patent) -> Patent:
        """创建专利记录"""
        self.session.add(patent)
        await self.session.commit()
        await self.session.refresh(patent)
        return patent

    async def bulk_create(self, patents: list[Patent]) -> list[Patent]:
        """批量创建专利记录"""
        self.session.add_all(patents)
        await self.session.commit()
        return patents

    async def get_by_id(self, patent_id: uuid.UUID) -> Patent | None:
        """根据 ID 获取专利"""
        return await self.session.get(Patent, patent_id)

    async def get_by_query(self, search_query: str) -> Sequence[Patent]:
        """根据搜索关键词获取专利列表"""
        stmt = (
            select(Patent)
            .where(Patent.search_query == search_query)
            .order_by(Patent.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_assignee(self, assignee: str) -> Sequence[Patent]:
        """根据申请人查询"""
        stmt = (
            select(Patent)
            .where(Patent.assignee.ilike(f"%{assignee}%"))
            .order_by(Patent.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def search(
        self,
        query: str | None = None,
        assignee: str | None = None,
        category: str | None = None,
        limit: int = 50,
    ) -> Sequence[Patent]:
        """多条件搜索"""
        stmt = select(Patent)
        if query:
            stmt = stmt.where(Patent.search_query == query)
        if assignee:
            stmt = stmt.where(Patent.assignee.ilike(f"%{assignee}%"))
        if category:
            stmt = stmt.where(Patent.category == category)
        stmt = stmt.order_by(Patent.created_at.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def delete_by_query(self, search_query: str) -> int:
        """删除某次查询的所有专利记录"""
        stmt = delete(Patent).where(Patent.search_query == search_query)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount
