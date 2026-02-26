"""
分析报告仓库 (Report Repository)
数据访问层 — 报告 CRUD
"""
from __future__ import annotations

import uuid
from typing import Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.report import AnalysisReport


class ReportRepository:
    """分析报告仓库"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, report: AnalysisReport) -> AnalysisReport:
        """创建报告（初始状态为 pending）"""
        self.session.add(report)
        await self.session.commit()
        await self.session.refresh(report)
        return report

    async def get_by_id(self, report_id: uuid.UUID) -> AnalysisReport | None:
        """根据 ID 获取报告"""
        return await self.session.get(AnalysisReport, report_id)

    async def get_by_query(self, query: str) -> Sequence[AnalysisReport]:
        """根据查询词获取历史报告"""
        stmt = (
            select(AnalysisReport)
            .where(AnalysisReport.query == query)
            .order_by(AnalysisReport.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_recent(self, limit: int = 20) -> Sequence[AnalysisReport]:
        """获取最近的报告"""
        stmt = (
            select(AnalysisReport)
            .order_by(AnalysisReport.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_status(
        self, report_id: uuid.UUID, status: str, **kwargs
    ) -> None:
        """更新报告状态和内容"""
        values = {"status": status, **kwargs}
        stmt = (
            update(AnalysisReport)
            .where(AnalysisReport.id == report_id)
            .values(**values)
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def update_report(
        self,
        report_id: uuid.UUID,
        full_report: str,
        patent_summary: str | None = None,
        trend_summary: str | None = None,
        metadata_json: dict | None = None,
    ) -> None:
        """更新报告完整内容"""
        values: dict = {
            "full_report": full_report,
            "status": "completed",
        }
        if patent_summary is not None:
            values["patent_summary"] = patent_summary
        if trend_summary is not None:
            values["trend_summary"] = trend_summary
        if metadata_json is not None:
            values["metadata_json"] = metadata_json

        stmt = (
            update(AnalysisReport)
            .where(AnalysisReport.id == report_id)
            .values(**values)
        )
        await self.session.execute(stmt)
        await self.session.commit()
