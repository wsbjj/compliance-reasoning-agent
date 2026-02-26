"""
分析报告模型 (Report Model)
存储 AI 生成的窗口期预警简报
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AnalysisReport(Base):
    """分析报告表"""
    __tablename__ = "analysis_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # 查询关键词
    query: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    # 专利分析摘要
    patent_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 趋势分析摘要
    trend_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 完整的 Markdown 报告
    full_report: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 额外上下文 (用户提供的补充信息)
    extra_context: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Agent 执行元数据 (节点耗时, 迭代次数 等)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # 状态: pending | running | completed | failed
    status: Mapped[str] = mapped_column(String(20), default="pending")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
